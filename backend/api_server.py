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


def _contains_table_block(lines: list[str]) -> bool:
    has_pipe_rows = any(line.strip().startswith("|") and line.strip().endswith("|") for line in lines)
    has_sep = any("---" in line and "|" in line for line in lines)
    return has_pipe_rows and has_sep


def _table_to_bullets(lines: list[str]) -> list[str]:
    rows = [line.strip() for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(rows) < 3:
        return lines

    # Skip header + separator and convert data rows to bullets.
    bullet_rows = []
    for row in rows[2:]:
        cols = [cell.strip() for cell in row.strip("|").split("|") if cell.strip()]
        if cols:
            bullet_rows.append(f"- {' | '.join(cols)}")

    return bullet_rows if bullet_rows else lines


def _normalize_response_text(text: str) -> str:
    lines = text.splitlines()
    if not _contains_table_block(lines):
        return text

    output_lines: list[str] = []
    block: list[str] = []

    def flush_block() -> None:
        nonlocal block
        if not block:
            return
        if _contains_table_block(block):
            output_lines.extend(_table_to_bullets(block))
        else:
            output_lines.extend(block)
        block = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            block.append(line)
            continue
        if block and ("---" in stripped and "|" in stripped):
            block.append(line)
            continue
        flush_block()
        output_lines.append(line)

    flush_block()
    return "\n".join(output_lines)


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    content: str
    session_id: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


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
        bot_response = _normalize_response_text(_extract_text(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    return ChatResponse(content=bot_response, session_id=session_id)
