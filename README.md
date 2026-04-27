# Local Business Assist

Full-stack AI assistant for discovering local businesses (food, PG, shops), fetching review data, and returning concise summaries.

## What This Project Includes

- Proper backend/frontend architecture (no Streamlit shortcut in main path)
- Backend API: FastAPI HTTP service
- Agent orchestration: LangChain + Groq model
- Tool integration: MCP client/server for business search + review fetching
- Frontend: React + Vite chat UI
- Basic tests for core normalization and validation behavior

## Architecture Overview

```text
frontend (React)
  -> POST /chat
backend/api_server.py (FastAPI)
  -> backend/agent/agent.py (LangChain agent)
  -> backend/mcp_client/mcp_client.py (MCP client tools)
  -> backend/mcp_server/mcp_server.py (MCP tools server)
  -> backend/mcp_server/tools/local_bussiness_tools.py (external API calls)
```

## Folder Structure

```text
backend/
  api_server.py
  agent/
    agent.py
    prompt.py
  mcp_client/
    mcp_client.py
  mcp_server/
    mcp_server.py
    tools/
      local_bussiness_tools.py
frontend/
  src/
  package.json
tests/
requirements.txt
```

## Setup

### 1) Backend dependencies

```bash
pip install -r requirements.txt
```

### 2) Frontend dependencies

```bash
cd frontend
npm install
```

### 3) Environment variables

Create `.env` in project root with:

```env
GROQ_API_KEY=your_groq_key
RAPIDAPI_KEY=your_openwebninja_key
GROQ_MODEL=openai/gpt-oss-120b
```

Optional:

```env
RAPIDAPI_HOST=local-business-data.p.rapidapi.com
```

### 4) Frontend API URL

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## Run (End-to-End)

### Terminal 1 (backend)

From project root:

```bash
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 (frontend)

```bash
cd frontend
npm run dev
```

Open Vite URL (usually `http://localhost:5173`).

## Usage

1. Ask for category + location (e.g., "best women PG in Velachery")
2. Assistant lists options
3. Ask for a specific place to get review-based summary

## Testing

Run basic unit tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Error Handling and Edge Coverage

- Empty user content rejected with 400
- Oversized content constrained with request schema
- Agent runtime failures return 500 with explicit detail
- `business_id` accepts both string and list, normalized safely
- Markdown table output normalized to readable bullets

## Git Hygiene

Repository includes `.gitignore` for Python and Node artifacts (`__pycache__`, `node_modules`, `.env`, etc.).
