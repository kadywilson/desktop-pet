# Security Policy

## Secrets

Do not commit real API keys, tokens, or provider credentials.

This project uses `.env` for local secrets. Keep `.env` private and use
`.env.example` only as a template.

## Local Data

Do not commit runtime data or generated files:

- `data/pet.db`
- `data/chat_memory/`
- `data/diary_feedback/`
- `data/tts_cache/`
- `data/tts_samples/`
- `data/weather_cache/`
- `logs/`

The repository keeps only `.gitkeep` placeholders for runtime directories.

## Weather Privacy

Weather lookup is manual-location only. Do not add system location, GPS,
browser geolocation, IP lookup, or empty-location wttr.in requests.

## Reporting

For a public fork, report security issues through the repository maintainer's
preferred private contact channel. Do not open public issues containing real
secrets, logs, chat memory, todo data, or personal diary context.
