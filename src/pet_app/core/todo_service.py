from datetime import datetime
from typing import List, Optional
from pet_app.core.storage import StorageManager
from pet_app.models.todo import TodoItem
from pet_app.utils.logger import logger


class TodoService:
    """Business logic for todo items."""

    def __init__(self, storage_manager: StorageManager):
        """Initialize todo service."""
        self.storage = storage_manager
        logger.info("TodoService initialized")

    def create_todo(self, title: str, description: Optional[str] = None, ddl: Optional[str] = None) -> TodoItem:
        """Create a new todo item."""
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        
        query = """
            INSERT INTO todos (title, description, ddl, is_done, created_at, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
        """
        
        self.storage.execute_update(query, (title, description, ddl, now, now))
        todo_id = self.storage.get_last_insert_id()
        
        logger.info(f"Todo created: {title} (ID: {todo_id})")
        
        return TodoItem(
            id=todo_id,
            title=title,
            description=description,
            ddl=ddl,
            is_done=0,
            created_at=now,
            updated_at=now
        )

    def get_all_todos(self) -> List[TodoItem]:
        """Get all todo items."""
        query = "SELECT * FROM todos ORDER BY is_done ASC, created_at DESC"
        rows = self.storage.execute_query(query)
        return [TodoItem.from_dict(row) for row in rows]

    def get_todo(self, todo_id: int) -> Optional[TodoItem]:
        """Get a specific todo item."""
        query = "SELECT * FROM todos WHERE id = ?"
        rows = self.storage.execute_query(query, (todo_id,))
        return TodoItem.from_dict(rows[0]) if rows else None

    def update_todo(self, todo_id: int, title: str = None, description: str = None, ddl: str = None) -> bool:
        """Update a todo item."""
        todo = self.get_todo(todo_id)
        if not todo:
            logger.warning(f"Todo not found: {todo_id}")
            return False

        now = datetime.now().isoformat(sep=" ", timespec="seconds")

        # Update only provided fields
        update_fields = []
        params = []

        if title is not None:
            update_fields.append("title = ?")
            params.append(title)

        if description is not None:
            update_fields.append("description = ?")
            params.append(description)

        if ddl is not None:
            update_fields.append("ddl = ?")
            params.append(ddl)
            # Reset reminder flags when DDL is changed
            update_fields.append("reminded_one_day = ?")
            params.append(0)
            update_fields.append("reminded_half_hour = ?")
            params.append(0)

        update_fields.append("updated_at = ?")
        params.append(now)
        params.append(todo_id)

        query = f"UPDATE todos SET {', '.join(update_fields)} WHERE id = ?"
        self.storage.execute_update(query, tuple(params))

        logger.info(f"Todo updated: {todo_id}")
        return True

    def toggle_done(self, todo_id: int) -> bool:
        """Toggle todo completion status."""
        todo = self.get_todo(todo_id)
        if not todo:
            logger.warning(f"Todo not found: {todo_id}")
            return False
        
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        new_status = 1 - todo.is_done
        
        query = "UPDATE todos SET is_done = ?, updated_at = ? WHERE id = ?"
        self.storage.execute_update(query, (new_status, now, todo_id))
        
        logger.info(f"Todo {todo_id} toggled: is_done={new_status}")
        return True

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item."""
        todo = self.get_todo(todo_id)
        if not todo:
            logger.warning(f"Todo not found: {todo_id}")
            return False
        
        query = "DELETE FROM todos WHERE id = ?"
        self.storage.execute_update(query, (todo_id,))
        
        logger.info(f"Todo deleted: {todo_id}")
        return True

    def get_pending_todos(self) -> List[TodoItem]:
        """Get all incomplete todo items."""
        query = "SELECT * FROM todos WHERE is_done = 0 ORDER BY ddl ASC NULLS LAST, created_at DESC"
        rows = self.storage.execute_query(query)
        return [TodoItem.from_dict(row) for row in rows]

    def mark_reminder_sent(self, todo_id: int, reminder_type: str) -> bool:
        """Mark a reminder as sent (one_day or half_hour)."""
        if reminder_type not in ("one_day", "half_hour"):
            logger.warning(f"Invalid reminder type: {reminder_type}")
            return False

        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        field = "reminded_one_day" if reminder_type == "one_day" else "reminded_half_hour"

        query = f"UPDATE todos SET {field} = 1, updated_at = ? WHERE id = ?"
        self.storage.execute_update(query, (now, todo_id))

        logger.info(f"Marked reminder as sent: todo_id={todo_id}, type={reminder_type}")
        return True