"""
Volcengine / Doubao TTS preview script.

Generates sample audio files for each configured emotion.
Output: data/tts_samples/<emotion>_<timestamp>.mp3

Usage:
    conda activate desktop-pet
    cd <PROJECT_ROOT>
    $env:PYTHONPATH="src"
    python scripts/preview_tts.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from pet_app.core.voice_config import load_voice_config
from pet_app.core.volcengine_tts import VolcengineTTSClient


def _mask(value: str) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def main():
    config = load_voice_config()

    print("=" * 50)
    print("Volcengine TTS Preview")
    print("=" * 50)
    print(f"Provider:    {config.provider}")
    print(f"Endpoint:    {config.endpoint}")
    print(f"Resource ID: {_mask(config.resource_id)}")
    print(f"Speaker:     {_mask(config.speaker)}")
    print(f"Format:      {config.audio_format}")
    print(f"Sample Rate: {config.sample_rate}")
    print(f"Context Texts: {'enabled' if config.use_context_texts else 'disabled'}")
    print(f"Emotion Param: {'enabled' if config.use_emotion_param else 'disabled'}")
    print("=" * 50)

    if not config.api_key:
        print("\n[ERROR] VOLCENGINE_TTS_API_KEY not set in environment.")
        print("Please set it in .env or as an environment variable.")
        sys.exit(1)

    if not config.preview_sample_texts:
        print("\n[ERROR] No sample texts configured in voice.yaml")
        sys.exit(1)

    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / config.preview_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOutput dir:  {output_dir}")
    print(f"Samples:     {len(config.preview_sample_texts)} emotions")
    print()

    client = VolcengineTTSClient(config)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = []

    for emotion, text in config.preview_sample_texts.items():
        print(f"[{emotion}] Synthesizing: {text}")

        result = client.synthesize(text, emotion)

        if result.success:
            filename = f"{emotion}_{timestamp}.{config.audio_format}"
            filepath = output_dir / filename
            filepath.write_bytes(result.audio_data)

            print(f"  -> OK: {filepath}")
            if result.text_words:
                print(f"     text_words: {result.text_words}")
            results.append((emotion, True, str(filepath)))
        else:
            print(f"  -> FAILED: {result.error_message}")
            if result.error_code:
                print(f"     code: {result.error_code}")
            if result.logid:
                print(f"     logid: {result.logid}")
            results.append((emotion, False, result.error_message))

        print()

    print("=" * 50)
    print("Summary")
    print("=" * 50)

    success_count = sum(1 for _, ok, _ in results if ok)
    fail_count = len(results) - success_count

    for emotion, ok, info in results:
        status = "OK" if ok else "FAILED"
        print(f"  [{status}] {emotion}: {info}")

    print()
    print(f"Total: {len(results)}, Success: {success_count}, Failed: {fail_count}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
