"""Pydantic schemas shared by API routes and services."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    app_name: str
    app_version: str


class WorldState(BaseModel):
    """Public state that drives both the web view and PyQt6 pet animations."""

    world_id: str = "shared_world"
    mood: str = "curious"
    color: str = "blue"
    animation: str = "idle"
    energy: int = Field(default=70, ge=0, le=100)
    friendliness: int = Field(default=60, ge=0, le=100)
    curiosity: int = Field(default=80, ge=0, le=100)
    chaos: int = Field(default=20, ge=0, le=100)
    stress: int = Field(default=30, ge=0, le=100)
    loneliness: int = Field(default=10, ge=0, le=100)


class ChatRequest(BaseModel):
    """Request body for chatting with the shared world soul."""

    message: str = Field(..., min_length=1, max_length=4000)
    password: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Response returned to the web page or PyQt6 desktop pet."""

    reply: str
    world_state: WorldState
    new_memories: list[str] = Field(default_factory=list)
