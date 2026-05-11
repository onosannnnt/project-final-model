from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Integer,
    String,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from enums import UserType, WeatherType


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "tier IS NULL OR tier BETWEEN 1 AND 4", name="users_tier_range"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    type: Mapped[UserType | None] = mapped_column(
        SQLEnum(UserType, name="user_type_enum"), nullable=True
    )
    tier: Mapped[int | None] = mapped_column(Integer, nullable=True)


class CombatLog(Base):
    __tablename__ = "combat_logs"
    __table_args__ = (
        CheckConstraint(
            "character_id BETWEEN 1 AND 2", name="combat_logs_character_id_range"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    character_id: Mapped[int] = mapped_column(Integer, nullable=False)
    wave_number: Mapped[int] = mapped_column(Integer, nullable=False)
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_max_hp: Mapped[float] = mapped_column(Float, nullable=False)
    target_current_hp: Mapped[float] = mapped_column(Float, nullable=False)
    damage_dealt: Mapped[float] = mapped_column(Float, nullable=False)
    damage_recieve: Mapped[float] = mapped_column(Float, nullable=False)
    caster_current_sp: Mapped[int] = mapped_column(Integer, nullable=False)
    caster_current_hp: Mapped[float] = mapped_column(Float, nullable=False)
    caster_max_hp: Mapped[float] = mapped_column(Float, nullable=False)
    current_frenzy_stack: Mapped[int] = mapped_column(Integer, nullable=False)
    heal_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_corrupt_blood_gain: Mapped[float] = mapped_column(Float, nullable=False)
    corrupt_blood_by_max_hp: Mapped[float] = mapped_column(Float, nullable=False)
    weather: Mapped[WeatherType] = mapped_column(
        SQLEnum(WeatherType, name="weather_type_enum"), nullable=False
    )
    momentum_gain: Mapped[int] = mapped_column(Integer, nullable=False)
    momentum_used: Mapped[int] = mapped_column(Integer, nullable=False)


class CleanedCombatLog(Base):
    __tablename__ = "cleaned_combat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_combat_log_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cleaned_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MLModelVersion(Base):
    __tablename__ = "ml_model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    feature_columns: Mapped[list] = mapped_column(JSON, nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    session_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    player_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    cluster_label: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MLModelComparison(Base):
    __tablename__ = "ml_model_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    compared_versions: Mapped[list] = mapped_column(JSON, nullable=False)
    winner_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
