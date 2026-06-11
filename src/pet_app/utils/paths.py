import os
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    current = Path(__file__).resolve()
    src_path = current.parent.parent.parent
    return src_path.parent


def get_assets_dir():
    """Get the assets directory path."""
    return get_project_root() / "assets"


def get_characters_dir():
    """Get the characters directory path."""
    return get_assets_dir() / "characters"


def get_default_pet_dir():
    """Get the default pet character directory."""
    return get_characters_dir() / "default_pet"


def get_pet_image_path(expression="default"):
    """Get the path to a pet image for the given expression."""
    pet_dir = get_default_pet_dir()
    image_path = pet_dir / f"{expression}.png"
    return image_path


def get_default_pet_image():
    """Get the default pet image path. Returns None if not found."""
    path = get_pet_image_path("default")
    if path.exists():
        return path
    return None


def get_logs_dir():
    """Get the logs directory path."""
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_data_dir():
    """Get the data directory path."""
    data_dir = get_project_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_icons_dir():
    """Get the icons directory path."""
    return get_assets_dir() / "icons"


def get_app_icon_path_ico():
    """Get the app icon ICO file path. Returns None if not found."""
    path = get_icons_dir() / "tray.ico"
    if path.exists():
        return path
    return None


def get_app_icon_path_png():
    """Get the app icon PNG file path. Returns None if not found."""
    path = get_icons_dir() / "tray.png"
    if path.exists():
        return path
    return None


def get_weather_cache_dir():
    """Get the weather cache directory path."""
    cache_dir = get_data_dir() / "weather_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir
