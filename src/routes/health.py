"""
Router: Health Check
GET /health — kiểm tra Redis còn sống không.
"""
from fastapi import APIRouter, HTTPException, Request

from src.schemas.chat import ErrorResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": ErrorResponse, "description": "Service Unavailable"}},
)
async def health(request: Request):
    """Ping Redis để xác nhận service còn hoạt động."""
    try:
        await request.app.state.redis.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Redis không phản hồi.")
    return HealthResponse(status="ok")
