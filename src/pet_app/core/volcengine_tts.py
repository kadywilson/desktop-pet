import base64
import json
import uuid
from dataclasses import dataclass

import requests

from pet_app.utils.logger import logger
from pet_app.core.voice_config import VoiceConfig, EmotionEntry


@dataclass
class TTSResult:
    success: bool
    audio_data: bytes = b""
    text_words: int = 0
    error_code: int = 0
    error_message: str = ""
    logid: str = ""


class VolcengineTTSClient:

    def __init__(self, config: VoiceConfig):
        self._config = config
        self._session = requests.Session()

    def synthesize(self, text: str, emotion: str = "default") -> TTSResult:
        if not self._config.api_key:
            logger.error("TTS API key not configured")
            return TTSResult(
                success=False,
                error_message="VOLCENGINE_TTS_API_KEY not set",
            )

        speaker = self._config.active_speaker_option()
        if speaker.api_version == "v1":
            return self._synthesize_v1(text, speaker)
        return self._synthesize_v3(text, emotion, speaker)

    def _synthesize_v3(self, text: str, emotion: str, speaker) -> TTSResult:
        request_id = str(uuid.uuid4())
        headers = {
            "X-Api-Key": self._config.api_key,
            "X-Api-Resource-Id": speaker.resource_id or self._config.resource_id,
            "X-Api-Request-Id": request_id,
            "Content-Type": "application/json",
        }

        body = self._build_v3_request_body(text, emotion, speaker.id)

        logger.info(
            f"TTS v3 request: speaker={speaker.id}, emotion={emotion}, "
            f"text_len={len(text)}, request_id={request_id}"
        )

        try:
            resp = self._session.post(
                speaker.endpoint or self._config.endpoint,
                headers=headers,
                json=body,
                stream=True,
                timeout=30,
            )
        except requests.exceptions.Timeout:
            logger.error("TTS request timed out")
            return TTSResult(success=False, error_message="Request timed out")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"TTS connection error: {e}")
            return TTSResult(success=False, error_message=f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS request failed: {e}")
            return TTSResult(success=False, error_message=str(e))

        logid = resp.headers.get("X-Tt-Logid", "")
        if logid:
            logger.info(f"TTS server logid: {logid}")

        if resp.status_code != 200:
            msg = f"TTS HTTP {resp.status_code}"
            logger.error(msg)
            return TTSResult(success=False, error_message=msg, logid=logid)

        return self._parse_stream_response(resp, logid)

    def _synthesize_v1(self, text: str, speaker) -> TTSResult:
        request_id = str(uuid.uuid4())
        headers = {
            "x-api-key": self._config.api_key,
            "Content-Type": "application/json",
        }
        body = self._build_v1_request_body(text, speaker.id, request_id, speaker.cluster)

        logger.info(
            f"TTS v1 request: speaker={speaker.id}, cluster={speaker.cluster}, "
            f"text_len={len(text)}, request_id={request_id}"
        )

        try:
            resp = self._session.post(
                speaker.endpoint or "https://openspeech.bytedance.com/api/v1/tts",
                headers=headers,
                json=body,
                timeout=30,
            )
        except requests.exceptions.Timeout:
            logger.error("TTS v1 request timed out")
            return TTSResult(success=False, error_message="Request timed out")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"TTS v1 connection error: {e}")
            return TTSResult(success=False, error_message=f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS v1 request failed: {e}")
            return TTSResult(success=False, error_message=str(e))

        logid = resp.headers.get("X-Tt-Logid", "") or resp.headers.get("x-tt-logid", "")
        if logid:
            logger.info(f"TTS v1 server logid: {logid}")

        if resp.status_code != 200:
            msg = f"TTS v1 HTTP {resp.status_code}"
            logger.error(msg)
            return TTSResult(success=False, error_message=msg, logid=logid)

        return self._parse_v1_response(resp, logid)

    def _build_v1_request_body(
        self, text: str, speaker_id: str, request_id: str, cluster: str
    ) -> dict:
        return {
            "app": {
                "cluster": cluster or "volcano_icl",
            },
            "user": {
                "uid": "desktop_pet",
            },
            "audio": {
                "voice_type": speaker_id,
                "encoding": self._config.audio_format,
                "speed_ratio": self._speech_rate_to_ratio(self._config.speech_rate),
            },
            "request": {
                "reqid": request_id,
                "text": text,
                "operation": "query",
            },
        }

    def _speech_rate_to_ratio(self, speech_rate: int) -> float:
        try:
            value = int(speech_rate)
        except (TypeError, ValueError):
            value = 0
        value = max(-100, min(100, value))
        return round(1.0 + value / 100.0, 2)

    def _build_v3_request_body(self, text: str, emotion: str, speaker_id: str) -> dict:
        emotion_entry = self._config.emotion_mapping.get(emotion)
        if emotion_entry is None:
            emotion_entry = self._config.emotion_mapping.get("default")

        audio_params: dict = {
            "format": self._config.audio_format,
            "sample_rate": self._config.sample_rate,
            "speech_rate": self._config.speech_rate,
            "loudness_rate": self._config.loudness_rate,
        }

        if self._config.use_emotion_param and emotion_entry:
            if emotion_entry.emotion:
                audio_params["emotion"] = emotion_entry.emotion
                audio_params["emotion_scale"] = emotion_entry.emotion_scale

        additions = {}
        if self._config.use_context_texts and emotion_entry:
            if emotion_entry.context_text:
                additions["context_texts"] = [emotion_entry.context_text]

        req_params: dict = {
            "text": text,
            "speaker": speaker_id,
            "audio_params": audio_params,
        }
        if additions:
            req_params["additions"] = json.dumps(additions, ensure_ascii=False)

        return {
            "user": {"uid": "desktop_pet"},
            "req_params": req_params,
        }

    def _parse_v1_response(self, resp: requests.Response, logid: str) -> TTSResult:
        try:
            payload = resp.json()
        except json.JSONDecodeError:
            logger.error("TTS v1: failed to parse JSON response")
            return TTSResult(success=False, error_message="Invalid JSON response", logid=logid)

        code = payload.get("code", 0)
        message = payload.get("message") or payload.get("msg") or ""
        if code not in (0, 3000, 20000000):
            logger.error(f"TTS v1 error: code={code}, message={message}")
            return TTSResult(
                success=False,
                error_code=code,
                error_message=message,
                logid=logid,
            )

        data_b64 = payload.get("data", "")
        if isinstance(data_b64, dict):
            data_b64 = data_b64.get("audio") or data_b64.get("data") or ""

        if not data_b64:
            logger.error("TTS v1: no audio data received")
            return TTSResult(
                success=False,
                error_code=code,
                error_message=message or "No audio data received",
                logid=logid,
            )

        try:
            audio_data = base64.b64decode(data_b64)
        except Exception as e:
            logger.error(f"TTS v1: failed to decode audio data: {e}")
            return TTSResult(success=False, error_message=str(e), logid=logid)

        logger.info(f"TTS v1 success: {len(audio_data)} bytes")
        return TTSResult(success=True, audio_data=audio_data, logid=logid)

    def _parse_stream_response(
        self, resp: requests.Response, logid: str
    ) -> TTSResult:
        audio_chunks: list[bytes] = []
        text_words = 0
        last_code = 0
        last_message = ""

        try:
            for line in resp.iter_lines():
                if not line:
                    continue

                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                try:
                    chunk = json.loads(line_str)
                except json.JSONDecodeError:
                    logger.warning(f"TTS: failed to parse JSON chunk")
                    continue

                code = chunk.get("code", 0)
                message = chunk.get("message", "")
                last_code = code
                last_message = message

                if code != 20000000 and code != 0:
                    logger.error(
                        f"TTS error: code={code}, message={message}"
                    )
                    return TTSResult(
                        success=False,
                        error_code=code,
                        error_message=message,
                        logid=logid,
                    )

                data_b64 = chunk.get("data", "")
                if data_b64:
                    audio_chunks.append(base64.b64decode(data_b64))

                usage = chunk.get("usage", {})
                if usage and "text_words" in usage:
                    text_words = usage["text_words"]

        except Exception as e:
            logger.error(f"TTS stream read error: {e}")
            return TTSResult(success=False, error_message=str(e), logid=logid)

        if not audio_chunks:
            logger.error("TTS: no audio data received")
            return TTSResult(
                success=False,
                error_code=last_code,
                error_message=last_message or "No audio data received",
                logid=logid,
            )

        audio_data = b"".join(audio_chunks)
        logger.info(
            f"TTS success: {len(audio_data)} bytes, "
            f"text_words={text_words}"
        )

        return TTSResult(
            success=True,
            audio_data=audio_data,
            text_words=text_words,
            logid=logid,
        )
