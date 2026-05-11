from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

import crud
import ml_service
from database import get_db
from schemas import (
    ActivateModelRequest,
    CompareModelsRequest,
    CompareModelsResponse,
    MLPredictBatchRequest,
    MLPredictBatchResponse,
    MLPredictBatchResponseItem,
    MLPredictionRead,
    MLPredictRequest,
    MLPredictResponse,
    ModelVersionRead,
    PipelineRunAllRequest,
    ProjectSummaryResponse,
    ReadyResponse,
    StageCompleteRequest,
    StageCompleteResponse,
    TrainModelRequest,
    TrainModelResponse,
    UploadModelRequest,
)

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/ready", response_model=ReadyResponse)
def ready(db: Session = Depends(get_db)) -> ReadyResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    active = ml_service.get_active_model_version(db)
    active_model = active.version if active else "not_configured"

    return ReadyResponse(api="ok", database=db_status, active_model=active_model)


@router.post("/pipeline/clean")
def pipeline_clean(
    payload: dict,
    db: Session = Depends(get_db),
) -> dict:
    session_id = payload.get("session_id")
    cleaned_logs = crud.clean_combat_logs(db, session_id=session_id)
    return {"inserted": len(cleaned_logs), "session_id": session_id}


@router.post("/pipeline/features")
def pipeline_features(
    payload: dict,
    db: Session = Depends(get_db),
) -> dict:
    session_id = payload.get("session_id")
    cleaned_logs = crud.clean_combat_logs(db, session_id=session_id)
    return {"features_generated": len(cleaned_logs), "session_id": session_id}


@router.post("/pipeline/train", response_model=TrainModelResponse)
def pipeline_train(
    payload: TrainModelRequest,
    db: Session = Depends(get_db),
) -> TrainModelResponse:
    try:
        model = ml_service.train_kmeans_from_cleaned(
            db,
            version=payload.version,
            n_clusters=payload.n_clusters,
            session_ids=payload.session_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return TrainModelResponse(
        version=model.version,
        algorithm=model.algorithm,
        n_features=len(model.feature_columns),
        metrics=model.metrics,
    )


@router.post("/pipeline/run-all")
def pipeline_run_all(
    payload: PipelineRunAllRequest,
    db: Session = Depends(get_db),
) -> dict:
    cleaned_logs = crud.clean_combat_logs(db, session_id=payload.clean_session_id)
    try:
        model = ml_service.train_kmeans_from_cleaned(
            db,
            version=payload.version,
            n_clusters=payload.n_clusters,
            session_ids=payload.train_session_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "cleaned_rows": len(cleaned_logs),
        "trained_model": model.version,
        "algorithm": model.algorithm,
    }


@router.post("/model/upload", response_model=ModelVersionRead)
def upload_model(
    payload: UploadModelRequest,
    db: Session = Depends(get_db),
) -> ModelVersionRead:
    model = ml_service.register_uploaded_model(
        db,
        version=payload.version,
        algorithm=payload.algorithm,
        artifact_base64=payload.artifact_base64,
        feature_columns=payload.feature_columns,
        metrics=payload.metrics,
    )
    return ModelVersionRead.model_validate(model)


@router.get("/model/info", response_model=ModelVersionRead)
def model_info(db: Session = Depends(get_db)) -> ModelVersionRead:
    active = ml_service.get_active_model_version(db)
    if active is None:
        raise HTTPException(status_code=404, detail="No active model configured.")
    return ModelVersionRead.model_validate(active)


@router.get("/model/versions", response_model=list[ModelVersionRead])
def model_versions(db: Session = Depends(get_db)) -> list[ModelVersionRead]:
    rows = ml_service.get_model_versions(db)
    return [ModelVersionRead.model_validate(row) for row in rows]


@router.post("/model/reload")
def model_reload(db: Session = Depends(get_db)) -> dict:
    try:
        info = ml_service.reload_active_model(db)
    except ml_service.ModelNotReadyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"reloaded": True, **info}


@router.post("/model/activate", response_model=ModelVersionRead)
def model_activate(
    payload: ActivateModelRequest,
    db: Session = Depends(get_db),
) -> ModelVersionRead:
    try:
        model = ml_service.set_active_model(db, payload.version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ModelVersionRead.model_validate(model)


@router.post("/model/activate/{model_version}", response_model=ModelVersionRead)
def model_activate_by_path(
    model_version: str, db: Session = Depends(get_db)
) -> ModelVersionRead:
    try:
        model = ml_service.set_active_model(db, model_version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ModelVersionRead.model_validate(model)


@router.post("/predict", response_model=MLPredictResponse)
def predict(
    payload: MLPredictRequest,
    db: Session = Depends(get_db),
) -> MLPredictResponse:
    feature_payload = ml_service.build_feature_payload_from_combat_logs(
        [
            {
                **payload.combat_log.model_dump(),
                "skill_target": payload.combat_log.skill_target_id,
                "weather": payload.combat_log.weather.value,
                "break_count": 0,
                "break_damage": 0.0,
                "target_debuff_count": 0.0,
                "debuff_hit_ratio": 0.0,
            }
        ]
    )
    try:
        label, model_version = ml_service.predict_with_active_model(db, feature_payload)
    except ml_service.ModelNotReadyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return MLPredictResponse(
        model_version=model_version,
        cluster_label=label,
        features=feature_payload,
    )


@router.post(
    "/predict-from-combat-log/{combat_log_id}", response_model=MLPredictResponse
)
def predict_from_combat_log(
    combat_log_id: int, db: Session = Depends(get_db)
) -> MLPredictResponse:
    log = crud.get_combat_log_by_id(db, combat_log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Combat log not found.")

    feature_payload = ml_service.build_feature_payload_from_combat_log(log)
    try:
        label, model_version = ml_service.predict_with_active_model(db, feature_payload)
    except ml_service.ModelNotReadyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return MLPredictResponse(
        model_version=model_version,
        cluster_label=label,
        features=feature_payload,
    )


@router.post("/predict/batch", response_model=MLPredictBatchResponse)
def predict_batch(
    payload: MLPredictBatchRequest,
    db: Session = Depends(get_db),
) -> MLPredictBatchResponse:
    items: list[MLPredictBatchResponseItem] = []
    model_version: str | None = None

    for combat_log in payload.items:
        feature_payload = ml_service.build_feature_payload_from_combat_logs(
            [
                {
                    **combat_log.model_dump(),
                    "skill_target": combat_log.skill_target_id,
                    "weather": combat_log.weather.value,
                    "break_count": 0,
                    "break_damage": 0.0,
                    "target_debuff_count": 0.0,
                    "debuff_hit_ratio": 0.0,
                }
            ]
        )
        try:
            label, mv = ml_service.predict_with_active_model(db, feature_payload)
        except ml_service.ModelNotReadyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

        model_version = mv
        items.append(
            MLPredictBatchResponseItem(cluster_label=label, features=feature_payload)
        )

    return MLPredictBatchResponse(model_version=model_version or "", items=items)


@router.post("/predict-and-save", response_model=MLPredictionRead)
def predict_and_save(
    payload: MLPredictRequest,
    db: Session = Depends(get_db),
) -> MLPredictionRead:
    feature_payload = ml_service.build_feature_payload_from_combat_logs(
        [
            {
                **payload.combat_log.model_dump(),
                "skill_target": payload.combat_log.skill_target_id,
                "weather": payload.combat_log.weather.value,
                "break_count": 0,
                "break_damage": 0.0,
                "target_debuff_count": 0.0,
                "debuff_hit_ratio": 0.0,
            }
        ]
    )
    try:
        label, model_version = ml_service.predict_with_active_model(db, feature_payload)
    except ml_service.ModelNotReadyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    saved = ml_service.save_prediction(
        db,
        model_version=model_version,
        source_type="payload",
        input_payload=feature_payload,
        cluster_label=label,
        session_id=payload.combat_log.session_id,
        player_id=payload.combat_log.player_id,
    )
    return MLPredictionRead.model_validate(saved)


@router.get("/predictions/{prediction_id}", response_model=MLPredictionRead)
def get_prediction(
    prediction_id: int, db: Session = Depends(get_db)
) -> MLPredictionRead:
    row = ml_service.get_prediction_by_id(db, prediction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Prediction not found.")
    return MLPredictionRead.model_validate(row)


@router.get("/predictions", response_model=list[MLPredictionRead])
def list_predictions(
    session_id: int | None = Query(default=None),
    player_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[MLPredictionRead]:
    rows = ml_service.list_predictions(db, session_id=session_id, player_id=player_id)
    return [MLPredictionRead.model_validate(row) for row in rows]


@router.post("/models/compare", response_model=CompareModelsResponse)
def compare_models(
    payload: CompareModelsRequest,
    db: Session = Depends(get_db),
) -> CompareModelsResponse:
    try:
        row = ml_service.compare_models(
            db,
            versions=payload.model_versions,
            session_ids=payload.session_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return CompareModelsResponse(
        comparison_id=row.id,
        winner_version=row.winner_version,
        summary=row.summary,
    )


@router.get("/models/compare/latest", response_model=CompareModelsResponse)
def latest_comparison(db: Session = Depends(get_db)) -> CompareModelsResponse:
    row = ml_service.get_latest_comparison(db)
    if row is None:
        raise HTTPException(status_code=404, detail="No comparison found.")

    return CompareModelsResponse(
        comparison_id=row.id,
        winner_version=row.winner_version,
        summary=row.summary,
    )


@router.get("/models/compare/{comparison_id}", response_model=CompareModelsResponse)
def comparison_by_id(
    comparison_id: int, db: Session = Depends(get_db)
) -> CompareModelsResponse:
    row = ml_service.get_comparison_by_id(db, comparison_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Comparison not found.")

    return CompareModelsResponse(
        comparison_id=row.id,
        winner_version=row.winner_version,
        summary=row.summary,
    )


@router.get("/models/compare/{comparison_id}/export")
def comparison_export(comparison_id: int, db: Session = Depends(get_db)) -> dict:
    row = ml_service.get_comparison_by_id(db, comparison_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Comparison not found.")

    return {
        "comparison_id": row.id,
        "winner_version": row.winner_version,
        "summary": row.summary,
    }


@router.post("/stage-complete", response_model=StageCompleteResponse)
def stage_complete(
    payload: StageCompleteRequest,
    db: Session = Depends(get_db),
) -> StageCompleteResponse:
    user = crud.get_user_by_id(db, payload.player_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    saved_logs = crud.create_combat_logs_batch(db, payload.combat_logs)

    log_rows = []
    for log in payload.combat_logs:
        data = log.model_dump()
        log_rows.append(
            {
                **data,
                "skill_target": data["skill_target_id"],
                "weather": data["weather"].value,
                "break_count": 0,
                "break_damage": 0.0,
                "target_debuff_count": 0.0,
                "debuff_hit_ratio": 0.0,
            }
        )

    features = ml_service.build_feature_payload_from_combat_logs(log_rows)
    try:
        cluster_label, model_version = ml_service.predict_with_active_model(
            db, features
        )
    except ml_service.ModelNotReadyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    predicted_type = ml_service.cluster_to_user_type(cluster_label)

    previous_type = user.type
    previous_tier = user.tier

    if user.type is None:
        user.type = predicted_type
        user.tier = 1
        update_mode = "initialized"
    elif user.type == predicted_type:
        user.tier = min(max(user.tier or 1, 1) + 1, 3)
        update_mode = "reinforced"
    else:
        user.type = predicted_type
        user.tier = 1
        update_mode = "changed"

    db.commit()
    db.refresh(user)

    source_id = saved_logs[-1].id if saved_logs else None
    ml_service.save_prediction(
        db,
        model_version=model_version,
        source_type="stage_complete",
        source_id=source_id,
        session_id=saved_logs[-1].session_id if saved_logs else None,
        player_id=user.id,
        input_payload=features,
        cluster_label=cluster_label,
    )

    return StageCompleteResponse(
        user_id=user.id,
        previous_type=previous_type,
        new_type=user.type,
        previous_tier=previous_tier,
        new_tier=user.tier or 1,
        predicted_cluster=cluster_label,
        model_version=model_version,
        update_mode=update_mode,
    )


@router.get("/project-summary", response_model=ProjectSummaryResponse)
def project_summary(db: Session = Depends(get_db)) -> ProjectSummaryResponse:
    return ProjectSummaryResponse(**ml_service.get_project_summary(db))
