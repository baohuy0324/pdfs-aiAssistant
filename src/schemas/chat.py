"""
Pydantic schemas cho toàn bộ API.
"""
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="ID trả về từ POST /v1/ingest")
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str


class IngestResponse(BaseModel):
    session_id: str
    message: str


class DeleteResponse(BaseModel):
    ok: bool
    message: str


class ErrorResponse(BaseModel):
    error: str
    message: str


class HealthResponse(BaseModel):
    status: str


ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    404: {"model": ErrorResponse, "description": "Not Found"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}
