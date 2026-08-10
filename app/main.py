"""FastAPI application entry point.

Exposes the game API under ``/api`` and serves the static frontend from the
``frontend/`` directory so the whole game runs from a single origin. Launch in
development with::

    uvicorn app.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router

app = FastAPI(
    title="ChessQuest API",
    description="Backend for the ChessQuest browser chess game.",
    version="1.0.0",
)

# Permissive CORS so the frontend can talk to the API during local development
# even if served from a different port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# Serve the built frontend at the root. Registered last so the API routes above
# take precedence over the static catch-all.
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
