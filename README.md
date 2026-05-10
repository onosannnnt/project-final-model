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

For local (non-Docker) runs, copy env template:

```/dev/null/README.md#L1-1
cp .env.example .env
```

## Run the server

```/dev/null/README.md#L1-1
uv run python main.py
```

The API will be available at `http://localhost:8000`.

`.env` is loaded automatically by Python via `python-dotenv`.

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

## Docker Compose

1. Copy environment template:

```/dev/null/README.md#L1-1
cp .env.example .env
```

2. Start API + PostgreSQL:

```/dev/null/README.md#L1-1
docker compose up --build
```

The API will be available at `http://localhost:${API_PORT}`.
