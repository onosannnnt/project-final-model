# Project Final Model

A minimal FastAPI service with a health check endpoint.

## Requirements

- Python 3.14+
- [`uv`](https://github.com/astral-sh/uv)

## Setup

```/dev/null/README.md#L1-3
uv venv
uv sync
```

## Run the server

```/dev/null/README.md#L1-1
uv run python main.py
```

The API will be available at `http://localhost:8000`.

## Health check

```/dev/null/README.md#L1-1
curl http://localhost:8000/health
```

Expected response:

```/dev/null/README.md#L1-1
{"status":"ok"}
```

## Development server (optional)

If you prefer auto-reload during development:

```/dev/null/README.md#L1-1
uv run uvicorn main:app --reload
```
