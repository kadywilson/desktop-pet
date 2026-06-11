import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from pet_app.core.voice_config import VoiceConfig, load_voice_config, save_current_speaker
from pet_app.core.volcengine_tts import VolcengineTTSClient
from pet_app.core.tts_cache import TTSCacheManager
from pet_app.utils.logger import logger
from pet_app.utils.paths import get_project_root


class _SynthesisWorker(QRunnable):

    def __init__(self, client: VolcengineTTSClient, text: str, emotion: str,
                 cache_path: Path | None, callback):
        super().__init__()
        self._client = client
        self._text = text
        self._emotion = emotion
        self._cache_path = cache_path
        self._callback = callback

    def run(self):
        try:
            result = self._client.synthesize(self._text, self._emotion)
            if result.success and result.audio_data:
                if self._cache_path:
                    self._cache_path.parent.mkdir(parents=True, exist_ok=True)
                    self._cache_path.write_bytes(result.audio_data)
                    self._callback(str(self._cache_path))
                else:
                    tmp = tempfile.NamedTemporaryFile(
                        suffix=".mp3", delete=False, dir=str(get_project_root() / "data" / "tts_cache")
                    )
                    tmp.write(result.audio_data)
                    tmp.close()
                    self._callback(tmp.name)
            else:
                logger.warning(f"TTS synthesis failed: {result.error_message}")
        except Exception as e:
            logger.error(f"TTS worker error: {e}")


class TTSPlayer(QObject):
    """Async TTS synthesis and playback service."""

    _play_file = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config: VoiceConfig = load_voice_config()
        self._client: VolcengineTTSClient | None = None
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(2)

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(1.0)

        self._play_file.connect(self._do_play)

        self._muted = self._config.muted

        # Initialize cache manager
        cache_dir = get_project_root() / self._config.cache_dir
        self._cache = TTSCacheManager(
            cache_dir=cache_dir,
            enabled=self._config.cache_enabled,
            max_age_days=self._config.cache_max_age_days,
            max_files=self._config.cache_max_files,
            audio_format=self._config.audio_format,
        )

        # Run cache cleanup on start
        if self._config.cache_cleanup_on_start and self._config.cache_enabled:
            self._cache.cleanup()

        if self._config.enabled and self._config.api_key:
            self._client = VolcengineTTSClient(self._config)
            logger.info("TTSPlayer initialized (voice enabled)")
        else:
            if not self._config.enabled:
                logger.info("TTSPlayer: TTS disabled in config")
            elif not self._config.api_key:
                logger.warning("TTSPlayer: API key not set, TTS unavailable")

    @property
    def muted(self) -> bool:
        return self._muted

    def set_muted(self, muted: bool):
        self._muted = muted
        if muted:
            self._player.stop()
        logger.info(f"TTSPlayer muted={muted}")

    def toggle_mute(self) -> bool:
        self.set_muted(not self._muted)
        return self._muted

    def get_speaker_options(self) -> list[tuple[str, str]]:
        return [(speaker.id, speaker.name) for speaker in self._config.speakers]

    def current_speaker(self) -> str:
        return self._config.speaker

    def set_speaker(self, speaker_id: str, persist: bool = True) -> bool:
        speaker_id = (speaker_id or "").strip()
        if not speaker_id:
            logger.warning("Ignoring empty TTS speaker selection")
            return False

        if speaker_id == self._config.speaker:
            return True

        known_ids = {speaker.id for speaker in self._config.speakers}
        if known_ids and speaker_id not in known_ids:
            logger.warning(f"Ignoring unknown TTS speaker selection: {speaker_id}")
            return False

        self._player.stop()
        self._config.speaker = speaker_id
        if persist:
            save_current_speaker(speaker_id)
        logger.info(f"TTS speaker switched: {speaker_id}")
        return True

    def speak(self, text: str, emotion: str = "default", source: str = "poke"):
        if not text or not text.strip():
            return

        if not self._config.enabled or not self._client:
            return

        if self._muted:
            return

        if not self._should_auto_play(source):
            return

        self._player.stop()

        cache_path = self._get_cache_path(text, emotion)
        if cache_path and cache_path.exists():
            logger.info(f"TTS cache hit: {cache_path.name}")
            self._play_file.emit(str(cache_path))
            return

        worker = _SynthesisWorker(
            self._client, text, emotion, cache_path, self._on_synthesis_done
        )
        self._thread_pool.start(worker)

    def _should_auto_play(self, source: str) -> bool:
        ap = self._config.auto_play
        if source == "poke":
            return ap.poke
        elif source == "chat":
            return ap.chat
        elif source == "reminder":
            return ap.reminder
        return True

    def _get_cache_path(self, text: str, emotion: str) -> Path | None:
        return self._cache.get_cache_path(text, emotion, self._config.speaker)

    def _on_synthesis_done(self, file_path: str):
        self._play_file.emit(file_path)

    @Slot(str)
    def _do_play(self, file_path: str):
        if self._muted:
            return
        try:
            self._player.stop()
            self._player.setSource(QUrl.fromLocalFile(file_path))
            self._player.play()
            logger.info(f"TTS playing: {Path(file_path).name}")
        except Exception as e:
            logger.error(f"TTS playback error: {e}")

    def stop(self):
        self._player.stop()

    def cleanup(self):
        self._player.stop()
        self._thread_pool.waitForDone(3000)
