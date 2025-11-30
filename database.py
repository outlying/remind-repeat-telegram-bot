import sqlite3
import threading
from typing import List, Dict, Optional
from datetime import datetime

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        """Create tables if they don't exist"""
        with self._lock:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    schedule_type TEXT NOT NULL,
                    schedule_data TEXT NOT NULL,
                    schedule_description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_reminders_user_id
                ON reminders(user_id)
            ''')
            self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_reminders_created_at
                ON reminders(created_at)
            ''')
            self.conn.commit()

    def add_reminder(self, user_id: int, chat_id: int, message: str,
                    schedule_type: str, schedule_data: str,
                    schedule_description: str) -> int:
        """Add a new reminder"""
        with self._lock:
            cursor = self.conn.execute('''
                INSERT INTO reminders
                (user_id, chat_id, message, schedule_type, schedule_data, schedule_description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, chat_id, message, schedule_type, schedule_data, schedule_description))
            self.conn.commit()
            return cursor.lastrowid

    def get_user_reminders(self, user_id: int) -> List[Dict]:
        """Get all reminders for a user"""
        with self._lock:
            cursor = self.conn.execute('''
                SELECT * FROM reminders
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_reminder(self, reminder_id: int) -> Optional[Dict]:
        """Get a single reminder"""
        with self._lock:
            cursor = self.conn.execute('''
                SELECT * FROM reminders
                WHERE id = ?
            ''', (reminder_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_reminders(self) -> List[Dict]:
        """Get all reminders (for loading at startup)"""
        with self._lock:
            cursor = self.conn.execute('SELECT * FROM reminders')
            return [dict(row) for row in cursor.fetchall()]

    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder"""
        with self._lock:
            cursor = self.conn.execute('''
                DELETE FROM reminders
                WHERE id = ?
            ''', (reminder_id,))
            self.conn.commit()
            return cursor.rowcount > 0
