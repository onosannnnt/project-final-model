# Machine Learning API Routes Documentation

This document summarizes the functionality provided by the ML router (`routers_ml.py`) in the application. These endpoints are accessible under the `/ml` prefix.

## 1. System Status & Health
* **`GET /ml/ready`**
  Checks the API and database health, and returns the status along with the currently active model version.

## 2. Data Pipeline & Training
These endpoints manage the data preparation and model training workflows.
* **`POST /ml/pipeline/clean`**
  Cleans raw combat logs for a specific `session_id`.
* **`POST /ml/pipeline/features`**
  Cleans and prepares feature generation for a given `session_id`.
* **`POST /ml/pipeline/train`**
  Trains a new K-Means machine learning model using cleaned data from specified session IDs and a defined number of clusters.
* **`POST /ml/pipeline/run-all`**
  Executes the entire pipeline in one call: cleans the data for a given session and trains a new model.

## 3. Model Management
These endpoints handle storing, listing, activating, and reloading machine learning models.
* **`POST /ml/model/upload`**
  Registers an externally trained model by uploading its artifact base64 payload, version, and features.
* **`GET /ml/model/info`**
  Retrieves information about the currently active model.
* **`GET /ml/model/versions`**
  Lists all available registered model versions.
* **`POST /ml/model/reload`**
  Forces the system to reload the active model into memory (useful after model updates).
* **`POST /ml/model/activate`** & **`POST /ml/model/activate/{model_version}`**
  Sets a specific model version as the "active" model used for live predictions.

## 4. Predictions
These endpoints allow you to make predictions using the currently active model.
* **`POST /ml/predict`**
  Takes a raw combat log payload, builds its features, and returns a cluster/label prediction.
* **`POST /ml/predict-from-combat-log/{combat_log_id}`**
  Looks up an existing combat log in the database by its ID and makes a prediction on it.
* **`POST /ml/predict/batch`**
  Accepts a batch of combat logs and returns a list of predictions for each log.
* **`POST /ml/predict-and-save`**
  Makes a prediction from a payload and simultaneously saves the result to the database for historical tracking.
* **`GET /ml/predictions`**
  Lists saved predictions (optionally filterable by `session_id` or `player_id`).
* **`GET /ml/predictions/{prediction_id}`**
  Retrieves a specific saved prediction by its ID.

## 5. Model Comparison
Endpoints for evaluating and comparing different models.
* **`POST /ml/models/compare`**
  Compares multiple model versions against specific session data to determine a "winner" based on clustering metrics.
* **`GET /ml/models/compare/latest`**
  Retrieves the results of the most recent model comparison.
* **`GET /ml/models/compare/{comparison_id}`**
  Retrieves the results of a specific comparison by its ID.
* **`GET /ml/models/compare/{comparison_id}/export`**
  Exports the summary and winner data for a specific comparison.

## 6. Game Integration & Reporting
* **`POST /ml/stage-complete`**
  The main integration point for game progression. When a stage is complete, it accepts combat logs, saves them, runs a prediction to determine the player's playstyle cluster, maps that cluster to a user "type", and updates the user's tier/type in the database (e.g., upgrading tier if playstyle remains consistent, or resetting tier if playstyle changes).
* **`GET /ml/project-summary`**
  Provides a high-level statistical summary of the machine learning project and service state.
