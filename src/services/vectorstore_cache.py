"""
Helper service: xử lý lịch sử chat cho router.
"""
from __future__ import annotations

import logging

from src.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)


def history_to_string(history: list[ChatMessage], max_turns: int = 5) -> str:
    """Chuyển lịch sử chat thành chuỗi text để đưa vào prompt."""
    tail = history[-max_turns:] if len(history) > max_turns else history
    lines: list[str] = []
    for m in tail:
        label = "Người dùng" if m.role == "user" else "Trợ lý AI"
        lines.append(f"{label}: {m.content}")
    return "\n".join(lines)
