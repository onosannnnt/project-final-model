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

## Cleaned combat logs pipeline

Run cleaning + feature extraction from `combat_logs` into `cleaned_combat_logs`:

```/dev/null/README.md#L1-4
curl -X POST http://localhost:8000/cleaned-combat-logs/run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

Use `{"session_id": null}` to process all sessions.

## API quick reference

Interactive docs:

```/dev/null/README.md#L1-1
http://localhost:8000/docs
```

### Core checks

```/dev/null/README.md#L1-2
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### Combat logs

Create one:

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/combat-logs \
  -H "Content-Type: application/json" \
  -d '{"session_id":"550e8400-e29b-41d4-a716-446655440000","player_id":10,"character_id":1,"wave_number":1,"turn_index":1,"skill_id":101,"skill_target_id":2,"target_max_hp":1000,"target_current_hp":800,"damage_dealt":120,"damage_recieve":30,"caster_current_sp":5,"caster_current_hp":900,"caster_max_hp":1000,"current_frenzy_stack":2,"heal_amount":0,"current_corrupt_blood_gain":1,"corrupt_blood_by_max_hp":5,"weather":"sunny","momentum_gain":2,"momentum_used":1}'
```

Create batch:

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/combat-logs/batch \
  -H "Content-Type: application/json" \
  -d '{"items":[{"session_id":"550e8400-e29b-41d4-a716-446655440000","player_id":10,"character_id":1,"wave_number":1,"turn_index":1,"skill_id":101,"skill_target_id":2,"target_max_hp":1000,"target_current_hp":800,"damage_dealt":120,"damage_recieve":30,"caster_current_sp":5,"caster_current_hp":900,"caster_max_hp":1000,"current_frenzy_stack":2,"heal_amount":0,"current_corrupt_blood_gain":1,"corrupt_blood_by_max_hp":5,"weather":"sunny","momentum_gain":2,"momentum_used":1}]}'
```

### Clean pipeline

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/pipeline/clean \
  -H "Content-Type: application/json" \
  -d '{"session_id":"550e8400-e29b-41d4-a716-446655440000"}'
```

Train model:

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/pipeline/train \
  -H "Content-Type: application/json" \
  -d '{"version":"kmeans_v1","n_clusters":3,"session_ids":["550e8400-e29b-41d4-a716-446655440000"]}'
```

Run all (clean + train):

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/pipeline/run-all \
  -H "Content-Type: application/json" \
  -d '{"clean_session_id":"550e8400-e29b-41d4-a716-446655440000","version":"kmeans_v1","n_clusters":3,"train_session_ids":["550e8400-e29b-41d4-a716-446655440000"]}'
```

### Model lifecycle

Activate model:

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/model/activate \
  -H "Content-Type: application/json" \
  -d '{"version":"kmeans_v1"}'
```

Model info and versions:

```/dev/null/README.md#L1-2
curl http://localhost:8000/ml/model/info
curl http://localhost:8000/ml/model/versions
```

Reload active model artifact:

```/dev/null/README.md#L1-1
curl -X POST http://localhost:8000/ml/model/reload
```

Upload a model (base64 `.pkl` string):

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/model/upload \
  -H "Content-Type: application/json" \
  -d '{"version":"kmeans_uploaded","algorithm":"kmeans","artifact_base64":"<BASE64_PKL>","feature_columns":["damage_dealt","avg_damage"]}'
```

### Prediction

Predict from payload:

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"combat_log":{"session_id":"550e8400-e29b-41d4-a716-446655440000","player_id":10,"character_id":1,"wave_number":1,"turn_index":1,"skill_id":101,"skill_target_id":2,"target_max_hp":1000,"target_current_hp":800,"damage_dealt":120,"damage_recieve":30,"caster_current_sp":5,"caster_current_hp":900,"caster_max_hp":1000,"current_frenzy_stack":2,"heal_amount":0,"current_corrupt_blood_gain":1,"corrupt_blood_by_max_hp":5,"weather":"sunny","momentum_gain":2,"momentum_used":1}}'
```

Predict from stored combat log:

```/dev/null/README.md#L1-1
curl -X POST http://localhost:8000/ml/predict-from-combat-log/1
```

Predict batch:

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"items":[{"session_id":"550e8400-e29b-41d4-a716-446655440000","player_id":10,"character_id":1,"wave_number":1,"turn_index":1,"skill_id":101,"skill_target_id":2,"target_max_hp":1000,"target_current_hp":800,"damage_dealt":120,"damage_recieve":30,"caster_current_sp":5,"caster_current_hp":900,"caster_max_hp":1000,"current_frenzy_stack":2,"heal_amount":0,"current_corrupt_blood_gain":1,"corrupt_blood_by_max_hp":5,"weather":"sunny","momentum_gain":2,"momentum_used":1}]}'
```

Predict and save:

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/predict-and-save \
  -H "Content-Type: application/json" \
  -d '{"combat_log":{"session_id":"550e8400-e29b-41d4-a716-446655440000","player_id":10,"character_id":1,"wave_number":1,"turn_index":1,"skill_id":101,"skill_target_id":2,"target_max_hp":1000,"target_current_hp":800,"damage_dealt":120,"damage_recieve":30,"caster_current_sp":5,"caster_current_hp":900,"caster_max_hp":1000,"current_frenzy_stack":2,"heal_amount":0,"current_corrupt_blood_gain":1,"corrupt_blood_by_max_hp":5,"weather":"sunny","momentum_gain":2,"momentum_used":1}}'
```

Prediction queries:

```/dev/null/README.md#L1-3
curl http://localhost:8000/ml/predictions
curl http://localhost:8000/ml/predictions?session_id=550e8400-e29b-41d4-a716-446655440000&player_id=10
curl http://localhost:8000/ml/predictions/1
```

### Model comparison + summary

Compare:

```/dev/null/README.md#L1-3
curl -X POST http://localhost:8000/ml/models/compare \
  -H "Content-Type: application/json" \
  -d '{"model_versions":["kmeans_v1","kmeans_v2"],"session_ids":["550e8400-e29b-41d4-a716-446655440000"]}'
```

Read comparison results:

```/dev/null/README.md#L1-3
curl http://localhost:8000/ml/models/compare/latest
curl http://localhost:8000/ml/models/compare/1
curl http://localhost:8000/ml/models/compare/1/export
```

Project summary:

```/dev/null/README.md#L1-1
curl http://localhost:8000/ml/project-summary
```
