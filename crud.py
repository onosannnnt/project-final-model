from sqlalchemy import select
from sqlalchemy.orm import Session

from models import CombatLog, User
from schemas import CombatLogCreate, CombatLogUpdate, UserCreate, UserUpdate


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


def list_combat_logs(db: Session) -> list[CombatLog]:
    stmt = select(CombatLog).order_by(
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
