"""Aplicação FastAPI local (projetos, chats, mensagens)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routes import chats as chats_routes
from apps.api.routes import projects as projects_routes
from apps.api.routes import runs as runs_routes
from core.database.schema import init_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_database()
    yield


app = FastAPI(title="squad-agentes API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_routes.router, prefix="/api/projects", tags=["projects"])
app.include_router(chats_routes.router, prefix="/api/chats", tags=["chats"])
app.include_router(runs_routes.router, prefix="/api/runs", tags=["runs"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
