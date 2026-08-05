"""FastAPI entrypoint for Shared Persona Core."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.responses import UTF8JSONResponse

from app.config import get_settings
from app.routers import chat, world
from app.schemas import HealthResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Cloud soul backend for a shared desktop pet Persona Core.",
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(world.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health and version metadata."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_version=settings.app_version,
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the minimal web entry point."""
    return FileResponse("app/static/index.html")
