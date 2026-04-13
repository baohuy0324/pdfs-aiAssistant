"""
Redis lifespan context manager.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis_async
from fastapi import FastAPI

from src.core.config import REDIS_URL

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Đang khởi tạo kết nối Redis tới {REDIS_URL}...")
    client = redis_async.from_url(REDIS_URL, decode_responses=False)
    try:
        await client.ping()
        logger.info("Kết nối Redis thành công!")
    except Exception as e:
        logger.error(f"Lỗi nối Redis: {e}")
        await client.aclose()
        raise RuntimeError(f"Không kết nối được Redis ({REDIS_URL}): {e}") from e
    app.state.redis = client
    yield
    logger.info("Đóng kết nối Redis...")
    await client.aclose()
