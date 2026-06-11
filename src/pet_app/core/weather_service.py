import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from pet_app.core.weather_config import WeatherConfig, load_weather_config
from pet_app.utils.logger import logger
from pet_app.utils.paths import get_project_root


@dataclass
class WeatherSummary:
    location_display_name: str = ""
    date_label: str = "today"
    condition_text: str = ""
    current_temp_c: str = ""
    max_temp_c: str = ""
    min_temp_c: str = ""
    feels_like_c: str = ""
    humidity: str = ""
    wind_kmph: str = ""
    chance_of_rain: str = ""
    short_advice: str = ""


class WeatherService:

    def __init__(self, config: Optional[WeatherConfig] = None):
        self._config = config or load_weather_config()
        self._cache_dir = get_project_root() / self._config.cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        if self._config.cache_cleanup_on_start:
            self._cleanup_cache()

    def get_weather_text(self, day: str = "today") -> str:
        if not self._config.enabled:
            return self._config.fallback_message

        if not self._config.location_query:
            logger.warning("[Weather] location.query is empty, cannot request")
            return self._config.fallback_message

        try:
            data = self._get_weather_data()
            if data is None:
                return self._config.fallback_message
            summary = self._parse_summary(data, day)
            return self._format_bubble_text(summary)
        except Exception as e:
            logger.error(f"[Weather] Unexpected error: {e}")
            return self._config.fallback_message

    def get_weather_context_for_ai(self) -> Optional[str]:
        """Return a short weather summary string for AI prompt injection, or None if unavailable."""
        if not self._config.enabled or not self._config.location_query:
            return None
        try:
            data = self._get_weather_data()
            if data is None:
                return None
            today_summary = self._parse_summary(data, "today")
            tomorrow_summary = self._parse_summary(data, "tomorrow")
            parts = []
            if today_summary.condition_text:
                parts.append(
                    f"今天{today_summary.location_display_name}天气：{today_summary.condition_text}，"
                    f"气温{today_summary.current_temp_c or today_summary.max_temp_c}°C"
                )
                if today_summary.chance_of_rain and int(today_summary.chance_of_rain or "0") > 30:
                    parts[-1] += f"，降雨概率{today_summary.chance_of_rain}%"
            if tomorrow_summary.condition_text:
                parts.append(
                    f"明天：{tomorrow_summary.condition_text}，"
                    f"最高{tomorrow_summary.max_temp_c}°C，最低{tomorrow_summary.min_temp_c}°C"
                )
            return "；".join(parts) if parts else None
        except Exception as e:
            logger.debug(f"[Weather] Failed to get context for AI: {e}")
            return None

    def _get_weather_data(self) -> Optional[dict]:
        cached = self._read_cache()
        if cached is not None:
            return cached

        data = self._fetch_from_provider(self._config.base_url)
        if data is None and self._config.backup_base_url:
            logger.info("[Weather] Primary failed, trying backup URL")
            data = self._fetch_from_provider(self._config.backup_base_url)

        if data is not None:
            self._write_cache(data)
        return data

    def _fetch_from_provider(self, base_url: str) -> Optional[dict]:
        query = self._config.location_query.strip()
        if not query:
            logger.error("[Weather] Empty location query, refusing to call wttr.in")
            return None

        url = f"{base_url}/{query}?format={self._config.format}"
        logger.info(f"[Weather] Requesting: {url}")

        try:
            resp = requests.get(url, timeout=self._config.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            if "current_condition" not in data:
                logger.warning("[Weather] Response missing current_condition field")
                return None
            return data
        except requests.Timeout:
            logger.warning(f"[Weather] Request timed out: {url}")
        except requests.RequestException as e:
            logger.warning(f"[Weather] Request failed: {e}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[Weather] Failed to parse JSON response: {e}")
        return None

    def _parse_summary(self, data: dict, day: str = "today") -> WeatherSummary:
        summary = WeatherSummary(
            location_display_name=self._config.display_name or self._config.location_query,
            date_label=day,
        )

        if day == "today":
            cc_list = data.get("current_condition", [])
            if cc_list:
                cc = cc_list[0]
                summary.current_temp_c = cc.get("temp_C", "")
                summary.feels_like_c = cc.get("FeelsLikeC", "")
                summary.humidity = cc.get("humidity", "")
                summary.wind_kmph = cc.get("windspeedKmph", "")
                desc_list = cc.get("weatherDesc", [])
                if desc_list:
                    summary.condition_text = desc_list[0].get("value", "")

            weather_list = data.get("weather", [])
            if weather_list:
                today_weather = weather_list[0]
                summary.max_temp_c = today_weather.get("maxtempC", "")
                summary.min_temp_c = today_weather.get("mintempC", "")
                hourly = today_weather.get("hourly", [])
                if hourly:
                    rain_chances = [int(h.get("chanceofrain", "0") or "0") for h in hourly]
                    summary.chance_of_rain = str(max(rain_chances)) if rain_chances else ""

        elif day == "tomorrow":
            weather_list = data.get("weather", [])
            if len(weather_list) >= 2:
                tmr = weather_list[1]
                summary.max_temp_c = tmr.get("maxtempC", "")
                summary.min_temp_c = tmr.get("mintempC", "")
                hourly = tmr.get("hourly", [])
                if hourly:
                    rain_chances = [int(h.get("chanceofrain", "0") or "0") for h in hourly]
                    summary.chance_of_rain = str(max(rain_chances)) if rain_chances else ""
                    mid_hour = hourly[len(hourly) // 2]
                    desc_list = mid_hour.get("weatherDesc", [])
                    if desc_list:
                        summary.condition_text = desc_list[0].get("value", "")
                    summary.feels_like_c = mid_hour.get("FeelsLikeC", "")
                    summary.humidity = mid_hour.get("humidity", "")
                    summary.wind_kmph = mid_hour.get("windspeedKmph", "")

        summary.short_advice = self._generate_advice(summary)
        return summary

    def _generate_advice(self, s: WeatherSummary) -> str:
        rain = int(s.chance_of_rain) if s.chance_of_rain else 0
        temp = int(s.max_temp_c) if s.max_temp_c else (int(s.current_temp_c) if s.current_temp_c else None)
        wind = int(s.wind_kmph) if s.wind_kmph else 0
        condition = (s.condition_text or "").lower()

        if rain >= 60 or "rain" in condition or "thunder" in condition:
            return "记得带伞哦"
        if rain >= 30:
            return "可能会下雨，带把伞比较稳"
        if temp is not None and temp >= 35:
            return "太热了，记得喝水防晒"
        if temp is not None and temp >= 30:
            return "有点热，出门注意防晒"
        if temp is not None and temp <= 5:
            return "挺冷的，多穿点别冻着"
        if temp is not None and temp <= 10:
            return "有点凉，加件外套吧"
        if wind >= 40:
            return "风很大，出门小心"
        if wind >= 25:
            return "风有点大，注意一下"
        if "snow" in condition:
            return "下雪了，注意保暖和路滑"
        if "clear" in condition or "sunny" in condition:
            return "天气不错，适合出门走走"
        return ""

    def _format_bubble_text(self, s: WeatherSummary) -> str:
        name = s.location_display_name
        day_prefix = "今天" if s.date_label == "today" else "明天"

        parts = []
        if s.condition_text:
            cond_zh = self._translate_condition(s.condition_text)
            if s.date_label == "today" and s.current_temp_c:
                parts.append(f"{day_prefix}{name}{cond_zh}，约 {s.current_temp_c}°C")
            elif s.max_temp_c and s.min_temp_c:
                parts.append(f"{day_prefix}{name}{cond_zh}，{s.min_temp_c}~{s.max_temp_c}°C")
            else:
                parts.append(f"{day_prefix}{name}{cond_zh}")
        else:
            if s.current_temp_c:
                parts.append(f"{day_prefix}{name}约 {s.current_temp_c}°C")
            elif s.max_temp_c:
                parts.append(f"{day_prefix}{name}{s.min_temp_c}~{s.max_temp_c}°C")
            else:
                return self._config.fallback_message

        if s.short_advice:
            parts.append(s.short_advice)

        text = "，".join(parts) + "。"
        return text

    _CONDITION_MAP = {
        "sunny": "晴",
        "clear": "晴",
        "partly cloudy": "多云",
        "cloudy": "阴",
        "overcast": "阴",
        "mist": "薄雾",
        "fog": "雾",
        "light rain": "小雨",
        "moderate rain": "中雨",
        "heavy rain": "大雨",
        "patchy rain possible": "可能有零星小雨",
        "patchy rain nearby": "附近有零星小雨",
        "light drizzle": "毛毛雨",
        "thundery outbreaks possible": "可能有雷阵雨",
        "thunder": "雷雨",
        "light snow": "小雪",
        "moderate snow": "中雪",
        "heavy snow": "大雪",
        "blizzard": "暴风雪",
        "light rain shower": "阵雨",
        "moderate or heavy rain shower": "中到大阵雨",
    }

    def _translate_condition(self, condition: str) -> str:
        lower = condition.strip().lower()
        return self._CONDITION_MAP.get(lower, condition)

    def _cache_file_path(self) -> Path:
        return self._cache_dir / "current_weather.json"

    def _read_cache(self) -> Optional[dict]:
        if not self._config.cache_enabled:
            return None
        cache_file = self._cache_file_path()
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            ts = cached.get("_cached_at", 0)
            location = cached.get("_location", "")
            if location != self._config.location_query:
                logger.info("[Weather] Cache location mismatch, ignoring cache")
                return None
            age_minutes = (time.time() - ts) / 60
            if age_minutes > self._config.cache_ttl_minutes:
                logger.info(f"[Weather] Cache expired ({age_minutes:.0f} min old)")
                return None
            logger.info("[Weather] Using cached weather data")
            return cached.get("data")
        except Exception as e:
            logger.warning(f"[Weather] Failed to read cache: {e}")
            return None

    def _write_cache(self, data: dict):
        if not self._config.cache_enabled:
            return
        cache_file = self._cache_file_path()
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "_cached_at": time.time(),
                "_location": self._config.location_query,
                "data": data,
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info("[Weather] Cache written successfully")
        except Exception as e:
            logger.warning(f"[Weather] Failed to write cache: {e}")

    def _cleanup_cache(self):
        try:
            if not self._cache_dir.exists():
                return
            now = time.time()
            max_age_seconds = self._config.cache_max_age_hours * 3600
            files = sorted(self._cache_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
            removed = 0
            for f in files:
                age = now - f.stat().st_mtime
                if age > max_age_seconds:
                    f.unlink()
                    removed += 1
            if removed:
                logger.info(f"[Weather] Cleaned up {removed} old cache file(s)")
        except Exception as e:
            logger.warning(f"[Weather] Cache cleanup error: {e}")
