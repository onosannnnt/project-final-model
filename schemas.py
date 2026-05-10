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
    session_id: int
    player_id: int
    character_id: int = Field(ge=1, le=2)
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


class CombatLogUpdate(BaseModel):
    session_id: int | None = None
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
