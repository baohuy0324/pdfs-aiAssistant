from collections.abc import Generator
from functools import lru_cache
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from src.core.config import GEMINI_API_KEY, GROQ_API_KEY
from src.core.prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)



@lru_cache(maxsize=1)
def _get_gemini() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.1,
    )


@lru_cache(maxsize=1)
def _get_groq() -> ChatGroq:
    return ChatGroq(
        model_name="llama-3.1-8b-instant",
        groq_api_key=GROQ_API_KEY,
        temperature=0.1,
    )


def ask_gemini(context: str, query: str, chat_history: str = "") -> Generator[str, None, None]:
    """Uses Gemini API for answering the query."""
    prompt = SYSTEM_PROMPT.format(context=context, question=query, chat_history=chat_history)
    for chunk in _get_gemini().stream(prompt):
        yield chunk.content


def ask_groq(context: str, query: str, chat_history: str = "") -> Generator[str, None, None]:
    """Uses Groq API for answering the query."""
    prompt = SYSTEM_PROMPT.format(context=context, question=query, chat_history=chat_history)
    for chunk in _get_groq().stream(prompt):
        yield chunk.content


def ask_llm(context: str, query: str, chat_history: str = "") -> Generator[str, None, None]:
    """
    Router phân xử logic LLM dựa trên độ dài của ngữ cảnh.
    Context ngắn (< 10000 ký tự) thì sử dụng Gemini.
    Context dài (>= 10000 ký tự) thì sử dụng Groq để tính toán.
    """
    if not context or not context.strip():
        yield "Tôi không tìm thấy thông tin trong tài liệu."
        return

    if len(context) < 10000:
        logger.info("LLM Router: Context ngắn (%d chars), dùng Gemini", len(context))
        has_yielded = False
        try:
            for chunk in ask_gemini(context, query, chat_history):
                has_yielded = True
                yield chunk
        except Exception as e:
            if has_yielded:
                logger.warning("Gemini bị ngắt kết nối giữa chừng (%s). Không thể fallback.", e)
                yield "\n\n*(Đã xảy ra lỗi kết nối mạng với mô hình, xin vui lòng gửi lại câu hỏi)*"
            else:
                logger.warning("Gemini lỗi (%s), fallback sang Groq", e)
                yield from ask_groq(context, query, chat_history)
    else:
        logger.info("LLM Router: Context dài (%d chars), dùng Groq", len(context))
        yield from ask_groq(context, query, chat_history)