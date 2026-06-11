import json
from pathlib import Path
from pet_app.models.character import CharacterConfig
from pet_app.utils.paths import get_default_pet_dir
from pet_app.utils.logger import logger


class CharacterLoader:
    """Load and manage character configuration."""

    def __init__(self, character_dir: Path = None):
        """Initialize character loader."""
        if character_dir is None:
            character_dir = get_default_pet_dir()
        
        self.character_dir = character_dir
        self.config = None
        self.load_manifest()

    def load_manifest(self) -> CharacterConfig:
        """Load character manifest from JSON file."""
        manifest_path = self.character_dir / "manifest.json"
        
        if not manifest_path.exists():
            logger.warning(f"Manifest not found at {manifest_path}, using defaults")
            self.config = CharacterConfig({})
            return self.config
        
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.config = CharacterConfig(data)
            logger.info(f"Loaded character: {self.config.name}")
            return self.config
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            self.config = CharacterConfig({})
            return self.config

    def get_config(self) -> CharacterConfig:
        """Get the loaded configuration."""
        return self.config

    def get_expression_image_path(self, expression: str) -> Path:
        """Get the full path to an expression image."""
        if not self.config:
            return None
        
        filename = self.config.get_expression_path(expression)
        if not filename:
            logger.warning(f"Expression '{expression}' not found in config")
            filename = self.config.get_expression_path(self.config.default_expression)
        
        return self.character_dir / filename if filename else None

    def get_expression_image_or_default(self, expression: str) -> Path:
        """Get expression image path, falling back to default if not found."""
        path = self.get_expression_image_path(expression)
        
        if path and path.exists():
            logger.info(f"Using expression image: {path}")
            return path
        
        logger.warning(f"Expression image not found: {path}, trying default")
        default_path = self.get_expression_image_path(self.config.default_expression)
        
        if default_path and default_path.exists():
            logger.info(f"Falling back to default image: {default_path}")
            return default_path
        
        logger.warning("Default expression image also not found")
        return None
