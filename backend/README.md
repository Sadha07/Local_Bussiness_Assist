# Backend

## Purpose

FastAPI service that exposes chat API endpoints and routes user requests through LangChain agent + MCP tools.

## Main Modules

- `api_server.py`: HTTP API (`/health`, `/chat`)
- `agent/agent.py`: model + tool orchestration
- `agent/prompt.py`: system behavior instructions
- `mcp_client/mcp_client.py`: MCP client wrappers as tools
- `mcp_server/mcp_server.py`: MCP tool host
- `mcp_server/tools/local_bussiness_tools.py`: external data access layer

## Run

From project root:

```bash
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```

From backend folder:

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

## Notes

- Agent import is lazy-loaded in `api_server.py` for better startup/test behavior.
- MCP server path is resolved via absolute file path in `mcp_client.py`.
