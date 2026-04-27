import asyncio
import uuid
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(title="Local Business Assist HTTP API")

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
        result = await asyncio.to_thread(
            loaded_agent.invoke,
            {"messages": [{"role": "user", "content": user_text}]},
            {"configurable": {"thread_id": session_id}},
        )
        bot_response = _extract_text(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    return ChatResponse(content=bot_response, session_id=session_id)
