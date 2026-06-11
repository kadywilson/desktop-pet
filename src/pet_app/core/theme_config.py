"""Theme configuration for the pet bubble and chat input."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from pet_app.utils.logger import logger
from pet_app.utils.paths import get_project_root


DEFAULT_THEME_ID = "milk"


@dataclass(frozen=True)
class ThemeStyle:
    theme_id: str
    display_name: str
    bubble_background: str
    bubble_background_solid: str
    bubble_border: str
    bubble_text: str
    bubble_shadow: str
    input_background: str
    input_border: str
    input_focus_border: str
    input_text: str
    input_placeholder: str
    input_selection: str
    accent: str
    font_family: str = "Microsoft YaHei UI"
    font_fallback: str = "Microsoft YaHei"
    bubble_font_size: int = 12
    input_font_size: int = 11
    bubble_font_weight: int = 500
    bubble_radius: int = 24
    input_radius: int = 16
    bubble_max_width: int = 260


THEMES: dict[str, ThemeStyle] = {
    "milk": ThemeStyle(
        theme_id="milk",
        display_name="Milk",
        bubble_background="rgba(255, 255, 255, 230)",
        bubble_background_solid="#FFFFFF",
        bubble_border="rgba(175, 198, 226, 235)",
        bubble_text="#24292F",
        bubble_shadow="rgba(100, 130, 168, 42)",
        input_background="rgba(255, 255, 255, 220)",
        input_border="rgba(175, 198, 226, 220)",
        input_focus_border="rgba(122, 167, 216, 230)",
        input_text="#3F4650",
        input_placeholder="#8993A0",
        input_selection="#DDEBFA",
        accent="#748398",
    ),
    "peach": ThemeStyle(
        theme_id="peach",
        display_name="Peach",
        bubble_background="rgba(255, 248, 241, 232)",
        bubble_background_solid="#FFF8F1",
        bubble_border="rgba(247, 151, 103, 180)",
        bubble_text="#67331F",
        bubble_shadow="rgba(185, 96, 54, 38)",
        input_background="rgba(255, 251, 247, 224)",
        input_border="rgba(247, 151, 103, 165)",
        input_focus_border="rgba(231, 123, 69, 220)",
        input_text="#6C493A",
        input_placeholder="#A78372",
        input_selection="#FFE3D4",
        accent="#E77B45",
        bubble_radius=22,
    ),
}


class ThemeConfigManager:
    """Load, save, and expose the selected UI theme."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or get_project_root() / "config" / "theme.yaml"
        self.active_theme_id = DEFAULT_THEME_ID
        self.load()

    def load(self) -> ThemeStyle:
        try:
            if not self.config_path.exists():
                logger.info("Theme config missing, creating default theme config")
                self.save()
                return self.get_current_theme()

            with open(self.config_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}

            active = (data.get("theme") or {}).get("active", DEFAULT_THEME_ID)
            if active not in THEMES:
                logger.warning(f"Unknown theme '{active}', falling back to {DEFAULT_THEME_ID}")
                active = DEFAULT_THEME_ID
            self.active_theme_id = active
        except Exception as exc:
            logger.warning(f"Failed to load theme config, using default: {exc}")
            self.active_theme_id = DEFAULT_THEME_ID

        return self.get_current_theme()

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "theme": {
                "active": self.active_theme_id,
            }
        }
        with open(self.config_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(data, file, sort_keys=False, allow_unicode=True)

    def get_current_theme_id(self) -> str:
        return self.active_theme_id

    def get_current_theme(self) -> ThemeStyle:
        return THEMES.get(self.active_theme_id, THEMES[DEFAULT_THEME_ID])

    def get_theme_options(self) -> list[tuple[str, str]]:
        return [(theme_id, theme.display_name) for theme_id, theme in THEMES.items()]

    def set_theme(self, theme_id: str, persist: bool = True) -> bool:
        if theme_id not in THEMES:
            logger.warning(f"Cannot select unknown theme: {theme_id}")
            return False

        self.active_theme_id = theme_id
        if persist:
            self.save()
        return True
