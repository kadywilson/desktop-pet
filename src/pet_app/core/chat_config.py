import yaml
from pathlib import Path
from typing import Dict, List, Optional
from pet_app.utils.paths import get_project_root
from pet_app.utils.logger import logger


class ChatConfig:
    """Chat configuration."""

    DEFAULT_CONFIG = {
        "chat": {
            "enabled": True,
            "memory_file": "data/chat_memory/active_chat.jsonl",
            "archive_dir": "data/chat_memory/archive",
            "max_recent_messages": 12,
            "max_user_input_chars": 300,
            "max_reply_chars": 120,
            "use_memory": False
        },
        "ui": {
            "input_placeholder": "和我说点什么……",
            "opacity": 0.82,
            "min_height": 44,
            "max_height": 180,
            "send_on_enter": True,
            "newline_shortcut": "Shift+Enter"
        },
        "behavior": {
            "show_thinking_bubble": True,
            "thinking_text": "我想想……",
            "hide_chat_does_not_clear_input": True,
            "poke_uses_chat_memory": False,
            "todo_reminder_uses_chat_memory": False
        },
        "chat_personality": {
            "mode": "short_companion_chat",
            "relationship": "熟悉的陪伴型桌宠，不是客服，不是老师",
            "reply_style": [
                "像熟人聊天",
                "可以接住用户的情绪",
                "不要每次都讲大道理",
                "不要把每句话都变成提醒或建议",
                "可以轻微吐槽，但要可爱",
                "可以偶尔追问一句，但不要连续追问"
            ],
            "emotional_rules": [
                "用户只是闲聊时，优先 default 或 happy",
                "用户表达压力时，可以温柔一点，不要嘲讽",
                "用户明显开心时，可以 happy",
                "annoyed 只用于轻微傲娇或玩笑式吐槽",
                "upset 只用于低落、担心或委屈，不要频繁使用",
                "不要连续多次使用同一个 emotion"
            ],
            "content_rules": [
                "回复不要超过 chat.max_reply_chars 个汉字",
                "可以根据用户的话自然回应",
                "不要像搜索引擎一样列很多点",
                "不要主动提 todo，除非用户提到任务、ddl、作业、考试",
                "不要读取待办事项数据库",
                "不要读取 DDL 提醒上下文",
                "不要说自己是 AI、语言模型或助手"
            ]
        }
    }

    def __init__(self, data: Dict = None):
        """Initialize chat config."""
        if data is None:
            data = self.DEFAULT_CONFIG.copy()

        # Top-level sections
        chat = data.get("chat", {})
        self.enabled = chat.get("enabled", True)
        self.memory_file = chat.get("memory_file", "data/chat_memory/active_chat.jsonl")
        self.archive_dir = chat.get("archive_dir", "data/chat_memory/archive")
        self.max_recent_messages = chat.get("max_recent_messages", 12)
        self.max_user_input_chars = chat.get("max_user_input_chars", 300)
        self.max_reply_chars = chat.get("max_reply_chars", 120)
        self.use_memory = chat.get("use_memory", False)

        # UI settings
        ui = data.get("ui", {})
        self.input_placeholder = ui.get("input_placeholder", "和我说点什么……")
        self.opacity = ui.get("opacity", 0.82)
        self.min_height = ui.get("min_height", 44)
        self.max_height = ui.get("max_height", 180)
        self.send_on_enter = ui.get("send_on_enter", True)
        self.newline_shortcut = ui.get("newline_shortcut", "Shift+Enter")

        # Behavior settings
        behavior = data.get("behavior", {})
        self.show_thinking_bubble = behavior.get("show_thinking_bubble", True)
        self.thinking_text = behavior.get("thinking_text", "我想想……")
        self.hide_chat_does_not_clear_input = behavior.get("hide_chat_does_not_clear_input", True)
        self.poke_uses_chat_memory = behavior.get("poke_uses_chat_memory", False)
        self.todo_reminder_uses_chat_memory = behavior.get("todo_reminder_uses_chat_memory", False)

        # Chat personality
        chat_personality = data.get("chat_personality", {})
        self.chat_mode = chat_personality.get("mode", "short_companion_chat")
        self.relationship = chat_personality.get("relationship", "熟悉的陪伴型桌宠")
        self.reply_style = chat_personality.get("reply_style", [])
        self.emotional_rules = chat_personality.get("emotional_rules", [])
        self.content_rules = chat_personality.get("content_rules", [])


class ChatConfigManager:
    """Load and manage chat configuration."""

    def __init__(self):
        """Initialize chat config manager."""
        self.config = None
        self.load_config()

    def load_config(self) -> ChatConfig:
        """Load chat configuration from YAML."""
        config_path = get_project_root() / "config" / "chat.yaml"

        if not config_path.exists():
            logger.warning(f"Chat config file not found at {config_path}, using defaults")
            self.config = ChatConfig()
            return self.config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.warning("Chat config YAML is empty, using defaults")
                self.config = ChatConfig()
            else:
                self.config = ChatConfig(data)
                logger.info("Chat config loaded successfully")

            return self.config
        except Exception as e:
            logger.error(f"Failed to load chat config: {e}, using defaults")
            self.config = ChatConfig()
            return self.config

    def get_config(self) -> ChatConfig:
        """Get loaded chat config."""
        return self.config
