import asyncio
import uuid
from collections import defaultdict
from functools import lru_cache
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(title="Local Business Assist HTTP API")

# Keep a compact rolling context per session to avoid model token overflow.
MAX_CONTEXT_MESSAGES = 6
MAX_MESSAGE_CHARS = 1200
MAX_CONTEXT_TOTAL_CHARS = 4500
_SESSION_HISTORY: dict[str, list[dict[str, str]]] = defaultdict(list)
_SESSION_HISTORY_LOCK = Lock()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Lazy-load the agent so API module import stays lightweight and test-friendly.
@lru_cache(maxsize=1)
def _load_agent():
    """Lazily import and cache the LangChain agent instance.

    This keeps module import lightweight for tests and avoids import path issues
    during startup until the first chat request arrives.
    """
    try:
        # Works when launched as package: uvicorn backend.api_server:app
        from .agent.agent import agent as loaded_agent
    except ImportError:
        # Works when launched from backend folder: uvicorn api_server:app
        from agent.agent import agent as loaded_agent
    return loaded_agent


def _extract_text(result: object) -> str:
    if isinstance(result, dict):
        messages = result.get("messages", [])
        if messages:
            content = messages[-1].content
            return content if isinstance(content, str) else str(content)
    return str(result)


def _clip_text(text: str, limit: int) -> str:
    clipped = text.strip()
    return clipped[:limit] if len(clipped) > limit else clipped


def _prune_history(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    # Keep the latest message window first.
    window = messages[-MAX_CONTEXT_MESSAGES:]

    # Then enforce an overall character budget from newest to oldest.
    kept_reversed: list[dict[str, str]] = []
    running_chars = 0
    for msg in reversed(window):
        content = msg.get("content", "")
        if running_chars + len(content) > MAX_CONTEXT_TOTAL_CHARS:
            continue
        kept_reversed.append(msg)
        running_chars += len(content)

    kept_reversed.reverse()
    return kept_reversed


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    content: str
    session_id: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# Main chat endpoint: validates request and returns model output as markdown.
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    user_text = request.content.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    session_id = request.session_id or f"local-business-{uuid.uuid4()}"
    try:
        loaded_agent = _load_agent()

        with _SESSION_HISTORY_LOCK:
            history = _SESSION_HISTORY[session_id]
            history.append({"role": "user", "content": _clip_text(user_text, MAX_MESSAGE_CHARS)})
            model_messages = _prune_history(history)

        result = await asyncio.to_thread(
            loaded_agent.invoke,
            {"messages": model_messages},
        )
        bot_response = _extract_text(result)

        with _SESSION_HISTORY_LOCK:
            history = _SESSION_HISTORY[session_id]
            history.append({"role": "assistant", "content": _clip_text(bot_response, MAX_MESSAGE_CHARS)})
            _SESSION_HISTORY[session_id] = _prune_history(history)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    return ChatResponse(content=bot_response, session_id=session_id)
