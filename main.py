import uvicorn
from fastapi import FastAPI

from database import Base, engine
from routers_combat_logs import router as combat_logs_router
from routers_users import router as users_router

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(users_router)
app.include_router(combat_logs_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
