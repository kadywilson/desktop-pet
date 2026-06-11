import hashlib
import time
from pathlib import Path

from pet_app.utils.logger import logger


class TTSCacheManager:

    def __init__(self, cache_dir: Path, enabled: bool,
                 max_age_days: int = 2, max_files: int = 300,
                 audio_format: str = "mp3"):
        self._cache_dir = cache_dir
        self._enabled = enabled
        self._max_age_days = max_age_days
        self._max_files = max_files
        self._audio_format = audio_format

        if self._enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def get_cache_path(self, text: str, emotion: str, speaker: str = "") -> Path | None:
        if not self._enabled:
            return None
        key = f"{speaker}:{emotion}:{text}"
        h = hashlib.md5(key.encode("utf-8")).hexdigest()[:16]
        return self._cache_dir / f"{h}.{self._audio_format}"

    def cleanup(self) -> dict:
        result = {"deleted_by_age": 0, "deleted_by_count": 0, "remaining": 0}

        if not self._enabled:
            return result

        if not self._cache_dir.exists():
            return result

        mp3_files = sorted(
            self._cache_dir.glob(f"*.{self._audio_format}"),
            key=lambda f: f.stat().st_mtime,
        )

        now = time.time()
        remaining = []

        if self._max_age_days > 0:
            cutoff = now - (self._max_age_days * 86400)
            for f in mp3_files:
                try:
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                        result["deleted_by_age"] += 1
                    else:
                        remaining.append(f)
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {f.name}: {e}")
                    remaining.append(f)
        else:
            remaining = list(mp3_files)

        if self._max_files > 0 and len(remaining) > self._max_files:
            to_delete = remaining[: len(remaining) - self._max_files]
            for f in to_delete:
                try:
                    f.unlink()
                    result["deleted_by_count"] += 1
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {f.name}: {e}")
            remaining = remaining[len(to_delete):]

        result["remaining"] = len(remaining)

        total_deleted = result["deleted_by_age"] + result["deleted_by_count"]
        if total_deleted > 0:
            logger.info(
                f"TTS cache cleanup: deleted {total_deleted} files "
                f"(age={result['deleted_by_age']}, count={result['deleted_by_count']}), "
                f"remaining={result['remaining']}"
            )
        else:
            logger.info(f"TTS cache cleanup: no files to delete, remaining={result['remaining']}")

        return result
