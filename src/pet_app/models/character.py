from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ImageSize:
    """Image size configuration."""
    width: int
    height: int


@dataclass
class BubbleOffset:
    """Bubble position offset."""
    x: int
    y: int


class CharacterConfig:
    """Character configuration loaded from manifest.json."""

    def __init__(self, data: Dict):
        """Initialize from manifest dictionary."""
        self.id = data.get("id", "default_pet")
        self.name = data.get("name", "默认桌宠")
        self.description = data.get("description", "")
        
        size_data = data.get("image_size", {"width": 240, "height": 240})
        self.image_size = ImageSize(
            width=size_data.get("width", 240),
            height=size_data.get("height", 240)
        )
        
        offset_data = data.get("bubble_offset", {"x": 0, "y": -100})
        self.bubble_offset = BubbleOffset(
            x=offset_data.get("x", 0),
            y=offset_data.get("y", -100)
        )
        
        self.expressions = data.get("expressions", {
            "default": "default.png",
            "happy": "happy.png",
            "annoyed": "annoyed.png",
            "upset": "upset.png"
        })
        self.default_expression = data.get("default_expression", "default")
        self.persona = data.get("persona", "")

    def get_expression_path(self, expression: str) -> Optional[str]:
        """Get the image filename for an expression."""
        return self.expressions.get(expression)

    def get_all_expressions(self) -> list:
        """Get list of all available expressions."""
        return list(self.expressions.keys())
