# API Routes Documentation

This document provides a comprehensive overview of all the API routes available in the application. It is structured to be easily parsable and understood by both developers and Large Language Models (LLMs).

The application is built with FastAPI and runs with the base URL typically set to `http://0.0.0.0:8000`.

---

## 1. Root & Health Check

Defined in `main.py`.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Returns a basic health check: `{"status": "ok"}`. |
| `GET` | `/ready` | Checks readiness of both the API and the Database connection. |

---

## 2. Users API (`/users`)

Defined in `routers_users.py`. Provides standard CRUD operations for `User` records.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/users` | Creates a new user. Expects a `UserCreate` payload. |
| `GET` | `/users` | Lists all users. |
| `GET` | `/users/{user_id}` | Retrieves a specific user by their ID. |
| `PUT` | `/users/{user_id}` | Updates a specific user. Expects a `UserUpdate` payload. |
| `DELETE`| `/users/{user_id}` | Deletes a specific user by their ID. |

---

## 3. Combat Logs API (`/combat-logs`)

Defined in `routers_combat_logs.py`. Manages raw game event data.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/combat-logs` | Creates a single raw combat log entry. |
| `POST` | `/combat-logs/batch`| Creates multiple combat logs at once. |
| `GET` | `/combat-logs` | Lists combat logs. Supports filtering via `?session_id=` and `?player_id=`. |
| `GET` | `/combat-logs/{id}` | Retrieves a specific combat log by its ID. |
| `PUT` | `/combat-logs/{id}` | Updates a specific combat log. |
| `DELETE`| `/combat-logs/{id}` | Deletes a specific combat log. |

---

## 4. Cleaned Combat Logs API (`/cleaned-combat-logs`)

Defined in `routers_cleaned_combat_logs.py`. Manages the processed/cleaned version of the combat logs used for ML feature extraction.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/cleaned-combat-logs/run` | Triggers the cleaning pipeline for a specific `session_id`. Reads raw logs, cleans them, and saves the cleaned versions. |
| `GET` | `/cleaned-combat-logs` | Lists cleaned combat logs. Supports filtering via `?session_id=` and `?player_id=`. |
| `GET` | `/cleaned-combat-logs/{id}`| Retrieves a specific cleaned combat log by its ID. |
| `DELETE`| `/cleaned-combat-logs/session/{session_id}` | Deletes all cleaned logs associated with a given `session_id`. |

---

## 5. Machine Learning API (`/ml`)

Defined in `routers_ml.py`. Manages everything from training to making real-time predictions.

### System & Pipeline
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/ml/ready` | Checks the status of the ML service and active model. |
| `POST` | `/ml/pipeline/clean` | Cleans raw logs for a given `session_id`. |
| `POST` | `/ml/pipeline/features` | Generates features for a given `session_id`. |
| `POST` | `/ml/pipeline/train` | Trains a new K-Means model for given `session_ids` and cluster count. |
| `POST` | `/ml/pipeline/run-all` | Runs the full pipeline: cleans data and trains a model in one step. |

### Model Management
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/ml/model/upload` | Uploads an externally trained model artifact (base64). |
| `GET` | `/ml/model/info` | Retrieves info on the currently active model. |
| `GET` | `/ml/model/versions`| Lists all registered model versions. |
| `POST` | `/ml/model/reload` | Forces the ML service to reload the active model into memory. |
| `POST` | `/ml/model/activate` | Sets a specified model version as the active model via payload. |
| `POST` | `/ml/model/activate/{model_version}` | Sets a specified model version as active via URL path. |

### Predictions
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/ml/predict` | Makes a prediction based on an incoming raw log payload. |
| `POST` | `/ml/predict-from-combat-log/{id}` | Looks up a saved combat log and runs a prediction on it. |
| `POST` | `/ml/predict/batch` | Makes predictions on a batch of combat log payloads. |
| `POST` | `/ml/predict-and-save` | Makes a prediction and saves the result to the database. |
| `GET` | `/ml/predictions` | Lists saved historical predictions (filterable by session/player). |
| `GET` | `/ml/predictions/{id}`| Retrieves a specific saved prediction by its ID. |

### Model Comparisons
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/ml/models/compare` | Compares multiple models to find the best performing one. |
| `GET` | `/ml/models/compare/latest` | Retrieves the results of the most recent comparison. |
| `GET` | `/ml/models/compare/{id}` | Retrieves a comparison result by ID. |
| `GET` | `/ml/models/compare/{id}/export` | Exports the comparison results. |

### Game Integration & Summary
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/ml/stage-complete` | **Main game integration point.** Receives end-of-stage combat logs, predicts playstyle, and updates the player's profile (tier and type). |
| `GET` | `/ml/project-summary` | Returns a statistical summary of the ML project/service. |
