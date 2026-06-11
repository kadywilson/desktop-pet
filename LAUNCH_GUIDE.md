# Desktop Pet Launch Guide

## Daily Launch

Double-click:

```text
run_pet_silent.vbs
```

This starts the app without a visible console window.

## Debug Launch

Double-click:

```text
run_pet_debug.bat
```

This keeps a console window open so you can see Python tracebacks and runtime
logs.

## Manual Launch

From the project root:

```powershell
conda activate desktop-pet
$env:PYTHONPATH = "src"
python -m pet_app.main
```

On `cmd.exe`:

```bat
conda activate desktop-pet
set PYTHONPATH=src
python -m pet_app.main
```

## Requirements

- Windows 10 or newer
- Anaconda or Miniconda
- Python 3.11
- Dependencies from `requirements.txt`

## Logs

Runtime logs are written under `logs/`. Logs are local runtime data and should
not be committed.
