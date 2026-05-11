from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

import crud
from database import get_db
from schemas import (
    CombatLogCreate,
    CombatLogCreateBatch,
    CombatLogRead,
    CombatLogUpdate,
)

router = APIRouter(prefix="/combat-logs", tags=["combat-logs"])


@router.post("", response_model=CombatLogRead, status_code=status.HTTP_201_CREATED)
def create_combat_log(
    payload: CombatLogCreate, db: Session = Depends(get_db)
) -> CombatLogRead:
    combat_log = crud.create_combat_log(db, payload)
    return CombatLogRead.model_validate(combat_log)


@router.post(
    "/batch", response_model=list[CombatLogRead], status_code=status.HTTP_201_CREATED
)
def create_combat_logs_batch(
    payload: CombatLogCreateBatch,
    db: Session = Depends(get_db),
) -> list[CombatLogRead]:
    combat_logs = crud.create_combat_logs_batch(db, payload.items)
    return [CombatLogRead.model_validate(combat_log) for combat_log in combat_logs]


@router.get("", response_model=list[CombatLogRead])
def list_combat_logs(
    session_id: int | None = Query(default=None),
    player_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CombatLogRead]:
    combat_logs = crud.list_combat_logs(db, session_id=session_id, player_id=player_id)
    return [CombatLogRead.model_validate(combat_log) for combat_log in combat_logs]


@router.get("/{combat_log_id}", response_model=CombatLogRead)
def get_combat_log(combat_log_id: int, db: Session = Depends(get_db)) -> CombatLogRead:
    combat_log = crud.get_combat_log_by_id(db, combat_log_id)
    if combat_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Combat log not found."
        )
    return CombatLogRead.model_validate(combat_log)


@router.put("/{combat_log_id}", response_model=CombatLogRead)
def update_combat_log(
    combat_log_id: int,
    payload: CombatLogUpdate,
    db: Session = Depends(get_db),
) -> CombatLogRead:
    combat_log = crud.get_combat_log_by_id(db, combat_log_id)
    if combat_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Combat log not found."
        )

    updated = crud.update_combat_log(db, combat_log, payload)
    return CombatLogRead.model_validate(updated)


@router.delete("/{combat_log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_combat_log(combat_log_id: int, db: Session = Depends(get_db)) -> Response:
    combat_log = crud.get_combat_log_by_id(db, combat_log_id)
    if combat_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Combat log not found."
        )

    crud.delete_combat_log(db, combat_log)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
