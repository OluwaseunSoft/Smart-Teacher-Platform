from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    admin,
    auth,
    curriculum,
    gamification,
    lessons,
    mastery,
    materials,
    notifications,
    planner,
    quizzes,
    reviews,
    sessions,
    tutor,
)
from app.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Suhail Smart Teacher API",
    version="0.1.0",
    description="AI-powered personal teacher: read, organize, teach, test, adapt.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(materials.router)
app.include_router(lessons.router)
app.include_router(quizzes.router)
app.include_router(sessions.router)
app.include_router(curriculum.router)
app.include_router(reviews.router)
app.include_router(mastery.router)
app.include_router(tutor.router)
app.include_router(planner.router)
app.include_router(gamification.router)
app.include_router(notifications.router)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
    }
