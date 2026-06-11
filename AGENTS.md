# Smart Desktop Pet - Agent Instructions

This repository is a local-first Windows desktop pet app written in Python.

## Project Scope

- Python 3.11
- PySide6 desktop UI
- Local SQLite todo storage
- Local JSONL chat memory
- Optional OpenAI-compatible chat API
- Optional Volcengine/Doubao TTS
- Manual-location weather through wttr.in

Do not add login, cloud sync, a web server, telemetry, deployment workflows, or
automatic location detection unless the maintainer explicitly asks for them.

## Repository Layout

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

- `main.py`: application entry point.
- `app.py`: main application controller.
- `ui/`: PySide6 windows, widgets, bubble, tray menu, todo window, chat panel.
- `core/`: business logic such as AI, todo, reminders, chat memory, TTS, weather.
- `models/`: data models.
- `utils/`: paths, logging, time helpers.
- `assets/`: character images, manifests, icons, theme assets.
- `config/`: local YAML config files and public `.example.yaml` templates.
- `data/`: local runtime data. Do not commit real contents.
- `logs/`: runtime logs. Do not commit logs.

## Privacy And Secrets

- Never commit `.env`.
- Never hard-code API keys.
- Never print or log real API keys.
- Keep real `config/*.yaml` local.
- Commit only `config/*.example.yaml` templates.
- Do not commit chat memory, diary bridge data, SQLite databases, generated TTS
  audio, weather cache, or logs.

Weather must stay manual-location only:

- Do not use system location.
- Do not use GPS.
- Do not use browser geolocation.
- Do not use IP geolocation.
- Do not call wttr.in with an empty location.

## Development Guidelines

- Keep changes small and readable.
- Keep UI code in `ui/` and business logic in `core/`.
- Prefer existing patterns over new abstractions.
- Add dependencies only when necessary.
- Keep the app runnable after each change.
- Use fallback behavior instead of crashing when optional API config is missing.

## Local Setup

```powershell
conda create -n desktop-pet python=3.11
conda activate desktop-pet
pip install -r requirements.txt
Copy-Item .env.example .env
Copy-Item config/persona.example.yaml config/persona.yaml
Copy-Item config/chat.example.yaml config/chat.yaml
Copy-Item config/voice.example.yaml config/voice.yaml
Copy-Item config/weather.example.yaml config/weather.yaml
Copy-Item config/theme.example.yaml config/theme.yaml
$env:PYTHONPATH = "src"
python -m pet_app.main
```

For daily local launch on Windows, use `run_pet_silent.vbs`. For debugging, use
`run_pet_debug.bat`.
