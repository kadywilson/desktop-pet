import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from pet_app.utils.logger import logger


class ChatMemoryService:
    """Manage Chat Panel conversation memory in JSONL format."""

    def __init__(self, memory_file: str, archive_dir: str, max_recent_messages: int = 12):
        """
        Initialize chat memory service.

        Args:
            memory_file: Path to active_chat.jsonl (relative to project root)
            archive_dir: Path to archive directory (relative to project root)
            max_recent_messages: Maximum number of recent messages to load
        """
        from pet_app.utils.paths import get_project_root

        self.project_root = get_project_root()
        self.memory_file = self.project_root / memory_file
        self.archive_dir = self.project_root / archive_dir
        self.max_recent_messages = max_recent_messages

        self.ensure_storage()

    def ensure_storage(self) -> None:
        """Create memory file and archive directory if they don't exist."""
        try:
            # Create archive directory
            self.archive_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Chat memory archive dir ready: {self.archive_dir}")

            # Create parent directory for memory file
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)

            # Create or ensure memory file exists
            if not self.memory_file.exists():
                self.memory_file.touch()
                logger.info(f"Created new chat memory file: {self.memory_file}")
            else:
                logger.debug(f"Chat memory file exists: {self.memory_file}")

        except Exception as e:
            logger.error(f"Failed to ensure chat memory storage: {e}")

    def append_user_message(self, content: str) -> bool:
        """
        Append user message to memory.

        Args:
            content: User message text

        Returns:
            True if successful, False otherwise
        """
        if not content or not content.strip():
            logger.debug("Chat memory: empty user message, skipping")
            return False

        try:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            message = {
                "timestamp": timestamp,
                "role": "user",
                "content": content.strip(),
                "source": "chat"
            }

            with open(self.memory_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(message, ensure_ascii=False) + "\n")

            logger.debug(f"Chat memory: appended user message: {content[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to append user message to chat memory: {e}")
            return False

    def append_pet_reply(self, content: str, emotion: str) -> bool:
        """
        Append pet reply to memory.

        Args:
            content: Pet reply text
            emotion: Pet emotion/expression

        Returns:
            True if successful, False otherwise
        """
        if not content or not content.strip():
            logger.debug("Chat memory: empty pet reply, skipping")
            return False

        try:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            message = {
                "timestamp": timestamp,
                "role": "pet",
                "content": content.strip(),
                "emotion": emotion,
                "source": "chat_reply"
            }

            with open(self.memory_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(message, ensure_ascii=False) + "\n")

            logger.debug(f"Chat memory: appended pet reply with emotion {emotion}: {content[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to append pet reply to chat memory: {e}")
            return False

    def append_diary_context(self, content: str) -> bool:
        """Append a diary context note exported from diary_ai."""
        return self._append_message(
            {
                "role": "user",
                "content": content,
                "source": "diary_context",
            }
        )

    def append_diary_context_reply(self, content: str, emotion: str = "default") -> bool:
        """Append the pet's local acknowledgement for a diary context note."""
        return self._append_message(
            {
                "role": "pet",
                "content": content,
                "emotion": emotion,
                "source": "diary_context_reply",
            }
        )

    def _append_message(self, message: Dict) -> bool:
        content = str(message.get("content") or "").strip()
        if not content:
            logger.debug("Chat memory: empty custom message, skipping")
            return False

        try:
            message = dict(message)
            message["timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            message["content"] = content

            with open(self.memory_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(message, ensure_ascii=False) + "\n")

            logger.debug(
                f"Chat memory: appended {message.get('source', 'custom')}: {content[:50]}..."
            )
            return True
        except Exception as e:
            logger.error(f"Failed to append custom message to chat memory: {e}")
            return False

    def load_recent_messages(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Load recent messages from memory.

        Args:
            limit: Maximum number of messages to load. If None, uses max_recent_messages.

        Returns:
            List of message dicts, in chronological order
        """
        if limit is None:
            limit = self.max_recent_messages

        messages = []

        try:
            if not self.memory_file.exists():
                logger.debug("Chat memory file does not exist yet")
                return messages

            with open(self.memory_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Parse all valid lines
            all_messages = []
            for i, line in enumerate(lines):
                try:
                    msg = json.loads(line.strip())
                    # Validate message structure
                    if "timestamp" in msg and "role" in msg and "content" in msg:
                        all_messages.append(msg)
                except json.JSONDecodeError:
                    logger.warning(f"Chat memory: skipped invalid JSON at line {i+1}: {line[:50]}...")
                except Exception as e:
                    logger.warning(f"Chat memory: error parsing line {i+1}: {e}")

            # Return last N messages
            messages = all_messages[-limit:] if len(all_messages) > limit else all_messages

            if messages:
                logger.debug(f"Chat memory: loaded {len(messages)} recent messages")
            else:
                logger.debug("Chat memory: no valid messages found")

            return messages

        except Exception as e:
            logger.error(f"Failed to load chat memory: {e}")
            return messages

    def archive_current_memory(self) -> Optional[Path]:
        """
        Archive current chat memory and start a new active memory.

        This is the primary method for Stage 4.
        Semantics: "Archive current chat memory, start a new memory segment"
        NOT "delete" or "say goodbye".

        Returns:
            Path to archived file if successful, None if no content to archive, raises exception on error
        """
        try:
            # Ensure storage exists first
            self.ensure_storage()

            # Check if memory file has content
            if not self.memory_file.exists():
                logger.info("Chat memory: no active memory file exists")
                # Ensure it exists for next time
                self.memory_file.touch()
                return None

            file_size = self.memory_file.stat().st_size
            if file_size == 0:
                logger.info("Chat memory: active memory is empty, nothing to archive")
                return None

            # Read current content
            with open(self.memory_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Create archive filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = self.archive_dir / f"chat_{timestamp}.jsonl"

            # Handle filename collision (unlikely but safe)
            counter = 1
            base_archive_file = archive_file
            while archive_file.exists():
                archive_file = self.archive_dir / f"chat_{timestamp}_{counter}.jsonl"
                counter += 1

            # Write to archive file
            with open(archive_file, "w", encoding="utf-8") as dst:
                dst.write(content)

            logger.info(f"Chat memory archived to: {archive_file}")

            # Truncate active file to empty (start new memory segment)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                f.truncate(0)

            logger.info("Chat memory: active memory cleared, new memory segment started")
            return archive_file

        except Exception as e:
            logger.error(f"Failed to archive current chat memory: {e}")
            raise

    def archive_and_clear(self) -> Optional[Path]:
        """
        Alias for archive_current_memory() for backward compatibility.

        Returns:
            Path to archived file if successful, None if no content, raises on error
        """
        return self.archive_current_memory()

    def get_memory_stats(self) -> Dict:
        """
        Get statistics about chat memory.

        Returns:
            Dictionary with memory stats
        """
        try:
            messages = self.load_recent_messages(limit=None)
            user_msgs = [m for m in messages if m.get("role") == "user"]
            pet_msgs = [m for m in messages if m.get("role") == "pet"]

            return {
                "total_messages": len(messages),
                "user_messages": len(user_msgs),
                "pet_messages": len(pet_msgs),
                "memory_file_exists": self.memory_file.exists(),
                "memory_file_size": self.memory_file.stat().st_size if self.memory_file.exists() else 0,
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
