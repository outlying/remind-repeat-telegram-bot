# Telegram Reminder Bot

A Telegram bot for creating recurring reminders.

## Features

- Create daily, weekly and monthly reminders
- Simple natural-language parsing (no AI/LLM)
- Confirmation of interpretation before adding
- User-specific reminder list
- Deleting reminders
- Data isolation per user

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` and add your bot token
4. Run the bot:
   ```bash
   python main.py
   ```

## Usage

### Commands

- `/start` - Show help
- `/add <description>` - Add a new reminder
- `/list` - Show all your reminders
- `/delete <id>` - Delete a reminder

### Examples

- `/add Daily at 07:05 remind me to take my medication`
- `/add Every Monday at 10:00 remind me about the team meeting`
- `/add On the 3rd day of the month at 11:00 remind me to pay bills`