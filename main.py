import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import json

from reminder_parser import ReminderParser
from database import Database
from reminder import Reminder

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file (if present)
load_dotenv()

# Bot token (from .env or environment)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment or .env. Set it in the environment or in a .env file.")
    exit(1)

# Initialization
db = Database('reminders.db')
parser = ReminderParser()
scheduler = AsyncIOScheduler()

# Temporary storage for pending confirmations
pending_reminders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "Hello! I'm a reminder bot. Available commands:\n\n"
        "/add <description> - Add a new reminder\n"
        "/list - Show all your reminders\n"
        "/delete <id> - Delete a reminder\n\n"
        "Example: /add Daily at 07:05 remind me to take my medication"
    )

async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding a new reminder"""
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Usage: /add <reminder description>")
        return

    text = ' '.join(context.args)

    # Parse text
    parsed = parser.parse(text)

    if not parsed:
        await update.message.reply_text(
            "I couldn't understand your reminder. Try formats:\n"
            "- Daily at 07:05 remind me to...\n"
            "- Every Monday at 10:00...\n"
            "- On the 3rd day of the month at 11:00..."
        )
        return

    # Store temporarily for confirmation
    reminder_id = f"{user_id}_{datetime.now().timestamp()}"
    pending_reminders[reminder_id] = {
        'user_id': user_id,
        'chat_id': update.effective_chat.id,
        'parsed': parsed,
        'original_text': text
    }

    # Show interpretation and ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, add", callback_data=f"confirm_{reminder_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{reminder_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"I understood it as:\n\n"
        f"📅 When: {parsed['schedule_description']}\n"
        f"💬 Message: {parsed['message']}\n\n"
        f"Is this correct?",
        reply_markup=reply_markup
    )

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all reminders for the user"""
    user_id = update.effective_user.id
    reminders = db.get_user_reminders(user_id)

    if not reminders:
        await update.message.reply_text("You don't have any reminders yet.")
        return

    message = "Your reminders:\n\n"
    for reminder in reminders:
        message += f"🔔 ID: {reminder['id']}\n"
        message += f"📅 When: {reminder['schedule_description']}\n"
        message += f"💬 Message: {reminder['message']}\n"
        message += f"📍 Channel: Private chat\n\n"

    await update.message.reply_text(message)

async def delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a reminder"""
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Usage: /delete <id>")
        return

    try:
        reminder_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID must be a number.")
        return

    # Check ownership
    reminder = db.get_reminder(reminder_id)
    if not reminder or reminder['user_id'] != user_id:
        await update.message.reply_text("No reminder found with that ID.")
        return

    # Remove from scheduler
    job_id = f"reminder_{reminder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Remove from database
    db.delete_reminder(reminder_id)

    await update.message.reply_text("Reminder has been deleted.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline buttons"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("confirm_"):
        reminder_id = data.replace("confirm_", "")

        if reminder_id not in pending_reminders:
            await query.edit_message_text("This reminder has already been processed.")
            return

        # Retrieve pending data
        pending = pending_reminders[reminder_id]

        # Save to database
        db_id = db.add_reminder(
            user_id=pending['user_id'],
            chat_id=pending['chat_id'],
            message=pending['parsed']['message'],
            schedule_type=pending['parsed']['schedule_type'],
            schedule_data=json.dumps(pending['parsed']['schedule_data']),
            schedule_description=pending['parsed']['schedule_description']
        )

        # Schedule the reminder
        schedule_reminder(db_id, pending['chat_id'], pending['parsed'])

        # Remove from pending
        del pending_reminders[reminder_id]

        await query.edit_message_text("✅ Reminder has been added!")

    elif data.startswith("cancel_"):
        reminder_id = data.replace("cancel_", "")

        if reminder_id in pending_reminders:
            del pending_reminders[reminder_id]

        await query.edit_message_text("❌ Adding reminder cancelled.")

def schedule_reminder(reminder_id: int, chat_id: int, parsed_data: dict):
    """Add a reminder to the scheduler"""
    job_id = f"reminder_{reminder_id}"

    schedule_type = parsed_data['schedule_type']
    schedule_data = parsed_data['schedule_data']
    message = parsed_data['message']

    if schedule_type == 'daily':
        scheduler.add_job(
            send_reminder,
            'cron',
            hour=schedule_data['hour'],
            minute=schedule_data['minute'],
            args=[chat_id, message],
            id=job_id,
            replace_existing=True
        )
    elif schedule_type == 'weekly':
        scheduler.add_job(
            send_reminder,
            'cron',
            day_of_week=schedule_data['day_of_week'],
            hour=schedule_data['hour'],
            minute=schedule_data['minute'],
            args=[chat_id, message],
            id=job_id,
            replace_existing=True
        )
    elif schedule_type == 'monthly':
        scheduler.add_job(
            send_reminder,
            'cron',
            day=schedule_data['day'],
            hour=schedule_data['hour'],
            minute=schedule_data['minute'],
            args=[chat_id, message],
            id=job_id,
            replace_existing=True
        )

async def send_reminder(chat_id: int, message: str):
    """Send a reminder message"""
    try:
        await application.bot.send_message(
            chat_id=chat_id,
            text=f"🔔 Reminder:\n\n{message}"
        )
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")

def load_all_reminders():
    """Load all reminders from the database into the scheduler"""
    reminders = db.get_all_reminders()
    for reminder in reminders:
        parsed_data = {
            'message': reminder['message'],
            'schedule_type': reminder['schedule_type'],
            'schedule_data': json.loads(reminder['schedule_data']),
            'schedule_description': reminder['schedule_description']
        }
        schedule_reminder(reminder['id'], reminder['chat_id'], parsed_data)

def main():
    """Main entry point"""
    global application

    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_reminder))
    application.add_handler(CommandHandler("list", list_reminders))
    application.add_handler(CommandHandler("delete", delete_reminder))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start scheduler
    scheduler.start()

    # Load existing reminders
    load_all_reminders()

    # Run bot
    application.run_polling()

if __name__ == '__main__':
    main()
