from sqlalchemy import CheckConstraint, Float, Integer, String
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
