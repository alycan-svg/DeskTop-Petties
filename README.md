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

## Manual API tests

Keep `uvicorn app.main:app --reload` running in one terminal, then open a second
terminal for these checks.

### macOS, Linux, or Git Bash

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/world/state
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"password":"persona-core","message":"你好，世界之魂"}'
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"password":"wrong-password","message":"你好"}'
```

### Windows PowerShell

PowerShell treats `curl` as an alias for `Invoke-WebRequest`, so Linux-style
`curl -H ... -d ...` commands may fail. Use `Invoke-RestMethod` instead:

```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/world/state"

$chatBody = @{
  password = "persona-core"
  message = "你好，世界之魂"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/chat" `
  -ContentType "application/json; charset=utf-8" `
  -Body $chatBody

$wrongPasswordBody = @{
  password = "wrong-password"
  message = "你好"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/chat" `
  -ContentType "application/json; charset=utf-8" `
  -Body $wrongPasswordBody
```

The wrong-password request is expected to fail with `401 Unauthorized`; in
PowerShell, `Invoke-RestMethod` displays that HTTP error as a red exception.
That means the password gate is working.

If the Chinese reply appears garbled in PowerShell, set the console encoding to
UTF-8 before the request:

```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
```

If you prefer real curl in PowerShell, call `curl.exe` and keep the command on
one line. Quoting JSON inline in PowerShell is easy to break, so writing a body
variable is safer:

```powershell
$chatJson = '{"password":"persona-core","message":"你好，世界之魂"}'
curl.exe -X POST "http://127.0.0.1:8000/api/chat" -H "Content-Type: application/json; charset=utf-8" --data-raw $chatJson
```


## Windows Chinese output troubleshooting

API responses explicitly declare `application/json; charset=utf-8`, but older
PowerShell terminals can still display Chinese text incorrectly. If that happens,
run these commands before testing the chat endpoint:

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
```

If the terminal still shows garbled characters, open the same endpoint in the
browser or use FastAPI's docs page at `http://127.0.0.1:8000/docs`; the backend
response is still valid UTF-8 JSON.


## Step 2: Supabase database schema

The cloud-memory schema lives in `sql/schema.sql`. Run it in the Supabase SQL
Editor after creating a Supabase project.

The schema creates these tables:

- `worlds`: the shared cloud soul identity.
- `world_state`: mood, color, animation, and personality values for the shared pet.
- `messages`: user, assistant, and system chat history.
- `memories`: long-term memory fragments extracted from conversations.
- `tasks`: reserved DDL/task records for later mood and stress evolution.
- `system_events`: structured audit events such as memory creation or mood changes.

It also creates indexes for recent chat lookup, important memory retrieval, task
filtering, and event history. The script seeds the first shared world with the id
`shared_world` and its default state.

## Step 3: Connect FastAPI to Supabase

The world-state endpoint now reads `world_state` from Supabase instead of
returning a hard-coded object. Complete these steps after running
`sql/schema.sql`:

1. Open the API settings for your Supabase project and copy the project URL and
   the **service role** key.
2. Open your local `.env` file and fill in these values:

   ```dotenv
   SUPABASE_URL="https://your-project.supabase.co"
   SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
   WORLD_ID="shared_world"
   ```

3. Keep `.env` private. The service-role key bypasses normal database access
   restrictions, so it must exist only on the FastAPI server—never in browser
   JavaScript or the future PyQt6 application.
4. Install the new dependency and restart FastAPI:

   ```powershell
   python -m pip install -r requirements.txt
   python run.py
   ```

   `run.py` can also be launched by its full path or through an IDE whose
   terminal is in another directory. Static files and `.env` are resolved from
   the repository root rather than from the terminal's current directory.

5. Visit `http://127.0.0.1:8000/api/world/state`. A successful response is the
   seeded `shared_world` row from Supabase. `POST /api/chat` also returns this
   same live state alongside its temporary reply.

If the Supabase variables are empty, the API deliberately returns HTTP `503`
instead of pretending that an in-memory value came from the cloud. Connection,
permission, and query failures return HTTP `502`. If the configured world exists
but has no `world_state` row, the backend inserts the default state automatically.

For automated service tests, install the development requirements and run:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Step 4: Persist conversation turns

`POST /api/chat` now writes each successful exchange to the Supabase `messages`
table. The user message and the temporary assistant reply are sent as one insert
request, in that order, and both rows use the configured `WORLD_ID`.

Test the endpoint from `http://127.0.0.1:8000/docs` with the configured access
password. After a successful `200` response, open Supabase Table Editor and
inspect `messages`. Each request should add exactly two rows:

1. `role = user`, containing the request's `message`.
2. `role = assistant`, containing the backend reply.

If persistence fails, the endpoint returns HTTP `502` instead of reporting a
successful chat that was never saved. The reply is still a placeholder in this
step; a later step will replace it with an LLM-generated response and retrieve
relevant long-term memories.

## Step 5: Read recent conversation history

`GET /api/chat/history` retrieves the newest messages for the configured shared
world. Supabase selects newest rows first so the database can apply the limit
efficiently; the service then reverses that small result so clients receive the
messages in natural, oldest-to-newest reading order.

The endpoint accepts:

- `limit`: optional query parameter from `1` to `100`, default `20`.
- `X-Access-Password`: required request header containing `ACCESS_PASSWORD`.

You can test it in `http://127.0.0.1:8000/docs`: first send several chat
requests, then open `GET /api/chat/history`, set `limit` and the password header,
and execute it. The returned `messages` should contain both user and assistant
rows in chronological order. The password is a header rather than a URL query
parameter so it is not copied into browser history or ordinary URL logs.

This endpoint is also the context boundary for the future LLM service. A later
step can request a small recent window without loading the shared world's entire
conversation archive into every model call.

## Step 6: Replaceable LLM service layer

Chat replies now pass through a provider-independent LLM layer. The layer builds
one chronological context containing:

1. A system prompt describing the shared desktop pet and its current world state.
2. Up to `LLM_HISTORY_LIMIT` recent cloud messages.
3. The user's current message.

The default `LLM_PROVIDER="mock"` makes no external network request. It produces
a deterministic Chinese response that shows how many previous messages were
included, making context behavior testable before choosing a paid model. A real
provider adapter can be added later without changing `/api/chat`, Supabase
persistence, the web client, or the future PyQt6 client.

Optional `.env` setting:

```dotenv
LLM_HISTORY_LIMIT=20
```

The value must be between `1` and `100`. With mock mode enabled, send another
`POST /api/chat` request. Its reply should begin with `（Mock 模式）`, mention
the current user message, and report the number of previous messages supplied as
context. The exact user and assistant texts are then persisted as before.

Setting an unsupported `LLM_PROVIDER` returns HTTP `503`; provider, context, or
generation failures return HTTP `502`. This prevents an unsaved fallback answer
from being mistaken for a successful model response.
