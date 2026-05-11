import uvicorn
from fastapi import FastAPI
from sqlalchemy import text

from database import Base, SessionLocal, engine
from routers_cleaned_combat_logs import router as cleaned_combat_logs_router
from routers_combat_logs import router as combat_logs_router
from routers_ml import router as ml_router
from routers_users import router as users_router

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready_check() -> dict:
    db_status = "ok"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {"api": "ok", "database": db_status}


app.include_router(users_router)
app.include_router(combat_logs_router)
app.include_router(cleaned_combat_logs_router)
app.include_router(ml_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
