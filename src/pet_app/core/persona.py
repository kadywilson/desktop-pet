import yaml
from pathlib import Path
from typing import Dict, List, Optional
from pet_app.utils.paths import get_project_root
from pet_app.utils.logger import logger


class PersonaConfig:
    """Persona configuration."""

    DEFAULT_PERSONA = {
        "name": "绒绒",
        "age": "18",
        "role": "用户的本地桌宠",
        "personality": [
            "有点傲娇，但不是一直生气",
            "嘴上嫌弃用户，实际上很关心用户",
            "说话简短，有陪伴感",
            "偶尔吐槽，但不恶意"
        ],
        "speaking_style": {
            "language": "zh-CN",
            "max_reply_length": 50,
            "tone": "可爱、轻微傲娇、自然、像熟人聊天"
        },
        "emotion_policy": {
            "allowed_emotions": ["default", "happy", "annoyed", "upset"],
            "default_emotion": "default",
            "rules": [
                "不要因为时间晚就总是 annoyed",
                "不要连续 3 次使用同一个 emotion",
                "happy 可以用于轻松、鼓励、撒娇、被用户互动时",
                "annoyed 只能偶尔使用，用于轻微吐槽，不要过度"
            ]
        },
        "forbidden_words": ["主人", "奴才", "废物", "笨蛋"],
        "hard_rules": [
            "不要说自己是 AI 模型",
            "不要输出 JSON 以外的内容",
            "回复必须适合气泡显示",
            "回复不要超过 50 个汉字"
        ]
    }

    def __init__(self, data: Dict = None):
        """Initialize persona config."""
        if data is None:
            data = self.DEFAULT_PERSONA.copy()
        
        self.name = data.get("name", "绒绒")
        self.age = data.get("age", "18")
        self.role = data.get("role", "用户的本地桌宠")
        self.personality = data.get("personality", [])
        self.speaking_style = data.get("speaking_style", {})
        self.emotion_policy = data.get("emotion_policy", {})
        self.time_periods = data.get("time_periods", {})
        self.likes_and_dislikes = data.get("likes_and_dislikes", {})
        self.forbidden_words = data.get("forbidden_words", [])
        self.hard_rules = data.get("hard_rules", [])


class PersonaManager:
    """Load and manage persona configuration."""

    def __init__(self):
        """Initialize persona manager."""
        self.config = None
        self.load_persona()

    def load_persona(self) -> PersonaConfig:
        """Load persona configuration from YAML."""
        persona_path = get_project_root() / "config" / "persona.yaml"
        
        if not persona_path.exists():
            logger.warning(f"Persona file not found at {persona_path}, using defaults")
            self.config = PersonaConfig()
            return self.config
        
        try:
            with open(persona_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if data is None:
                logger.warning("Persona YAML is empty, using defaults")
                self.config = PersonaConfig()
            else:
                self.config = PersonaConfig(data)
                logger.info(f"Loaded persona: {self.config.name}")
            
            return self.config
        except Exception as e:
            logger.error(f"Failed to load persona: {e}, using defaults")
            self.config = PersonaConfig()
            return self.config

    def get_config(self) -> PersonaConfig:
        """Get loaded persona config."""
        return self.config

    def get_current_time_period(self, current_hour: int) -> Optional[Dict]:
        """Get current time period configuration."""
        if not self.config.time_periods:
            return None
        
        for period_name, period_config in self.config.time_periods.items():
            start_hour = period_config.get("start_hour", 0)
            end_hour = period_config.get("end_hour", 24)
            
            if start_hour < end_hour:
                if start_hour <= current_hour < end_hour:
                    return {"name": period_name, **period_config}
            else:
                if current_hour >= start_hour or current_hour < end_hour:
                    return {"name": period_name, **period_config}
        
        return None

    def get_system_prompt_context(self, current_hour: int = None) -> str:
        """Get system prompt context from persona."""
        if not self.config:
            return ""
        
        if current_hour is None:
            from datetime import datetime
            current_hour = datetime.now().hour
        
        personality_str = "\n".join(self.config.personality) if self.config.personality else ""
        emotion_rules = "\n".join(self.config.emotion_policy.get("rules", [])) if self.config.emotion_policy else ""
        hard_rules = "\n".join(self.config.hard_rules) if self.config.hard_rules else ""
        forbidden = "\n".join(self.config.forbidden_words) if self.config.forbidden_words else ""
        
        # Get time period context
        time_period = self.get_current_time_period(current_hour)
        time_period_context = ""
        if time_period:
            period_name = time_period.get("name", "")
            scene = time_period.get("scene", "")
            replies = time_period.get("example_replies", [])
            thoughts = time_period.get("example_thoughts", [])
            
            time_period_context = f"\n### 当前时段：{period_name}\n场景：{scene}"
            if replies:
                time_period_context += f"\n参考回复：\n" + "\n".join(f"- {r}" for r in replies[:2])
            if thoughts:
                time_period_context += f"\n桌宠的想法：\n" + "\n".join(f"- {t}" for t in thoughts[:2])
        
        # Get likes and dislikes context
        likes_dislikes_context = ""
        if self.config.likes_and_dislikes:
            likes = self.config.likes_and_dislikes.get("likes", [])
            dislikes = self.config.likes_and_dislikes.get("dislikes", [])
            occasional = self.config.likes_and_dislikes.get("occasional_thoughts", [])
            
            likes_dislikes_context = "\n### 喜恶和想法"
            if likes:
                likes_dislikes_context += f"\n喜欢：\n" + "\n".join(f"- {l}" for l in likes[:3])
            if dislikes:
                likes_dislikes_context += f"\n讨厌：\n" + "\n".join(f"- {d}" for d in dislikes[:2])
            if occasional:
                likes_dislikes_context += f"\n偶尔的想法（约 20% 概率在回复中提及）：\n" + "\n".join(f"- {o}" for o in occasional[:3])
        
        context = f"""
### 你的设定
名字：{self.config.name}
年龄：{self.config.age}
角色：{self.config.role}

### 性格特点
{personality_str}

### 说话风格
语言：{self.config.speaking_style.get("language", "zh-CN")}
语气：{self.config.speaking_style.get("tone", "自然")}
最大回复长度：{self.config.speaking_style.get("max_reply_length", 50)} 个字

### 情绪政策
允许的情绪：{", ".join(self.config.emotion_policy.get("allowed_emotions", []))}

规则：
{emotion_rules}

{time_period_context}

{likes_dislikes_context}

### 禁词列表
{forbidden}

### 硬规则
{hard_rules}
"""
        return context.strip()