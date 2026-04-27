# Project Documentation: Local Business Assist

## 1. Project Overview

Local Business Assist is a full-stack conversational application that helps users discover local businesses (food spots, PG accommodations, shops, pubs, etc.) and get review-informed summaries.

The system combines:
- A React frontend for chat UX
- A FastAPI backend for HTTP APIs
- A LangChain agent for orchestration
- MCP (Model Context Protocol) client/server for tool execution boundaries
- External business data APIs (OpenWebNinja endpoints)

The main objective is practical, real-time, decision-support output with a production-like architecture and maintainable code organization.

---

## 2. Why We Chose Hybrid LangChain + MCP

### 2.1 What Hybrid Means Here

Hybrid means:
- LangChain is used for agent orchestration (reasoning, tool selection, conversation state handling).
- MCP is used as the tool execution boundary (a clean protocol layer between the agent and data-fetching tool implementations).

In this project:
- LangChain agent sits in `backend/agent/agent.py`
- MCP client wrappers sit in `backend/mcp_client/mcp_client.py`
- MCP server tools sit in `backend/mcp_server/mcp_server.py`

### 2.2 Why Not Only LangChain

Only-LangChain approach can work for smaller projects, but here it would tightly couple:
- tool implementation details,
- external API handling,
- and agent orchestration.

That makes modular growth harder if you later:
- add more tools,
- split services,
- reuse tools from another app.

### 2.3 Why Not Only MCP

Only-MCP with manual chat loop is possible, but then you must hand-build:
- tool-call reasoning loop,
- retries/robust orchestration,
- output control strategy.

This quickly adds complexity and maintenance load for behavior LangChain already solves well.

### 2.4 Hybrid Benefits in This Project

- Clear separation of concerns
- Reusable tool protocol boundary
- Easier extension for future tools
- Better maintainability for team-style codebases
- Faster iteration with less orchestration boilerplate

---

## 3. Why We Use Direct APIs Instead of Building RAG First

### 3.1 Nature of Data in This Use Case

This project depends on fresh, external business/review data. The source of truth is API-driven and dynamic.

For this type of problem, direct retrieval from APIs is often the most accurate first approach.

### 3.2 Practical Reasons We Did Not Start with RAG

- Faster to implement and validate
- Lower complexity for MVP
- No vector infrastructure management
- No ingestion/index maintenance
- Lower mismatch risk between indexed data and current real-world data

### 3.3 RAG Disadvantages for This Project (At This Stage)

RAG is powerful, but in this specific project it introduces disadvantages early:

1. Data freshness risk
- Indexed vectors can become stale quickly for local business/review content.

2. More moving parts
- Chunking, embedding model choice, index updates, retrieval tuning, reranking.

3. Cost overhead
- Embedding and indexing pipelines add compute/storage overhead.

4. Operational burden
- Rebuild/reindex strategy, schema changes, and drift monitoring.

5. Quality variance on short/noisy review data
- Many reviews are short/noisy; retrieval quality may not justify extra complexity at current scale.

### 3.4 When RAG Would Be Worth Adding

RAG becomes valuable if/when:
- You store large historical review corpora,
- You ingest internal documents (pricing sheets, policies, SOPs, amenities docs),
- You need semantic retrieval across mixed, long-lived knowledge sources.

---

## 4. End-to-End Architecture and Request Flow

## 4.1 High-Level Components

- Frontend (React/Vite): `frontend/src/App.jsx`
- Backend API (FastAPI): `backend/api_server.py`
- Agent (LangChain + Groq): `backend/agent/agent.py`
- MCP Client wrappers: `backend/mcp_client/mcp_client.py`
- MCP Server tool host: `backend/mcp_server/mcp_server.py`
- External API adapters: `backend/mcp_server/tools/local_bussiness_tools.py`

## 4.2 Runtime Flow (One Chat Request)

1. User submits message in frontend.
2. Frontend sends `POST /chat` with:
   - `content`
   - `session_id`
3. FastAPI endpoint validates input and ensures session id.
4. Backend agent processes user message.
5. Agent decides to call tool(s) if needed.
6. Tool call is routed via MCP client wrapper.
7. MCP client starts/connects stdio MCP server process.
8. MCP server executes tool implementation.
9. Tool implementation calls external business/review API.
10. Tool returns structured JSON payload to MCP client.
11. Agent uses tool output to generate final natural-language response.
12. FastAPI normalizes output formatting safeguards (table-to-bullets fallback) and returns response.
13. Frontend renders response with markdown formatting.

---

## 5. Code Walkthrough with Detailed Snippets

## 5.1 FastAPI Chat Contract

From `backend/api_server.py`:

```python
class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None

class ChatResponse(BaseModel):
    content: str
    session_id: str
```

Why this matters:
- Enforces request shape
- Guards against empty/oversized payloads
- Keeps session continuity explicit

Endpoint behavior:

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    user_text = request.content.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")
```

- Clean validation path and explicit 400 for empty content.

Agent invocation pattern:

```python
result = await asyncio.to_thread(
    loaded_agent.invoke,
    {"messages": [{"role": "user", "content": user_text}]},
    {"configurable": {"thread_id": session_id}},
)
```

- `asyncio.to_thread` prevents blocking event loop while agent runs.
- `thread_id` preserves conversation continuity.

---

## 5.2 Agent Configuration (LangChain Layer)

From `backend/agent/agent.py`:

```python
model = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    max_retries=2,
    api_key=os.getenv("GROQ_API_KEY"),
)

agent = create_agent(
    model=model,
    tools=[get_loca_bussiness_data_tool, get_business_reviews_tool],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=memory,
)
```

What this gives:
- Pluggable model selection via env
- Explicit tool registry
- Prompt-driven behavior control
- Memory/checkpoint support via thread-based config

---

## 5.3 MCP Client Wrappers (Tool Adapter Layer)

From `backend/mcp_client/mcp_client.py`:

```python
SERVER_SCRIPT = Path(__file__).resolve().parent.parent / "mcp_server" / "mcp_server.py"
```

- Absolute/derived path avoids brittle CWD assumptions.

Tool wrappers:

```python
@tool("get_bussiness")
def get_loca_bussiness_data_tool(query: str) -> str:
    return get_loca_bussiness_data(query)

@tool("get_business_reviews")
def get_business_reviews_tool(...):
    return get_business_reviews(...)
```

- LangChain sees these as tools.
- Actual execution goes through MCP session calls.

Robust business id normalization:

```python
def _normalize_business_id(business_id: str | Sequence[str]) -> str:
    ...
```

- Handles model variability (`"id"` vs `["id"]`) safely.

---

## 5.4 MCP Server and Tool Implementations

From `backend/mcp_server/mcp_server.py`:

```python
@mcp.tool(name="get_local_business_data")
def get_local_business_data(query: str) -> str:
    return fetch_local_business_data(query)
```

```python
@mcp.tool(name="get_business_reviews_by_id")
def get_business_reviews_by_id(...):
    return fetch_business_reviews_by_id(...)
```

From `backend/mcp_server/tools/local_bussiness_tools.py`:
- `fetch_local_business_data(...)`
- `fetch_business_reviews_by_id(...)`

These functions:
- Validate required API key
- Call external HTTP endpoints
- Normalize response payload fields
- Limit review text size to control downstream token load

---

## 5.5 Frontend Chat UX

From `frontend/src/App.jsx`:
- Maintains local message history
- Sends HTTP requests to backend
- Handles loading states and progress labels
- Supports Enter-to-send
- Supports New Chat reset
- Renders markdown safely for better readability

The frontend is intentionally decoupled from backend internals and only depends on API contract.

---

## 6. Error Handling and Edge Cases Covered

Current coverage includes:
- Empty chat messages -> explicit 400
- Invalid/empty business id in tool layer -> clear validation error
- External API request failures -> propagated with explicit error context
- Model/tool mismatch for `business_id` list/string -> normalized
- Unexpected markdown table output -> converted to bullet format fallback
- Connectivity failures in frontend -> shown as user-visible error message

---

## 7. Performance and Efficiency Notes

For current scope, performance is reasonable because:
- API-first retrieval avoids heavy indexing pipelines
- Review text length is capped
- MCP tool boundary keeps execution focused
- Async endpoint offloads blocking agent invoke work using thread execution

Potential future optimizations:
- Add short-lived caching for repeated business_id lookups
- Add response streaming if needed
- Add request timeout wrappers and backoff policies

---

## 8. Testability and Validation

Basic validation/testing strategy expected:
- Unit tests for helper logic (normalization, table conversion, validation rules)
- API contract tests for `/health` and `/chat`
- Smoke test for import/run modes (`backend.api_server:app` and `api_server:app`)

If tests are added, run with:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 9. Runbook (End-to-End)

1. Install backend dependencies

```bash
pip install -r requirements.txt
```

2. Configure root `.env`

```env
GROQ_API_KEY=...
RAPIDAPI_KEY=...
GROQ_MODEL=openai/gpt-oss-120b
```

3. Run backend

From project root:

```bash
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```

4. Configure frontend API URL

`frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

5. Run frontend

```bash
cd frontend
npm install
npm run dev
```

6. Open app in browser (`http://localhost:5173` typically)

---

## 10. Summary of Design Choices

- Chosen architecture is intentionally production-oriented (separate frontend/backend + modular backend packages).
- Hybrid LangChain + MCP balances orchestration convenience and protocol-based modularity.
- Direct API retrieval is the right initial strategy for freshness and complexity control.
- RAG is deferred intentionally due to operational overhead and limited payoff for current data shape/scope.

This gives a system that is practical, modular, testable, and ready for iterative enhancement.
