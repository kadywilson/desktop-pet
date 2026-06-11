import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from pet_app.utils.logger import logger
from pet_app.utils.paths import get_project_root


_DEFAULTS = {
    "tts": {
        "enabled": True,
        "provider": "volcengine",
        "endpoint": "https://openspeech.bytedance.com/api/v3/tts/unidirectional",
        "resource_id": "seed-tts-2.0",
        "speaker": "zh_male_kailangdidi_uranus_bigtts",
    },
    "audio": {
        "format": "mp3",
        "sample_rate": 24000,
        "speech_rate": 0,
        "loudness_rate": 0,
    },
    "playback": {
        "muted": False,
        "auto_play": {
            "poke": True,
            "chat": True,
            "reminder": True,
        },
    },
    "emotion": {
        "use_context_texts": True,
        "use_emotion_param": False,
        "default_emotion_scale": 4,
        "mapping": {
            "default": {
                "context_text": "请用自然、亲近、像中文桌宠和熟人聊天的语气说话。",
                "emotion": "neutral",
                "emotion_scale": 3,
            },
            "happy": {
                "context_text": "请用开心、轻快、带一点撒娇感的语气说话。",
                "emotion": "happy",
                "emotion_scale": 4,
            },
            "annoyed": {
                "context_text": "请用轻微嗔怪、傲娇、但不要真的凶的语气说话。",
                "emotion": "annoyed",
                "emotion_scale": 3,
            },
            "upset": {
                "context_text": "请用低落、委屈、轻声安慰的语气说话。",
                "emotion": "comfort",
                "emotion_scale": 3,
            },
        },
    },
    "cache": {
        "enabled": True,
        "dir": "data/tts_cache",
        "max_age_days": 2,
        "max_files": 300,
        "cleanup_on_start": True,
    },
    "preview": {
        "output_dir": "data/tts_samples",
        "sample_texts": {
            "default": "你又来戳我啦？我在呢。",
            "happy": "哼哼，今天心情不错，被你戳一下也不是不行。",
            "annoyed": "不要一直戳我啦，我也是要面子的。",
            "upset": "这么晚还没睡？我有点担心你。",
        },
    },
}


@dataclass
class EmotionEntry:
    context_text: str
    emotion: str = ""
    emotion_scale: int = 3


@dataclass
class AutoPlayConfig:
    poke: bool = True
    chat: bool = True
    reminder: bool = True


@dataclass
class SpeakerOption:
    id: str
    name: str
    api_version: str = "v3"
    endpoint: str = ""
    resource_id: str = ""
    cluster: str = ""


@dataclass
class VoiceConfig:
    enabled: bool = True
    provider: str = "volcengine"
    endpoint: str = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
    resource_id: str = "seed-tts-2.0"
    speaker: str = "zh_male_kailangdidi_uranus_bigtts"
    speakers: list[SpeakerOption] = field(default_factory=list)

    audio_format: str = "mp3"
    sample_rate: int = 24000
    speech_rate: int = 0
    loudness_rate: int = 0

    use_context_texts: bool = True
    use_emotion_param: bool = False
    default_emotion_scale: int = 4
    emotion_mapping: dict[str, EmotionEntry] = field(default_factory=dict)

    muted: bool = False
    auto_play: AutoPlayConfig = field(default_factory=AutoPlayConfig)

    cache_enabled: bool = True
    cache_dir: str = "data/tts_cache"
    cache_max_age_days: int = 2
    cache_max_files: int = 300
    cache_cleanup_on_start: bool = True

    preview_output_dir: str = "data/tts_samples"
    preview_sample_texts: dict[str, str] = field(default_factory=dict)

    api_key: str = ""

    def active_speaker_option(self) -> SpeakerOption:
        for option in self.speakers:
            if option.id == self.speaker:
                return option
        return SpeakerOption(
            id=self.speaker,
            name="Current Voice",
            api_version="v3",
            endpoint=self.endpoint,
            resource_id=self.resource_id,
        )


def _deep_get(data: dict, *keys, default=None):
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key, default)
    return data


def _load_voice_yaml() -> tuple[dict, Path]:
    root = get_project_root()
    yaml_path = root / "config" / "voice.yaml"

    raw = {}
    if yaml_path.exists():
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to parse config/voice.yaml: {e}, using defaults")
    else:
        logger.warning("config/voice.yaml not found, using defaults")

    return raw, yaml_path


def _parse_speakers(tts: dict, current_speaker: str) -> list[SpeakerOption]:
    raw_speakers = tts.get("speakers", [])
    speakers: list[SpeakerOption] = []
    seen: set[str] = set()

    if isinstance(raw_speakers, list):
        for entry in raw_speakers:
            if not isinstance(entry, dict):
                continue
            speaker_id = str(entry.get("id", "")).strip()
            if not speaker_id or speaker_id in seen:
                continue
            name = str(entry.get("name") or speaker_id).strip()
            speakers.append(
                SpeakerOption(
                    id=speaker_id,
                    name=name,
                    api_version=str(entry.get("api_version") or "v3").strip().lower(),
                    endpoint=str(entry.get("endpoint") or "").strip(),
                    resource_id=str(entry.get("resource_id") or "").strip(),
                    cluster=str(entry.get("cluster") or "").strip(),
                )
            )
            seen.add(speaker_id)

    if current_speaker and current_speaker not in seen:
        speakers.insert(0, SpeakerOption(id=current_speaker, name="Current Voice"))

    return speakers


def save_current_speaker(speaker_id: str) -> bool:
    speaker_id = (speaker_id or "").strip()
    if not speaker_id:
        logger.warning("Refusing to save empty TTS speaker id")
        return False

    raw, yaml_path = _load_voice_yaml()
    if not isinstance(raw, dict):
        raw = {}
    tts = raw.setdefault("tts", {})
    if not isinstance(tts, dict):
        raw["tts"] = {}
        tts = raw["tts"]

    tts["speaker"] = speaker_id

    try:
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(raw, f, allow_unicode=True, sort_keys=False)
        logger.info(f"Saved TTS speaker selection: {speaker_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to save TTS speaker selection: {e}")
        return False


def load_voice_config() -> VoiceConfig:
    raw, _yaml_path = _load_voice_yaml()

    def get(section, key, default=None):
        val = _deep_get(raw, section, key)
        if val is None:
            val = _deep_get(_DEFAULTS, section, key, default=default)
        return val

    tts = raw.get("tts", {}) or {}
    audio = raw.get("audio", {}) or {}
    playback_cfg = raw.get("playback", {}) or {}
    emotion_cfg = raw.get("emotion", {}) or {}
    cache_cfg = raw.get("cache", {}) or {}
    preview_cfg = raw.get("preview", {}) or {}

    mapping_raw = emotion_cfg.get("mapping") or _DEFAULTS["emotion"]["mapping"]
    emotion_mapping = {}
    for name, entry in mapping_raw.items():
        if isinstance(entry, dict):
            emotion_mapping[name] = EmotionEntry(
                context_text=entry.get("context_text", ""),
                emotion=entry.get("emotion", ""),
                emotion_scale=entry.get("emotion_scale", 3),
            )

    api_key = os.getenv("VOLCENGINE_TTS_API_KEY", "")
    resource_id = (
        os.getenv("VOLCENGINE_TTS_RESOURCE_ID")
        or tts.get("resource_id")
        or _DEFAULTS["tts"]["resource_id"]
    )
    speaker = (
        tts.get("speaker")
        or os.getenv("VOLCENGINE_TTS_VOICE_TYPE")
        or _DEFAULTS["tts"]["speaker"]
    )
    speakers = _parse_speakers(tts, speaker)

    auto_play_raw = playback_cfg.get("auto_play", {}) or {}
    auto_play_defaults = _DEFAULTS["playback"]["auto_play"]
    auto_play = AutoPlayConfig(
        poke=auto_play_raw.get("poke", auto_play_defaults["poke"]),
        chat=auto_play_raw.get("chat", auto_play_defaults["chat"]),
        reminder=auto_play_raw.get("reminder", auto_play_defaults["reminder"]),
    )

    config = VoiceConfig(
        enabled=tts.get("enabled", _DEFAULTS["tts"]["enabled"]),
        provider=tts.get("provider", _DEFAULTS["tts"]["provider"]),
        endpoint=tts.get("endpoint", _DEFAULTS["tts"]["endpoint"]),
        resource_id=resource_id,
        speaker=speaker,
        speakers=speakers,
        audio_format=audio.get("format", _DEFAULTS["audio"]["format"]),
        sample_rate=audio.get("sample_rate", _DEFAULTS["audio"]["sample_rate"]),
        speech_rate=audio.get("speech_rate", _DEFAULTS["audio"]["speech_rate"]),
        loudness_rate=audio.get("loudness_rate", _DEFAULTS["audio"]["loudness_rate"]),
        use_context_texts=emotion_cfg.get(
            "use_context_texts", _DEFAULTS["emotion"]["use_context_texts"]
        ),
        use_emotion_param=emotion_cfg.get(
            "use_emotion_param", _DEFAULTS["emotion"]["use_emotion_param"]
        ),
        default_emotion_scale=emotion_cfg.get(
            "default_emotion_scale", _DEFAULTS["emotion"]["default_emotion_scale"]
        ),
        emotion_mapping=emotion_mapping,
        muted=playback_cfg.get("muted", _DEFAULTS["playback"]["muted"]),
        auto_play=auto_play,
        cache_enabled=cache_cfg.get("enabled", _DEFAULTS["cache"]["enabled"]),
        cache_dir=cache_cfg.get("dir", _DEFAULTS["cache"]["dir"]),
        cache_max_age_days=cache_cfg.get("max_age_days", _DEFAULTS["cache"]["max_age_days"]),
        cache_max_files=cache_cfg.get("max_files", _DEFAULTS["cache"]["max_files"]),
        cache_cleanup_on_start=cache_cfg.get("cleanup_on_start", _DEFAULTS["cache"]["cleanup_on_start"]),
        preview_output_dir=preview_cfg.get(
            "output_dir", _DEFAULTS["preview"]["output_dir"]
        ),
        preview_sample_texts=preview_cfg.get(
            "sample_texts", _DEFAULTS["preview"]["sample_texts"]
        ),
        api_key=api_key,
    )

    if not config.api_key:
        logger.warning("VOLCENGINE_TTS_API_KEY not set in environment")

    return config
