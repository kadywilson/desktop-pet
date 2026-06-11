from datetime import datetime
from typing import Dict, Optional
from pet_app.core.ai_client import AIClient
from pet_app.core.chat_memory import ChatMemoryService
from pet_app.utils.logger import logger


class ConversationService:
    """Manage pet conversations."""

    def __init__(self, ai_client: AIClient, chat_memory_service: Optional[ChatMemoryService] = None):
        """Initialize conversation service."""
        self.ai_client = ai_client
        self.interaction_count = 0  # For poke interactions
        self.chat_memory_service = chat_memory_service

    def get_ai_response(self) -> Dict:
        """Get AI response for poke (double-click) interaction."""
        self.interaction_count += 1
        current_time = datetime.now().strftime("%H:%M")

        logger.info(f"Getting AI response #{self.interaction_count} at {current_time}")

        response = self.ai_client.generate_reply(self.interaction_count)

        logger.info(f"AI response: emotion={response.get('emotion')}, reply={response.get('reply')}")

        return response

    def get_chat_response(self, user_message: str, chat_config=None) -> Dict:
        """
        Get AI response for Chat Panel interaction.

        Args:
            user_message: The user's chat message
            chat_config: ChatConfig instance for Chat-specific settings

        Returns:
            Dict with 'emotion' and 'reply' keys
        """
        if not user_message or not user_message.strip():
            logger.debug("Chat message is empty, skipping AI call")
            return None

        current_time = datetime.now().strftime("%H:%M")
        logger.info(f"[Chat] Getting chat response at {current_time}")

        # Pass chat memory service to AI client for memory context
        response = self.ai_client.generate_chat_reply(user_message, chat_config, self.chat_memory_service)

        logger.info(f"[Chat] Response: emotion={response.get('emotion')}, reply={response.get('reply')[:50]}...")

        return response

    def append_chat_user_message(self, content: str) -> bool:
        """Append user message to chat memory."""
        if self.chat_memory_service:
            return self.chat_memory_service.append_user_message(content)
        return False

    def append_chat_pet_reply(self, content: str, emotion: str) -> bool:
        """Append pet reply to chat memory."""
        if self.chat_memory_service:
            return self.chat_memory_service.append_pet_reply(content, emotion)
        return False
