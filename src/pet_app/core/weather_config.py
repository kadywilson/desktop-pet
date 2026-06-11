from dataclasses import dataclass
from pathlib import Path

import yaml

from pet_app.utils.logger import logger
from pet_app.utils.paths import get_project_root


@dataclass
class WeatherConfig:
    enabled: bool = True
    location_mode: str = "manual"
    location_query: str = ""
    display_name: str = ""
    base_url: str = "https://wttr.in"
    backup_base_url: str = "https://wttr.is"
    format: str = "j1"
    timeout_seconds: int = 8
    cache_enabled: bool = True
    cache_ttl_minutes: int = 30
    cache_dir: str = "data/weather_cache"
    cache_cleanup_on_start: bool = True
    cache_max_age_hours: int = 6
    cache_max_files: int = 5
    units: str = "metric"
    show_feels_like: bool = True
    show_humidity: bool = True
    show_wind: bool = True
    show_precipitation: bool = True
    speak_if_voice_enabled: bool = True
    allow_system_location: bool = False
    allow_gps: bool = False
    allow_ip_location: bool = False
    allow_browser_location: bool = False
    fallback_message: str = "天气暂时查不到啦，可能是网络有点闹脾气。"


def load_weather_config() -> WeatherConfig:
    root = get_project_root()
    yaml_path = root / "config" / "weather.yaml"

    if not yaml_path.exists():
        logger.warning("config/weather.yaml not found, using defaults")
        return WeatherConfig()

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to parse config/weather.yaml: {e}, using defaults")
        return WeatherConfig()

    w = raw.get("weather", {}) or {}
    location = w.get("location", {}) or {}
    provider = w.get("provider", {}) or {}
    cache = w.get("cache", {}) or {}
    display = w.get("display", {}) or {}
    behavior = w.get("behavior", {}) or {}
    privacy = w.get("privacy", {}) or {}
    fallback = w.get("fallback", {}) or {}

    config = WeatherConfig(
        enabled=w.get("enabled", True),
        location_mode=location.get("mode", "manual"),
        location_query=location.get("query", ""),
        display_name=location.get("display_name", ""),
        base_url=provider.get("base_url", "https://wttr.in"),
        backup_base_url=provider.get("backup_base_url", "https://wttr.is"),
        format=provider.get("format", "j1"),
        timeout_seconds=provider.get("timeout_seconds", 8),
        cache_enabled=cache.get("enabled", True),
        cache_ttl_minutes=cache.get("ttl_minutes", 30),
        cache_dir=cache.get("dir", "data/weather_cache"),
        cache_cleanup_on_start=cache.get("cleanup_on_start", True),
        cache_max_age_hours=cache.get("max_age_hours", 6),
        cache_max_files=cache.get("max_files", 5),
        units=display.get("units", "metric"),
        show_feels_like=display.get("show_feels_like", True),
        show_humidity=display.get("show_humidity", True),
        show_wind=display.get("show_wind", True),
        show_precipitation=display.get("show_precipitation", True),
        speak_if_voice_enabled=behavior.get("speak_if_voice_enabled", True),
        allow_system_location=privacy.get("allow_system_location", False),
        allow_gps=privacy.get("allow_gps", False),
        allow_ip_location=privacy.get("allow_ip_location", False),
        allow_browser_location=privacy.get("allow_browser_location", False),
        fallback_message=fallback.get("message", "天气暂时查不到啦，可能是网络有点闹脾气。"),
    )

    if not config.location_query:
        logger.warning("weather.location.query is empty, weather feature will use fallback")

    return config
