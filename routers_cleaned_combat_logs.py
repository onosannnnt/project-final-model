from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import crud
from database import get_db
from schemas import (
    CleanCombatLogsRequest,
    CleanCombatLogsResponse,
    CleanedCombatLogRead,
)

router = APIRouter(prefix="/cleaned-combat-logs", tags=["cleaned-combat-logs"])


@router.post("/run", response_model=CleanCombatLogsResponse)
def run_clean_pipeline(
    payload: CleanCombatLogsRequest,
    db: Session = Depends(get_db),
) -> CleanCombatLogsResponse:
    cleaned_logs = crud.clean_combat_logs(db, session_id=payload.session_id)

    return CleanCombatLogsResponse(
        inserted=len(cleaned_logs),
        session_id=payload.session_id,
        cleaned_logs=[CleanedCombatLogRead.model_validate(row) for row in cleaned_logs],
    )


@router.get("", response_model=list[CleanedCombatLogRead])
def list_cleaned_combat_logs(
    session_id: int | None = Query(default=None),
    player_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CleanedCombatLogRead]:
    rows = crud.list_cleaned_combat_logs(db, session_id=session_id, player_id=player_id)
    return [CleanedCombatLogRead.model_validate(row) for row in rows]


@router.get("/{cleaned_id}", response_model=CleanedCombatLogRead)
def get_cleaned_combat_log(
    cleaned_id: int, db: Session = Depends(get_db)
) -> CleanedCombatLogRead:
    row = crud.get_cleaned_combat_log_by_id(db, cleaned_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Cleaned combat log not found.")
    return CleanedCombatLogRead.model_validate(row)


@router.delete("/session/{session_id}")
def delete_cleaned_combat_logs_by_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> dict:
    deleted = crud.delete_cleaned_combat_logs_by_session(db, session_id=session_id)
    return {"deleted": deleted, "session_id": session_id}
