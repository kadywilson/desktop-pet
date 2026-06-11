# Smart Desktop Pet

A local-first Windows desktop pet built with Python and PySide6.

It supports a draggable always-on-top pet, speech bubbles, todo reminders,
short AI chat, optional TTS playback, manual-location weather, and local chat
memory.

## Features

- Transparent draggable desktop pet window
- Double-click poke response
- Click-to-hide speech bubble
- Emotion image switching
- Todo window with SQLite storage
- AI-assisted deadline reminders
- Tray menu and pet right-click menu
- Chat panel with local JSONL memory
- Archive chat memory
- Optional Volcengine/Doubao TTS
- Manual-location weather through wttr.in
- Optional diary-context bridge through a local JSON file

## Privacy

This app is designed for local personal use.

- No login
- No cloud sync
- No telemetry
- No automatic location detection
- No GPS, browser geolocation, system location, or IP geolocation
- Weather location is read only from `config/weather.yaml`
- Chat memory, todo data, logs, TTS cache, and weather cache stay local

Do not commit `.env`, real `config/*.yaml`, `data/`, or `logs/` contents.

## Requirements

- Windows 10 or newer
- Python 3.11
- Anaconda or Miniconda
- Dependencies from `requirements.txt`

## Setup

Create and activate the conda environment:

```powershell
conda create -n desktop-pet python=3.11
conda activate desktop-pet
pip install -r requirements.txt
```

Copy local configuration templates:

```powershell
Copy-Item .env.example .env
Copy-Item config/persona.example.yaml config/persona.yaml
Copy-Item config/chat.example.yaml config/chat.yaml
Copy-Item config/voice.example.yaml config/voice.yaml
Copy-Item config/weather.example.yaml config/weather.yaml
Copy-Item config/theme.example.yaml config/theme.yaml
```

Edit the copied files for your machine. Keep `.env` and `config/*.yaml` local.
Only the `.example.yaml` files are meant to be committed.

## API Configuration

Chat AI uses an OpenAI-compatible provider configured through `.env`:

```text
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=your_openai_compatible_model_here
```

TTS is optional:

```text
VOLCENGINE_TTS_API_KEY=your_volcengine_tts_api_key_here
VOLCENGINE_TTS_RESOURCE_ID=your_volcengine_resource_id_here
VOLCENGINE_TTS_VOICE_TYPE=your_volcengine_voice_type_here
```

If API configuration is missing, the app should fall back gracefully where
possible.

## Weather Configuration

Weather uses wttr.in and does not require an API key.

Configure a manual location in `config/weather.yaml`:

```yaml
weather:
  location:
    mode: "manual"
    query: "London"
    display_name: "London"
```

Do not leave `query` empty, because empty wttr.in requests may infer location by
IP.

## Run

Daily silent launch:

```text
run_pet_silent.vbs
```

Debug launch:

```text
run_pet_debug.bat
```

Manual launch:

```powershell
conda activate desktop-pet
$env:PYTHONPATH = "src"
python -m pet_app.main
```

## TTS Preview

After filling `.env` and `config/voice.yaml`, generate local sample audio:

```powershell
conda activate desktop-pet
$env:PYTHONPATH = "src"
python scripts/preview_tts.py
```

Generated samples are written to `data/tts_samples/` and should not be
committed.

## Project Layout

```text
src/pet_app/
├─ main.py
├─ app.py
├─ config.py
├─ ui/
├─ core/
├─ models/
└─ utils/
```

- `ui/`: PySide6 windows, widgets, bubble, tray menu, todo window, chat panel
- `core/`: AI, todo, reminders, chat memory, TTS, weather, persona loading
- `models/`: data models
- `utils/`: paths, logging, time helpers
- `assets/`: character images, icons, theme assets
- `config/`: local config files and public example templates
- `data/`: local runtime data
- `logs/`: runtime logs

## Notes For Public Forks

Before publishing your fork, confirm that:

- `.env` is not present
- real `config/*.yaml` files are not staged
- `data/` contains only `.gitkeep` placeholders
- `logs/` contains only `.gitkeep`
- generated audio, cache files, databases, and vendor PDFs are not staged
- character and icon assets are yours or licensed for redistribution
