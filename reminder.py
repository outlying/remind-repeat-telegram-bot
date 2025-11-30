from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class Reminder:
    id: int
    user_id: int
    chat_id: int
    message: str
    schedule_type: str
    schedule_data: Dict[str, Any]
    schedule_description: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'message': self.message,
            'schedule_type': self.schedule_type,
            'schedule_data': self.schedule_data,
            'schedule_description': self.schedule_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reminder':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            chat_id=data['chat_id'],
            message=data['message'],
            schedule_type=data['schedule_type'],
            schedule_data=data['schedule_data'],
            schedule_description=data['schedule_description'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )
