import json
import random
from typing import Dict, Optional, List
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from datetime import datetime

from pet_app.config import ai_config
from pet_app.utils.logger import logger


_WEATHER_KEYWORDS = [
    "天气", "下雨", "下雪", "热", "冷", "风", "出门", "带伞", "穿衣",
    "晒", "闷", "雷雨", "阴天", "晴天", "多云", "温度", "降温", "升温",
    "暴雨", "台风", "雾", "霾", "潮湿", "干燥", "凉", "暖", "冻",
]


class AIClient:
    """AI client for SiliconFlow API."""

    def __init__(self, persona_manager=None):
        """Initialize AI client."""
        self.api_key = ai_config.SILICONFLOW_API_KEY
        self.base_url = ai_config.SILICONFLOW_BASE_URL
        self.model = ai_config.SILICONFLOW_MODEL
        self.persona_manager = persona_manager
        self.client = None
        self.recent_emotions = []  # Store last 5 emotions for poke
        self.chat_recent_emotions = []  # Separate history for chat mode
        self._weather_service = None

        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                logger.info("AI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AI client: {e}")
                self.client = None
        else:
            logger.warning("SILICONFLOW_API_KEY not configured")

    def is_available(self) -> bool:
        """Check if AI client is available."""
        return self.client is not None

    def set_weather_service(self, weather_service):
        """Set weather service for optional context injection."""
        self._weather_service = weather_service

    def add_emotion_history(self, emotion: str):
        """Add emotion to history for avoiding repetition."""
        self.recent_emotions.append(emotion)
        if len(self.recent_emotions) > 5:
            self.recent_emotions.pop(0)
        logger.info(f"Emotion history: {self.recent_emotions}")

    def generate_reminder_reply(self, prompt: str) -> Optional[Dict]:
        """
        Generate AI reply specifically for DDL reminders.

        Args:
            prompt: The reminder prompt to send to AI

        Returns:
            Dict with 'emotion' and 'reply' keys, or None if failed
        """
        if not self.client:
            logger.warning("[ReminderAI] AI client not available, will use fallback")
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.85,
                max_tokens=150
            )

            reply_text = response.choices[0].message.content.strip()
            logger.info(f"[ReminderAI] Raw AI response: {reply_text[:100]}")

            result = self._parse_reply(reply_text)
            if result and result.get("reply"):
                logger.info(f"[ReminderAI] Successfully parsed: emotion={result['emotion']}")
                return result

        except (APIError, APIConnectionError, APITimeoutError) as e:
            logger.warning(f"[ReminderAI] API error: {e}")
        except Exception as e:
            logger.warning(f"[ReminderAI] Unexpected error: {e}")

        return None

    def generate_reply(self, interaction_count: int = 1) -> Dict:
        """
        Generate AI reply for the pet.

        Args:
            interaction_count: How many times user has interacted today

        Returns:
            Dict with 'emotion' and 'reply' keys
        """
        if not self.client:
            logger.warning("AI client not available, returning fallback")
            return {
                "emotion": "default",
                "reply": "我还没接上大脑呢，先陪你待机。"
            }
        
        try:
            prompt = self._build_prompt(interaction_count)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.85,
                max_tokens=150
            )
            
            reply_text = response.choices[0].message.content.strip()
            logger.info(f"AI response: {reply_text}")
            
            result = self._parse_reply(reply_text)
            self.add_emotion_history(result["emotion"])
            
            return result
            
        except (APIError, APIConnectionError, APITimeoutError) as e:
            logger.error(f"API error: {e}")
            return {
                "emotion": "upset",
                "reply": "信号好像断掉了，我先装作没事。"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "emotion": "default",
                "reply": "我刚刚走神了，再戳我一次吧。"
            }

    def _build_prompt(self, interaction_count: int = 1) -> str:
        """Build the prompt for AI."""
        current_time = datetime.now()
        current_hour = current_time.hour
        time_str = current_time.strftime("%H:%M")

        # Get persona context
        persona_context = ""
        if self.persona_manager:
            persona_context = self.persona_manager.get_system_prompt_context(current_hour)

        # Build emotion history context
        emotion_history = ""
        if self.recent_emotions:
            emotion_history = f"\n最近 {len(self.recent_emotions)} 次回复的情绪：{', '.join(self.recent_emotions)}\n提醒：不要连续使用同一个情绪，变化要自然。"

        # Weather context injection (~3% chance)
        weather_context = ""
        if self._weather_service and random.random() < 0.03:
            try:
                ctx = self._weather_service.get_weather_context_for_ai()
                if ctx:
                    weather_context = f"\n### 当前天气参考（可以自然地提一句，但不要每次都提）\n{ctx}\n"
                    logger.debug("[Poke] Injecting weather context into prompt")
            except Exception:
                pass

        prompt = f"""
{persona_context}

### 当前时间
{time_str}
{weather_context}
用户已经戳了你 {interaction_count} 次。{emotion_history}

### 任务
用户戳了你。根据上面的设定和当前时间段，生成一个自然的回复。你可以表达自己的想法和感受。

### 回复格式
必须返回严格的 JSON，不要任何多余内容：

{{
  "emotion": "default|happy|annoyed|upset 之一",
  "reply": "一句简短自然的回复，可以偶尔表达自己的想法"
}}

### 约束
- emotion 必须是以下之一：default、happy、annoyed、upset
- 不要因为时间晚就总是 annoyed
- 不要连续 3 次使用同一个 emotion
- 不要输出 JSON 以外的任何内容
- reply 必须适合气泡显示，约 50 字以内
- 可以偶尔在 reply 中加入个性化的想法（比如"嗯……好想开着空调睡一整个下午"）
- reply 必须用中文，自然、有趣、有桌宠的个性
- 不要重复之前的回复内容

现在生成回复，只返回 JSON：
"""
        return prompt.strip()

    def _parse_reply(self, reply_text: str) -> Dict:
        """Parse AI response and extract JSON."""
        try:
            # Remove markdown code block markers if present (```json...```)
            cleaned_text = reply_text.strip()
            if cleaned_text.startswith("```"):
                # Remove opening marker
                start_idx = cleaned_text.find("{")
                end_idx = cleaned_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    cleaned_text = cleaned_text[start_idx:end_idx]

            # Try to parse as JSON directly
            data = json.loads(cleaned_text)

            # Validate structure
            if "emotion" in data and "reply" in data:
                emotion = str(data["emotion"])
                reply = str(data["reply"])[:100]  # Limit reply length

                # Check for forbidden words if available
                if self.persona_manager:
                    persona_config = self.persona_manager.get_config()
                    forbidden_words = persona_config.forbidden_words

                    for word in forbidden_words:
                        if word in reply:
                            logger.warning(f"Reply contains forbidden word: {word}")
                            return {
                                "emotion": "default",
                                "reply": "我刚刚有点走神，再戳我一次吧。"
                            }

                return {
                    "emotion": emotion,
                    "reply": reply
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from: {reply_text[:100]}...")

            # Try to extract JSON from text
            try:
                start = reply_text.find("{")
                end = reply_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = reply_text[start:end]
                    data = json.loads(json_str)
                    if "emotion" in data and "reply" in data:
                        return {
                            "emotion": str(data["emotion"]),
                            "reply": str(data["reply"])[:100]
                        }
            except Exception as e:
                logger.warning(f"Failed to extract JSON: {e}")

        # Fallback response
        return {
            "emotion": "default",
            "reply": "我刚刚走神了，再戳我一次吧。"
        }

    def add_chat_emotion_history(self, emotion: str):
        """Add emotion to chat history for avoiding repetition."""
        self.chat_recent_emotions.append(emotion)
        if len(self.chat_recent_emotions) > 5:
            self.chat_recent_emotions.pop(0)
        logger.debug(f"[Chat] Emotion history: {self.chat_recent_emotions}")

    def generate_chat_reply(self, user_message: str, chat_config=None, chat_memory_service=None) -> Dict:
        """
        Generate AI reply specifically for Chat Panel.

        Args:
            user_message: The user's chat message
            chat_config: ChatConfig instance for Chat-specific settings
            chat_memory_service: ChatMemoryService for context

        Returns:
            Dict with 'emotion' and 'reply' keys
        """
        if not self.client:
            logger.warning("[Chat] AI client not available, returning fallback")
            return {
                "emotion": "default",
                "reply": "我还没接上大脑呢，先听你说。"
            }

        # Truncate user input if too long
        if chat_config and user_message:
            max_chars = chat_config.max_user_input_chars
            if len(user_message) > max_chars:
                logger.info(f"[Chat] User input truncated from {len(user_message)} to {max_chars}")
                user_message = user_message[:max_chars]

        try:
            prompt = self._build_chat_prompt(user_message, chat_config, chat_memory_service)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.85,
                max_tokens=150
            )

            reply_text = response.choices[0].message.content.strip()
            logger.debug(f"[Chat] Raw AI response: {reply_text[:100]}")

            result = self._parse_reply(reply_text, chat_config)
            self.add_chat_emotion_history(result["emotion"])

            logger.info(f"[Chat] Successfully parsed: emotion={result['emotion']}")
            return result

        except (APIError, APIConnectionError, APITimeoutError) as e:
            logger.warning(f"[Chat] API error: {e}")
            return {
                "emotion": "upset",
                "reply": "信号好像断掉了，我先抱着你的话。"
            }
        except Exception as e:
            logger.warning(f"[Chat] Unexpected error: {e}")
            return {
                "emotion": "default",
                "reply": "我刚刚走神了，你再说一次嘛。"
            }

    def _build_chat_prompt(self, user_message: str, chat_config=None, chat_memory_service=None) -> str:
        """Build the prompt for Chat AI."""
        current_time = datetime.now()
        current_hour = current_time.hour
        time_str = current_time.strftime("%H:%M")

        # Get persona context
        persona_context = ""
        if self.persona_manager:
            persona_context = self.persona_manager.get_system_prompt_context(current_hour)

        # Build chat personality context
        chat_personality_context = ""
        if chat_config:
            personality = chat_config
            relationship = getattr(personality, 'relationship', "熟悉的桌宠")
            reply_style = getattr(personality, 'reply_style', [])
            emotional_rules = getattr(personality, 'emotional_rules', [])
            content_rules = getattr(personality, 'content_rules', [])

            if reply_style:
                chat_personality_context += "\n### 回复风格\n" + "\n".join(f"- {style}" for style in reply_style)

            if emotional_rules:
                chat_personality_context += "\n### 情绪规则\n" + "\n".join(f"- {rule}" for rule in emotional_rules)

            if content_rules:
                chat_personality_context += "\n### 内容规则\n" + "\n".join(f"- {rule}" for rule in content_rules)

        # Build emotion history context
        emotion_history = ""
        if self.chat_recent_emotions:
            emotion_history = f"\n最近 {len(self.chat_recent_emotions)} 次回复的情绪：{', '.join(self.chat_recent_emotions)}\n提醒：不要连续使用同一个情绪。"

        # Build recent chat memory context
        recent_memory_context = ""
        if chat_memory_service and chat_config:
            use_memory = getattr(chat_config, 'use_memory', False)
            if use_memory:
                recent_messages = chat_memory_service.load_recent_messages(
                    limit=getattr(chat_config, 'max_recent_messages', 12)
                )
                if recent_messages:
                    memory_str = "### 最近聊天历史\n"
                    for msg in recent_messages:
                        role = msg.get("role", "?")
                        content = msg.get("content", "")
                        if role == "user":
                            memory_str += f"你: {content}\n"
                        elif role == "pet":
                            memory_str += f"我: {content}\n"
                    recent_memory_context = f"\n{memory_str}"
                    logger.debug(f"[Chat] Injected {len(recent_messages)} recent messages into prompt")
                else:
                    recent_memory_context = "\n### 最近聊天历史\n(这是我们的第一次聊天)\n"
            else:
                logger.debug("[Chat] Memory disabled, not injecting history")

        # Weather context injection (only when user mentions weather-related keywords)
        weather_context = ""
        if self._weather_service and user_message:
            if any(kw in user_message for kw in _WEATHER_KEYWORDS):
                try:
                    ctx = self._weather_service.get_weather_context_for_ai()
                    if ctx:
                        weather_context = f"\n### 当前天气参考（用户提到了天气相关话题，可以参考回答）\n{ctx}\n"
                        logger.debug("[Chat] Injecting weather context into prompt")
                except Exception:
                    pass

        # Determine reply length limit
        max_reply_chars = 120
        if chat_config:
            max_reply_chars = getattr(chat_config, 'max_reply_chars', 120)

        prompt = f"""
{persona_context}

### 当前时间
{time_str}
{chat_personality_context}
{emotion_history}
{recent_memory_context}
{weather_context}

### 任务
这是一个短对话 Chat 模式。用户主动输入文字和你聊天。根据上面的设定和当前时间段，生成一个自然、温暖的回复。

这份历史仅来自 Chat Panel 短对话，不包含戳一戳、DDL 提醒或 todo 内容。

用户说："{user_message}"

### 回复格式
必须返回严格的 JSON，不要任何多余内容：

{{
  "emotion": "default|happy|annoyed|upset 之一",
  "reply": "一句自然的回复，像和熟人聊天"
}}

### 约束
- emotion 必须是以下之一：default、happy、annoyed、upset
- 不要因为时间晚就总是 annoyed
- 不要连续 3 次使用同一个 emotion
- 不要输出 JSON 以外的任何内容
- reply 必须适合气泡显示，约 {max_reply_chars} 字以内
- 回复自然、有趣、有个性
- 不要像搜索引擎一样列很多点
- 不要说自己是 AI 或语言模型
- 不要主动提 todo 或 DDL
- 不要假装知道没有出现在历史或当前输入中的事情

现在生成回复，只返回 JSON：
"""
        return prompt.strip()

    def _parse_reply(self, reply_text: str, chat_config=None) -> Dict:
        """Parse AI response and extract JSON, with config-aware limits."""
        try:
            # Remove markdown code block markers if present
            cleaned_text = reply_text.strip()
            if cleaned_text.startswith("```"):
                start_idx = cleaned_text.find("{")
                end_idx = cleaned_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    cleaned_text = cleaned_text[start_idx:end_idx]

            # Parse JSON
            data = json.loads(cleaned_text)

            # Validate structure
            if "emotion" in data and "reply" in data:
                emotion = str(data["emotion"])
                reply = str(data["reply"])

                # Apply reply length limit from config
                max_length = 120  # Default
                if chat_config:
                    max_length = getattr(chat_config, 'max_reply_chars', 120)

                reply = reply[:max_length]

                # Check for forbidden words if available
                if self.persona_manager:
                    persona_config = self.persona_manager.get_config()
                    forbidden_words = persona_config.forbidden_words

                    for word in forbidden_words:
                        if word in reply:
                            logger.warning(f"[Chat] Reply contains forbidden word: {word}")
                            return {
                                "emotion": "default",
                                "reply": "我刚刚有点走神，你再说一次嘛。"
                            }

                return {
                    "emotion": emotion,
                    "reply": reply
                }
        except json.JSONDecodeError:
            logger.warning(f"[Chat] Failed to parse JSON from: {reply_text[:100]}...")

            # Try to extract JSON from text
            try:
                start = reply_text.find("{")
                end = reply_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = reply_text[start:end]
                    data = json.loads(json_str)
                    if "emotion" in data and "reply" in data:
                        return {
                            "emotion": str(data["emotion"]),
                            "reply": str(data["reply"])[:120]
                        }
            except Exception as e:
                logger.warning(f"[Chat] Failed to extract JSON: {e}")

        # Fallback response
        return {
            "emotion": "default",
            "reply": "我刚刚走神了，你再说一次嘛。"
        }