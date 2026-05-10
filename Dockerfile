FROM python:3.14-slim AS builder

WORKDIR /app

# Install uv and resolve dependencies from lockfile
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy virtual environment created by uv
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY main.py pyproject.toml uv.lock /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
