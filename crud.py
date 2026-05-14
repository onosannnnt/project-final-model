import uuid
from uuid import UUID

import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from cleaned import build_features
from models import CleanedCombatLog, CombatLog, User
from schemas import CombatLogCreate, CombatLogUpdate, UserCreate, UserUpdate


def _sanitize_payload(d: dict) -> dict:
    """Convert all values in a dict to JSON-serialisable Python primitives."""
    result = {}
    for k, v in d.items():
        if isinstance(v, uuid.UUID):
            result[k] = str(v)
        elif isinstance(v, (np.integer,)):
            result[k] = int(v)
        elif isinstance(v, (np.floating,)):
            result[k] = float(v)
        elif isinstance(v, (np.bool_,)):
            result[k] = bool(v)
        elif isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            result[k] = 0.0
        else:
            result[k] = v
    return result


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(username=payload.username, type=payload.type, tier=payload.tier)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.username.asc())).all())


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


def create_combat_log(db: Session, payload: CombatLogCreate) -> CombatLog:
    combat_log = CombatLog(**payload.model_dump())
    db.add(combat_log)
    db.commit()
    db.refresh(combat_log)
    return combat_log


def create_combat_logs_batch(
    db: Session, payloads: list[CombatLogCreate]
) -> list[CombatLog]:
    logs = [CombatLog(**payload.model_dump()) for payload in payloads]
    db.add_all(logs)
    db.commit()
    for log in logs:
        db.refresh(log)
    return logs


def list_combat_logs(
    db: Session,
    session_id: UUID | None = None,
    player_id: int | None = None,
) -> list[CombatLog]:
    stmt = select(CombatLog)
    if session_id is not None:
        stmt = stmt.where(CombatLog.session_id == session_id)
    if player_id is not None:
        stmt = stmt.where(CombatLog.player_id == player_id)

    stmt = stmt.order_by(
        CombatLog.session_id.asc(),
        CombatLog.wave_number.asc(),
        CombatLog.turn_index.asc(),
    )
    return list(db.scalars(stmt).all())


def get_combat_log_by_id(db: Session, combat_log_id: int) -> CombatLog | None:
    return db.get(CombatLog, combat_log_id)


def update_combat_log(
    db: Session, combat_log: CombatLog, payload: CombatLogUpdate
) -> CombatLog:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(combat_log, key, value)
    db.commit()
    db.refresh(combat_log)
    return combat_log


def delete_combat_log(db: Session, combat_log: CombatLog) -> None:
    db.delete(combat_log)
    db.commit()


def list_cleaned_combat_logs(
    db: Session,
    session_id: UUID | None = None,
    player_id: int | None = None,
) -> list[CleanedCombatLog]:
    stmt = select(CleanedCombatLog)
    if session_id is not None:
        stmt = stmt.where(CleanedCombatLog.session_id == session_id)
    if player_id is not None:
        stmt = stmt.where(CleanedCombatLog.player_id == player_id)
    stmt = stmt.order_by(CleanedCombatLog.created_at.desc())
    return list(db.scalars(stmt).all())


def get_cleaned_combat_log_by_id(
    db: Session, cleaned_id: int
) -> CleanedCombatLog | None:
    return db.get(CleanedCombatLog, cleaned_id)


def delete_cleaned_combat_logs_by_session(db: Session, session_id: UUID) -> int:
    result = db.execute(
        delete(CleanedCombatLog).where(CleanedCombatLog.session_id == session_id)
    )
    db.commit()
    return int(result.rowcount or 0)


def clean_combat_logs(
    db: Session, session_id: UUID | None = None
) -> list[CleanedCombatLog]:
    """
    Reads CombatLog rows from DB, runs build_features(), and upserts
    one CleanedCombatLog per session into cleaned_combat_logs.

    build_features() is expected to return one aggregated row per session_id.
    Each resulting CleanedCombatLog stores:
      - session_id / player_id   from the first CombatLog of that session
      - source_combat_log_id     = id of the first CombatLog of that session
      - cleaned_payload          = the full feature dict (including session_id as UUID)
    """
    query = select(CombatLog)
    if session_id is not None:
        query = query.where(CombatLog.session_id == session_id)

    combat_logs = list(
        db.scalars(
            query.order_by(
                CombatLog.session_id.asc(),
                CombatLog.wave_number.asc(),
                CombatLog.turn_index.asc(),
            )
        ).all()
    )

    if not combat_logs:
        return []

    # ---------- build raw dataframe ----------
    raw_rows: list[dict] = []
    for log in combat_logs:
        raw_rows.append(
            {
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
                "weather": str(log.weather),
                "momentum_gain": log.momentum_gain,
                "momentum_used": log.momentum_used,
                # optional columns expected by build_features
                "break_count": 0,
                "break_damage": 0.0,
                "target_debuff_count": 0.0,
                "debuff_hit_ratio": 0.0,
            }
        )

    raw_df = pd.DataFrame(raw_rows)
    features_df = build_features(raw_df)
    features_df = features_df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    feature_rows = features_df.to_dict(orient="records")

    logs_by_session: dict[str, list[CombatLog]] = {}
    for log in combat_logs:
        logs_by_session.setdefault(str(log.session_id), []).append(log)

    # Build a UUID-keyed map to the first log of each session
    first_log_by_session: dict[uuid.UUID, CombatLog] = {
        uuid.UUID(sid): logs[0] for sid, logs in logs_by_session.items()
    }

    # ---------- delete stale cleaned rows for affected sessions ----------
    target_sessions = {log.session_id for log in combat_logs}
    db.execute(
        delete(CleanedCombatLog).where(CleanedCombatLog.session_id.in_(target_sessions))
    )

    # ---------- insert one CleanedCombatLog per feature row ----------
    cleaned_logs: list[CleanedCombatLog] = []
    for feature_row in feature_rows:
        raw_session_id = feature_row.get("session_id")
        if raw_session_id is None:
            continue
        # Normalise to uuid.UUID regardless of whether it came back as str/UUID.
        try:
            row_session_id = (
                raw_session_id
                if isinstance(raw_session_id, uuid.UUID)
                else uuid.UUID(str(raw_session_id))
            )
        except ValueError, AttributeError:
            continue

        source_log = first_log_by_session.get(row_session_id)
        if source_log is None:
            continue

        # feature_row is already a plain dict (from to_dict(orient="records")),
        # so sanitize it directly without calling .to_dict() again.
        payload_dict = _sanitize_payload(feature_row)
        payload_dict["session_id"] = str(row_session_id)

        cleaned_logs.append(
            CleanedCombatLog(
                source_combat_log_id=source_log.id,
                session_id=row_session_id,
                player_id=source_log.player_id,
                cleaned_payload=payload_dict,
            )
        )

    if cleaned_logs:
        db.add_all(cleaned_logs)
        db.commit()
        for cleaned_log in cleaned_logs:
            db.refresh(cleaned_log)

    return cleaned_logs
