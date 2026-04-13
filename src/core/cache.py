"""
LRU Cache thread-safe cho FAISS vectorstore.
"""
from __future__ import annotations

import logging
import threading

from cachetools import LRUCache
from langchain_community.vectorstores import FAISS

from src.services.rag import get_embeddings

logger = logging.getLogger(__name__)

# cachetools.LRUCache không thread-safe => cần lock khi truy cập từ thread pool
_cache_lock = threading.Lock()
VECTORSTORE_CACHE: LRUCache = LRUCache(maxsize=50)


def get_vectorstore(session_id: str, payload: bytes) -> FAISS:
    """
    Lấy FAISS vectorstore từ RAM cache hoặc deserialize từ payload.
    Thread-safe nhờ double-checked locking: deserialize nặng CPU thực hiện ngoài lock.
    """
    with _cache_lock:
        if session_id in VECTORSTORE_CACHE:
            logger.info(f"Cache hit: Đã tìm thấy VectorStore của session='{session_id}' trong RAM")
            return VECTORSTORE_CACHE[session_id]

    # Deserialize ngoài lock (CPU nặng, không block threads khác)
    logger.info(f"Cache miss: Đang giải mã VectorStore cho session='{session_id}'...")
    vectorstore = FAISS.deserialize_from_bytes(
        payload, get_embeddings(), allow_dangerous_deserialization=True
    )

    # Double-check: nếu thread khác đã deserialize xong trước => dùng kết quả đó
    with _cache_lock:
        if session_id not in VECTORSTORE_CACHE:
            VECTORSTORE_CACHE[session_id] = vectorstore
        else:
            vectorstore = VECTORSTORE_CACHE[session_id]
    return vectorstore


def evict_session(session_id: str) -> None:
    """Xoá session khỏi RAM cache (gọi khi DELETE /v1/sessions/{id})."""
    with _cache_lock:
        if session_id in VECTORSTORE_CACHE:
            del VECTORSTORE_CACHE[session_id]
            logger.info(f"Đã xoá cache session='{session_id}'.")
