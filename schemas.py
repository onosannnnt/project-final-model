from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from enums import UserType, WeatherType


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    type: UserType | None = None
    tier: int | None = Field(default=None, ge=1, le=4)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=255)
    type: UserType | None = None
    tier: int | None = Field(default=None, ge=1, le=4)


class UserRead(BaseModel):
    id: int
    username: str
    type: UserType | None
    tier: int | None

    model_config = {"from_attributes": True}


class CombatLogBase(BaseModel):
    session_id: UUID
    player_id: int
    character_id: int
    wave_number: int
    turn_index: int
    skill_id: int
    skill_target_id: int
    target_max_hp: float
    target_current_hp: float
    damage_dealt: float
    damage_recieve: float
    caster_current_sp: int
    caster_current_hp: float
    caster_max_hp: float
    current_frenzy_stack: int
    heal_amount: float
    current_corrupt_blood_gain: float
    corrupt_blood_by_max_hp: float
    weather: WeatherType
    momentum_gain: int
    momentum_used: int


class CombatLogCreate(CombatLogBase):
    pass


class CombatLogCreateBatch(BaseModel):
    items: list[CombatLogCreate]


class CombatLogUpdate(BaseModel):
    session_id: UUID | None = None
    player_id: int | None = None
    character_id: int | None = Field(default=None, ge=1, le=2)
    wave_number: int | None = None
    turn_index: int | None = None
    skill_id: int | None = None
    skill_target_id: int | None = None
    target_max_hp: float | None = None
    target_current_hp: float | None = None
    damage_dealt: float | None = None
    damage_recieve: float | None = None
    caster_current_sp: int | None = None
    caster_current_hp: float | None = None
    caster_max_hp: float | None = None
    current_frenzy_stack: int | None = None
    heal_amount: float | None = None
    current_corrupt_blood_gain: float | None = None
    corrupt_blood_by_max_hp: float | None = None
    weather: WeatherType | None = None
    momentum_gain: int | None = None
    momentum_used: int | None = None


class CombatLogRead(CombatLogBase):
    id: int

    model_config = {"from_attributes": True}


class CleanCombatLogsRequest(BaseModel):
    session_id: UUID | None = None


class CleanedCombatLogRead(BaseModel):
    id: int
    source_combat_log_id: int
    session_id: UUID
    player_id: int
    cleaned_payload: dict
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CleanCombatLogsResponse(BaseModel):
    inserted: int
    session_id: UUID | None = None
    cleaned_logs: list[CleanedCombatLogRead]


class TrainModelRequest(BaseModel):
    version: str
    n_clusters: int = Field(default=3, ge=2, le=20)
    session_ids: list[UUID] | None = None


class TrainModelResponse(BaseModel):
    version: str
    algorithm: str
    n_features: int
    metrics: dict[str, Any] | None


class ActivateModelRequest(BaseModel):
    version: str


class UploadModelRequest(BaseModel):
    version: str
    algorithm: str = "kmeans"
    artifact_base64: str
    feature_columns: list[str]
    metrics: dict[str, Any] | None = None


class ModelVersionRead(BaseModel):
    id: int
    version: str
    algorithm: str
    artifact_path: str
    feature_columns: list
    metrics: dict[str, Any] | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineRunAllRequest(BaseModel):
    clean_session_id: UUID | None = None
    version: str
    n_clusters: int = Field(default=3, ge=2, le=20)
    train_session_ids: list[UUID] | None = None


class MLPredictRequest(BaseModel):
    combat_log: CombatLogCreate


class MLPredictBatchRequest(BaseModel):
    items: list[CombatLogCreate]


class MLPredictResponse(BaseModel):
    model_version: str
    cluster_label: int
    features: dict[str, Any]


class MLPredictBatchResponseItem(BaseModel):
    cluster_label: int
    features: dict[str, Any]


class MLPredictBatchResponse(BaseModel):
    model_version: str
    items: list[MLPredictBatchResponseItem]


class MLPredictionRead(BaseModel):
    id: int
    model_version: str
    source_type: str
    source_id: int | None
    session_id: UUID | None
    player_id: int | None
    input_payload: dict[str, Any]
    cluster_label: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CompareModelsRequest(BaseModel):
    model_versions: list[str]
    session_ids: list[UUID] | None = None


class CompareModelsResponse(BaseModel):
    comparison_id: int
    winner_version: str | None
    summary: dict[str, Any]


class ProjectSummaryResponse(BaseModel):
    combat_logs: int
    cleaned_combat_logs: int
    predictions: int
    model_versions: int
    active_model: str | None
    latest_comparison_id: int | None
    latest_comparison_winner: str | None


class ReadyResponse(BaseModel):
    api: str
    database: str
    active_model: str


class StageCompleteRequest(BaseModel):
    player_id: int
    combat_logs: list[CombatLogCreate]


class StageCompleteResponse(BaseModel):
    user_id: int
    previous_type: UserType | None
    new_type: UserType
    previous_tier: int | None
    new_tier: int
    predicted_cluster: int
    model_version: str
    update_mode: str



class ProjectSummaryResponse(BaseModel):
    combat_logs: int
    cleaned_combat_logs: int
    predictions: int
    model_versions: int
    active_model: str | None
    latest_comparison_id: int | None
    latest_comparison_winner: str | None


class ReadyResponse(BaseModel):
    api: str
    database: str
    active_model: str


class StageCompleteRequest(BaseModel):
    player_id: int
    combat_logs: list[CombatLogCreate]


class StageCompleteResponse(BaseModel):
    user_id: int
    previous_type: UserType | None
    new_type: UserType
    previous_tier: int | None
    new_tier: int
    predicted_cluster: int
    model_version: str
    update_mode: str
