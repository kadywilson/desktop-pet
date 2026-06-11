import sqlite3
from pathlib import Path
from pet_app.utils.paths import get_project_root, get_data_dir
from pet_app.utils.logger import logger


class StorageManager:
    """Manage SQLite database connection and initialization."""

    def __init__(self):
        """Initialize storage manager."""
        self.db_path = get_data_dir() / "pet.db"
        self.connection = None
        self.init_db()

    def init_db(self):
        """Initialize database and create tables if they don't exist."""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            cursor = self.connection.cursor()
            
            # Create todos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    ddl TEXT,
                    is_done INTEGER NOT NULL DEFAULT 0,
                    reminded_one_day INTEGER NOT NULL DEFAULT 0,
                    reminded_half_hour INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            self.connection.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self.connection is None:
            self.init_db()
        return self.connection

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """Execute a SELECT query."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT, UPDATE, or DELETE query."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            logger.info(f"Update successful, rows affected: {cursor.rowcount}")
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.connection.rollback()
            raise

    def get_last_insert_id(self) -> int:
        """Get ID of last inserted row."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT last_insert_rowid() as id")
        return cursor.fetchone()[0]