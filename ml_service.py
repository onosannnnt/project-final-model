from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cleaned import build_features
from models import (
    CleanedCombatLog,
    CombatLog,
    MLModelComparison,
    MLModelVersion,
    MLPrediction,
)

ARTIFACT_DIR = Path(__file__).resolve().parent / "models_artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


class ModelNotReadyError(RuntimeError):
    pass


def cluster_to_user_type(label: int) -> str:
    mapping = {0: "EL", 1: "RV", 2: "CE"}
    return mapping.get(label % 3, "EL")


def _to_feature_frame(rows: list[CleanedCombatLog]) -> pd.DataFrame:
    payloads = [row.cleaned_payload for row in rows]
    if not payloads:
        return pd.DataFrame()

    df = pd.DataFrame(payloads)
    for col in list(df.columns):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    numeric_df = df.select_dtypes(include=[np.number]).copy()
    if "session_id" in numeric_df.columns:
        numeric_df = numeric_df.drop(columns=["session_id"])

    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return numeric_df


def _artifact_path(version: str) -> Path:
    safe_version = version.replace("/", "_").replace(" ", "_")
    return ARTIFACT_DIR / f"{safe_version}.pkl"


def _combat_log_to_row(log: CombatLog) -> dict[str, Any]:
    return {
        "session_id": log.session_id,
        "player_id": log.player_id,
        "character_id": log.character_id,
        "wave_number": log.wave_number,
        "turn_index": log.turn_index,
        "skill_id": log.skill_id,
        "skill_target": log.skill_target_id,
        "target_max_hp": log.target_max_hp,
        "target_current_hp": log.target_current_hp,
        "damage_dealt": log.damage_dealt,
        "damage_recieve": log.damage_recieve,
        "caster_current_sp": log.caster_current_sp,
        "caster_current_hp": log.caster_current_hp,
        "caster_max_hp": log.caster_max_hp,
        "current_frenzy_stack": log.current_frenzy_stack,
        "heal_amount": log.heal_amount,
        "current_corrupt_blood_gain": log.current_corrupt_blood_gain,
        "corrupt_blood_by_max_hp": log.corrupt_blood_by_max_hp,
        "weather": log.weather.value,
        "momentum_gain": log.momentum_gain,
        "momentum_used": log.momentum_used,
        "break_count": 0,
        "break_damage": 0.0,
        "target_debuff_count": 0.0,
        "debuff_hit_ratio": 0.0,
    }


def build_feature_payload_from_combat_logs(
    log_rows: list[dict[str, Any]],
) -> dict[str, float]:
    raw_df = pd.DataFrame(log_rows)
    features_df = build_features(raw_df)
    if features_df.empty:
        return {}
    return dict(features_df.iloc[0].to_dict())


def build_feature_payload_from_combat_log(log: CombatLog) -> dict[str, float]:
    return build_feature_payload_from_combat_logs([_combat_log_to_row(log)])


def train_kmeans_from_cleaned(
    db: Session,
    version: str,
    n_clusters: int = 3,
    session_ids: list[UUID] | None = None,
) -> MLModelVersion:
    query = select(CleanedCombatLog)
    if session_ids:
        query = query.where(CleanedCombatLog.session_id.in_(session_ids))

    rows = list(db.scalars(query.order_by(CleanedCombatLog.id.asc())).all())
    feature_df = _to_feature_frame(rows)
    if feature_df.empty:
        raise ValueError("No cleaned features available to train model.")

    n_samples = len(feature_df)
    if n_samples < 2:
        raise ValueError("Need at least 2 cleaned rows to train clustering model.")

    clusters = max(2, min(n_clusters, n_samples))
    model = KMeans(n_clusters=clusters, random_state=42, n_init=10)
    labels = model.fit_predict(feature_df)

    metrics: dict[str, float | int] = {
        "n_samples": int(n_samples),
        "n_clusters": int(clusters),
        "inertia": float(model.inertia_),
    }
    if len(set(labels)) > 1 and n_samples > len(set(labels)):
        metrics["silhouette_score"] = float(silhouette_score(feature_df, labels))

    artifact = {
        "algorithm": "kmeans",
        "version": version,
        "feature_columns": feature_df.columns.tolist(),
        "model": model,
        "trained_at": datetime.utcnow().isoformat(),
    }
    artifact_path = _artifact_path(version)
    joblib.dump(artifact, artifact_path)

    existing = db.scalar(
        select(MLModelVersion).where(MLModelVersion.version == version)
    )
    if existing is None:
        existing = MLModelVersion(
            version=version,
            algorithm="kmeans",
            artifact_path=str(artifact_path),
            feature_columns=feature_df.columns.tolist(),
            metrics=metrics,
            is_active=False,
        )
        db.add(existing)
    else:
        existing.algorithm = "kmeans"
        existing.artifact_path = str(artifact_path)
        existing.feature_columns = feature_df.columns.tolist()
        existing.metrics = metrics

    db.commit()
    db.refresh(existing)
    return existing


def register_uploaded_model(
    db: Session,
    version: str,
    algorithm: str,
    artifact_base64: str,
    feature_columns: list[str],
    metrics: dict[str, Any] | None = None,
) -> MLModelVersion:
    artifact_path = _artifact_path(version)
    artifact_bytes = base64.b64decode(artifact_base64)
    artifact_path.write_bytes(artifact_bytes)

    existing = db.scalar(
        select(MLModelVersion).where(MLModelVersion.version == version)
    )
    if existing is None:
        existing = MLModelVersion(
            version=version,
            algorithm=algorithm,
            artifact_path=str(artifact_path),
            feature_columns=feature_columns,
            metrics=metrics,
            is_active=False,
        )
        db.add(existing)
    else:
        existing.algorithm = algorithm
        existing.artifact_path = str(artifact_path)
        existing.feature_columns = feature_columns
        existing.metrics = metrics

    db.commit()
    db.refresh(existing)
    return existing


def get_model_versions(db: Session) -> list[MLModelVersion]:
    return list(
        db.scalars(
            select(MLModelVersion).order_by(MLModelVersion.created_at.desc())
        ).all()
    )


def get_active_model_version(db: Session) -> MLModelVersion | None:
    return db.scalar(
        select(MLModelVersion)
        .where(MLModelVersion.is_active.is_(True))
        .order_by(MLModelVersion.created_at.desc())
    )


def set_active_model(db: Session, version: str) -> MLModelVersion:
    model_version = db.scalar(
        select(MLModelVersion).where(MLModelVersion.version == version)
    )
    if model_version is None:
        raise ValueError(f"Model version '{version}' not found.")

    all_versions = list(db.scalars(select(MLModelVersion)).all())
    for mv in all_versions:
        mv.is_active = mv.version == version

    db.commit()
    db.refresh(model_version)
    return model_version


def _load_artifact(model_version: MLModelVersion) -> dict[str, Any]:
    artifact_path = Path(model_version.artifact_path)
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    artifact = joblib.load(artifact_path)
    if not isinstance(artifact, dict) or "model" not in artifact:
        raise ValueError("Invalid model artifact format.")
    return artifact


def reload_active_model(db: Session) -> dict[str, Any]:
    active = get_active_model_version(db)
    if active is None:
        raise ModelNotReadyError("No active model configured.")
    artifact = _load_artifact(active)
    return {
        "version": active.version,
        "algorithm": active.algorithm,
        "feature_columns": artifact.get("feature_columns", active.feature_columns),
    }


def predict_with_active_model(
    db: Session, feature_payload: dict[str, Any]
) -> tuple[int, str]:
    active = get_active_model_version(db)
    if active is None:
        raise ModelNotReadyError("No active model configured.")

    artifact = _load_artifact(active)
    model = artifact["model"]
    feature_columns = artifact.get("feature_columns", active.feature_columns)

    row = {col: float(feature_payload.get(col, 0.0) or 0.0) for col in feature_columns}
    X = pd.DataFrame([row], columns=feature_columns)
    label = int(model.predict(X)[0])
    return label, active.version


def save_prediction(
    db: Session,
    model_version: str,
    source_type: str,
    input_payload: dict[str, Any],
    cluster_label: int,
    source_id: int | None = None,
    session_id: UUID | None = None,
    player_id: int | None = None,
) -> MLPrediction:
    pred = MLPrediction(
        model_version=model_version,
        source_type=source_type,
        source_id=source_id,
        session_id=session_id,
        player_id=player_id,
        input_payload=input_payload,
        cluster_label=cluster_label,
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred


def list_predictions(
    db: Session,
    session_id: UUID | None = None,
    player_id: int | None = None,
) -> list[MLPrediction]:
    stmt = select(MLPrediction)
    if session_id is not None:
        stmt = stmt.where(MLPrediction.session_id == session_id)
    if player_id is not None:
        stmt = stmt.where(MLPrediction.player_id == player_id)
    stmt = stmt.order_by(MLPrediction.created_at.desc())
    return list(db.scalars(stmt).all())


def get_prediction_by_id(db: Session, prediction_id: int) -> MLPrediction | None:
    return db.get(MLPrediction, prediction_id)


def compare_models(
    db: Session,
    versions: list[str],
    session_ids: list[UUID] | None = None,
) -> MLModelComparison:
    if not versions:
        raise ValueError("At least one model version is required.")

    query = select(CleanedCombatLog)
    if session_ids:
        query = query.where(CleanedCombatLog.session_id.in_(session_ids))
    rows = list(db.scalars(query).all())
    feature_df = _to_feature_frame(rows)
    if feature_df.empty:
        raise ValueError("No cleaned features available for comparison.")

    per_model: list[dict[str, Any]] = []
    best_version: str | None = None
    best_score = float("-inf")

    for version in versions:
        model_version = db.scalar(
            select(MLModelVersion).where(MLModelVersion.version == version)
        )
        if model_version is None:
            continue
        artifact = _load_artifact(model_version)
        model = artifact["model"]
        cols = artifact.get("feature_columns", model_version.feature_columns)

        aligned = pd.DataFrame()
        for col in cols:
            aligned[col] = pd.to_numeric(
                feature_df.get(col, 0.0), errors="coerce"
            ).fillna(0.0)

        labels = model.predict(aligned)
        metrics: dict[str, Any] = {
            "version": version,
            "n_samples": int(len(aligned)),
            "unique_clusters": int(len(set(labels))),
        }
        if hasattr(model, "inertia_"):
            metrics["inertia"] = float(model.inertia_)

        score = -9999.0
        if len(set(labels)) > 1 and len(aligned) > len(set(labels)):
            sil = float(silhouette_score(aligned, labels))
            metrics["silhouette_score"] = sil
            score = sil

        per_model.append(metrics)
        if score > best_score:
            best_score = score
            best_version = version

    summary = {
        "evaluated_at": datetime.utcnow().isoformat(),
        "dataset_rows": int(len(feature_df)),
        "results": per_model,
        "winner_version": best_version,
    }

    record = MLModelComparison(
        compared_versions=versions,
        winner_version=best_version,
        summary=summary,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_latest_comparison(db: Session) -> MLModelComparison | None:
    return db.scalar(
        select(MLModelComparison).order_by(MLModelComparison.created_at.desc())
    )


def get_comparison_by_id(db: Session, comparison_id: int) -> MLModelComparison | None:
    return db.get(MLModelComparison, comparison_id)


def get_project_summary(db: Session) -> dict[str, Any]:
    combat_count = db.scalar(select(func.count()).select_from(CombatLog))
    cleaned_count = db.scalar(select(func.count()).select_from(CleanedCombatLog))
    prediction_count = db.scalar(select(func.count()).select_from(MLPrediction))
    model_count = db.scalar(select(func.count()).select_from(MLModelVersion))

    active = get_active_model_version(db)
    latest_comp = get_latest_comparison(db)

    return {
        "combat_logs": int(combat_count or 0),
        "cleaned_combat_logs": int(cleaned_count or 0),
        "predictions": int(prediction_count or 0),
        "model_versions": int(model_count or 0),
        "active_model": active.version if active else None,
        "latest_comparison_id": latest_comp.id if latest_comp else None,
        "latest_comparison_winner": latest_comp.winner_version if latest_comp else None,
    }
