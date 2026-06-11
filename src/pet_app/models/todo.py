from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TodoItem:
    """Todo item model."""
    title: str
    description: Optional[str] = None
    ddl: Optional[str] = None  # ISO format: 2026-05-22 23:30:00
    is_done: int = 0
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    reminded_one_day: int = 0
    reminded_half_hour: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "ddl": self.ddl,
            "is_done": self.is_done,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "reminded_one_day": self.reminded_one_day,
            "reminded_half_hour": self.reminded_half_hour
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TodoItem":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description"),
            ddl=data.get("ddl"),
            is_done=data.get("is_done", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            reminded_one_day=data.get("reminded_one_day", 0),
            reminded_half_hour=data.get("reminded_half_hour", 0)
        )