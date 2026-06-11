# Smart Desktop Pet

Local-first Windows desktop pet app built with Python and PySide6.

[中文说明](README.zh-CN.md)

Smart Desktop Pet is a small local companion app that sits on your desktop. It supports a draggable transparent pet window, speech bubbles, todo reminders, short AI chat, optional TTS playback, manual-location weather, and an optional sanitized diary-context bridge.

The project is designed for private local use. Real API keys, local config files, chat memory, todo data, logs, TTS cache, weather cache, and diary bridge files should stay on your own machine.

## What It Does

* Shows a transparent always-on-top desktop pet.
* Lets you drag the pet around the desktop.
* Triggers a short AI poke response on double click.
* Shows replies in a speech bubble.
* Switches pet expressions such as `default`, `happy`, `annoyed`, and `upset`.
* Provides a local todo window backed by SQLite.
* Generates AI-assisted deadline reminders.
* Provides a short chat panel with local JSONL memory.
* Archives active chat memory into local archive files.
* Can optionally play bubble text through Volcengine/Doubao TTS.
* Can show weather from wttr.in using a manually configured location.
* Can optionally receive sanitized diary context from AI Diary Feedback.

## Related Project

Smart Desktop Pet can optionally integrate with AI Diary Feedback:

[https://github.com/kadywilson/ai_diary](https://github.com/kadywilson/ai_diary)

The diary project can export a user-approved local JSON bridge file containing sanitized context, such as a short summary or suggested tone. Smart Desktop Pet reads only that exported bridge file. It should not read raw diary folders, full diary entries, raw AI conversations, API keys, tokens, or private local paths.

You do not need AI Diary Feedback installed to run this desktop pet.

## Project Structure

```text
src/pet_app/
|-- main.py                  # Application entry point
|-- app.py                   # Main controller
|-- config.py                # Environment-based AI config
|-- ui/                      # PySide6 windows, widgets, bubble, tray menu
|-- core/                    # AI, todo, reminders, chat memory, TTS, weather
|-- models/                  # Data models
`-- utils/                   # Paths, logging, helpers

assets/                      # Pet images, icons, theme assets
config/                      # Local YAML configs and public example templates
data/                        # Local runtime data; only .gitkeep is committed
logs/                        # Local logs; only .gitkeep is committed
scripts/                     # Optional helper scripts
```

## Requirements

* Windows 10 or Windows 11
* Python 3.11
* Conda or another Python environment manager
* An OpenAI-compatible API key if you want real AI replies
* Optional Volcengine/Doubao TTS credentials if you want voice playback

Install dependencies:

```bat
conda create -n desktop-pet python=3.11
conda activate desktop-pet
python -m pip install -r requirements.txt
```

## Configuration

Copy the example files:

```bat
copy .env.example .env
copy config\persona.example.yaml config\persona.yaml
copy config\chat.example.yaml config\chat.yaml
copy config\voice.example.yaml config\voice.yaml
copy config\weather.example.yaml config\weather.yaml
copy config\theme.example.yaml config\theme.yaml
```

Then edit the copied local files with your own private values.

Important `.env` settings:

```env
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=your_openai_compatible_model_here

VOLCENGINE_TTS_API_KEY=your_volcengine_tts_api_key_here
VOLCENGINE_TTS_RESOURCE_ID=your_volcengine_resource_id_here
VOLCENGINE_TTS_VOICE_TYPE=your_volcengine_voice_type_here
```

Never commit `.env` or real `config/*.yaml` files.

## Weather

Weather uses wttr.in and does not require an API key.

Configure a manual location in `config/weather.yaml`:

```yaml
weather:
  location:
    mode: "manual"
    query: "London"
    display_name: "London"
```

Do not leave `query` empty. Empty wttr.in requests may infer location by IP, which is outside this project's privacy design.

## Optional Integration: AI Diary Feedback

If you use AI Diary Feedback, it can export a local bridge file for this app:

```text
data/diary_feedback/inbox/latest.json
```

The desktop pet menu item `Diary Feedback` reads that local bridge file and appends the sanitized context to the active local chat memory.

The bridge is intentionally narrow:

* It should not contain full diary entries.
* It should not contain raw AI conversations.
* It should not contain API keys or tokens.
* It should not contain private local paths.
* It should not upload anything.

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

```bat
conda activate desktop-pet
set PYTHONPATH=src
python -m pet_app.main
```

PowerShell:

```powershell
conda activate desktop-pet
$env:PYTHONPATH = "src"
python -m pet_app.main
```

## Main Workflows

### Poke The Pet

Double-click the pet window. The app asks the configured AI provider for a short response and shows it in the speech bubble. If AI configuration is missing or fails, the app falls back gracefully.

### Chat

Open the chat panel from the tray menu or pet right-click menu. Chat memory is stored locally in JSONL format under `data/chat_memory/`.

### Todo And Reminders

Open the todo window from the menu, create todos, and set deadline times. The app can remind you before unfinished and unexpired todos.

### Weather

Use `Weather Today` or `Weather Tomorrow` from the menu. Weather is fetched in the background and shown in the speech bubble.

### Voice Playback

Turn voice on or off from the menu. When voice is off, the app should not call the TTS API.

### TTS Preview

After filling `.env` and `config/voice.yaml`, generate local sample audio:

```bat
conda activate desktop-pet
set PYTHONPATH=src
python scripts\preview_tts.py
```

Generated samples are written to `data/tts_samples/` and should not be committed.

## Privacy And Safety

This repository is meant to publish code, public assets, documentation, and example configuration only.

Do not commit:

* `.env`
* real `config/*.yaml`
* `data/pet.db`
* `data/chat_memory/`
* `data/diary_feedback/`
* `data/tts_cache/`
* `data/tts_samples/`
* `data/weather_cache/`
* logs
* generated audio
* API keys or tokens
* private local paths

See:

* `SECURITY.md`
* `AGENTS.md`

## License

MIT License. See `LICENSE`.
