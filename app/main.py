from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from app.api.v1.router import router as api_router
from app.core.config import get_settings


app = FastAPI(
    title="Enterprise Service Management Platform",
    version="0.1.0",
)
app.include_router(api_router)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_index = Path(__file__).resolve().parents[1] / "frontend" / "dist" / "index.html"


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {"message": "ESMP API is running"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/version", tags=["health"])
def version() -> dict[str, str]:
    return {"version": app.version}


if frontend_index.exists():

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        requested = frontend_index.parent / path
        if path and requested.is_file():
            return FileResponse(requested)
        return FileResponse(frontend_index)