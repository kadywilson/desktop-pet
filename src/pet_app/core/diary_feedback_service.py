import json
from dataclasses import dataclass
from pathlib import Path

from pet_app.utils.logger import logger
from pet_app.utils.paths import get_project_root


@dataclass
class DiaryContext:
    date: str
    title: str
    summary: str
    pet_context: str
    created_at: str

    @property
    def summary_length(self) -> int:
        return len(self.summary.strip())


class DiaryFeedbackService:
    """Read the user-approved diary context exported by diary_ai."""

    def __init__(self, feedback_file: Path | None = None):
        self._feedback_file = feedback_file or (
            get_project_root() / "data" / "diary_feedback" / "inbox" / "latest.json"
        )

    @property
    def feedback_file(self) -> Path:
        return self._feedback_file

    def load_latest(self) -> DiaryContext | None:
        if not self._feedback_file.exists():
            logger.info(f"[DiaryFeedback] No feedback file found: {self._feedback_file}")
            return None

        try:
            raw = json.loads(self._feedback_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            logger.warning(f"[DiaryFeedback] Invalid JSON: {e}")
            return None
        except OSError as e:
            logger.warning(f"[DiaryFeedback] Failed to read feedback file: {e}")
            return None

        if raw.get("source") != "diary_ai":
            logger.warning("[DiaryFeedback] Unknown feedback source")
            return None

        if raw.get("type") != "diary_context":
            logger.warning("[DiaryFeedback] Unsupported feedback type")
            return None

        summary = str(raw.get("summary") or "").strip()
        pet_context = str(raw.get("pet_context") or "").strip()
        if not summary or not pet_context:
            logger.warning("[DiaryFeedback] Diary context is incomplete")
            return None

        return DiaryContext(
            date=str(raw.get("date") or ""),
            title=str(raw.get("title") or "日记反馈"),
            summary=summary,
            pet_context=pet_context,
            created_at=str(raw.get("created_at") or ""),
        )

    def get_status_text(self) -> str:
        feedback = self.load_latest()
        if feedback is None:
            return "还没有保存给我的日记反馈哦。"

        date_part = f"{feedback.date} 的" if feedback.date else "最新的"
        return f"我读到{date_part}今日小纸条了。"
