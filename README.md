# DeskTop-Petties

## Shared Persona Core

This repository starts the B-student component of the desktop pet project: a
cloud-backed shared persona core for a desktop digital life form.

The first implementation focuses on a Python FastAPI backend that will later
connect to Supabase, an LLM provider, a simple web interaction page, and the
PyQt6 desktop pet built by student A.

## Step 1: FastAPI skeleton

Implemented in this step:

- FastAPI application entrypoint.
- Centralized environment configuration in `app/config.py`.
- Lightweight shared access-password helper.
- Placeholder database configuration checker.
- Pydantic schemas for health, chat, and world-state responses.
- Placeholder chat endpoint.
- Placeholder world-state endpoint.
- Minimal static landing page.

## Local setup

Use Python 3.10 or newer when possible. Python 3.11 is recommended for this
project.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Then open:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## If dependency installation fails

First confirm that you are installing into the project virtual environment:

```bash
python --version
python -m pip --version
```

Then upgrade pip and retry:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

If you are in a network environment where the default PyPI source is slow or
blocked, try a mirror:

```bash
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

If your Python version is too old, install Python 3.10+ and recreate the virtual
environment before running the install commands again.

## Current prototype endpoints

### `GET /health`

Returns service status and version metadata.

### `GET /api/world/state`

Returns the default shared world state. Later steps will load the same response
shape from Supabase.

### `POST /api/chat`

Returns a placeholder response after checking the shared access password.

Example request body:

```json
{
  "password": "persona-core",
  "message": "你好，世界之魂。"
}
```
