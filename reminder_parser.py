import re
from datetime import datetime
from typing import Optional, Dict, Any

class ReminderParser:
    def __init__(self):
        # Days of week mapping (English variants)
        self.days_of_week = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }

        # Regex patterns (English)
        self.time_pattern = r'(?:at\s*)?(\d{1,2}):(\d{2})'
        self.daily_pattern = r'\bdaily\b|\bevery day\b|\beach day\b'
        # weekly_pattern will match e.g. "every monday" or "on monday"
        self.weekly_pattern = r'(?:every|each|on|every)\s*(' + '|'.join(self.days_of_week.keys()) + r')'
        # monthly: match "3rd day of the month", "on the 3rd of the month", "3 day of month", or "on day 3 of month"
        self.monthly_pattern = r'(\d{1,2})(?:st|nd|rd|th)?(?:\s*(?:day\s*(?:of\s*)?the\s*month|of\s*the\s*month|of\s*month|day\s*of\s*month|month))?'

    def parse(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse text and return a dict with reminder data"""
        text = text.lower()

        # Find time
        time_match = re.search(self.time_pattern, text)
        if not time_match:
            return None

        hour = int(time_match.group(1))
        minute = int(time_match.group(2))

        if hour > 23 or minute > 59:
            return None

        # Extract message
        message = self._extract_message(text)
        if not message:
            return None

        # Determine schedule type
        if re.search(self.daily_pattern, text):
            return {
                'schedule_type': 'daily',
                'schedule_data': {
                    'hour': hour,
                    'minute': minute
                },
                'schedule_description': f'Daily at {hour:02d}:{minute:02d}',
                'message': message
            }

        weekly_match = re.search(self.weekly_pattern, text)
        if weekly_match:
            day_name = weekly_match.group(1)
            day_of_week = self.days_of_week.get(day_name)

            if day_of_week is not None:
                # Use English description (capitalize day name)
                return {
                    'schedule_type': 'weekly',
                    'schedule_data': {
                        'day_of_week': day_of_week,
                        'hour': hour,
                        'minute': minute
                    },
                    'schedule_description': f'Every {day_name.capitalize()} at {hour:02d}:{minute:02d}',
                    'message': message
                }

        monthly_match = re.search(self.monthly_pattern, text)
        if monthly_match:
            day = int(monthly_match.group(1))

            if 1 <= day <= 31:
                return {
                    'schedule_type': 'monthly',
                    'schedule_data': {
                        'day': day,
                        'hour': hour,
                        'minute': minute
                    },
                    'schedule_description': f'On day {day} of the month at {hour:02d}:{minute:02d}',
                    'message': message
                }

        return None

    def _extract_message(self, text: str) -> Optional[str]:
        """Extract reminder message from text"""
        # Look for phrases indicating the start of the message (English)
        message_indicators = [
            'remind me to', 'remind to', 'reminder to',
            'write to', 'notify me to', 'notify to',
            'remind that', 'write that', 'notify that'
        ]

        for indicator in message_indicators:
            if indicator in text:
                pos = text.find(indicator)
                message = text[pos + len(indicator):].strip()

                if message:
                    message = message.rstrip('.')
                    return message[0].upper() + message[1:] if message else None

        # If no indicator found, try extracting after the time
        time_match = re.search(self.time_pattern, text)
        if time_match:
            pos = time_match.end()
            message = text[pos:].strip()

            # Remove common leading words
            for word in ['remind', 'write', 'notify']:
                if message.startswith(word):
                    message = message[len(word):].strip()

            for word in ['me', 'to']:
                if message.startswith(word + ' '):
                    message = message[len(word):].strip()

            if message.startswith('to '):
                message = message[3:].strip()

            if message:
                return message[0].upper() + message[1:] if message else None

        return None
