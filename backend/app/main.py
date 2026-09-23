from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import init_db
from app.api.routes import router
from app.services.snapshots.scheduler import start_background_checkpoints

app = FastAPI(
    title="Project Context Manager",
    description="Lightweight semantic framework for cross-application developer workspace restoration.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    init_db()
    start_background_checkpoints()


@app.get("/health")
def health():
    return {"status": "ok"}
