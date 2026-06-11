# Logging

The app writes runtime logs to:

```text
logs/pet_app.log
```

Logs are useful for local debugging, but they may contain local paths, API error
messages, weather locations, todo metadata, or other private context.

Do not commit log files. The repository keeps only:

```text
logs/.gitkeep
```

## Debugging

Use `run_pet_debug.bat` to start the app with a visible console window.

You can also inspect recent logs with PowerShell:

```powershell
Get-Content logs\pet_app.log -Tail 100
Get-Content logs\pet_app.log -Tail 0 -Wait
```
