import asyncio
import sys
from pathlib import Path
from typing import Sequence

from langchain.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = Path(__file__).resolve().parent.parent / "mcp_server" / "mcp_server.py"


# Input normalization for LLM tool-call variability.
def _normalize_business_id(business_id: str | Sequence[str]) -> str:
    if isinstance(business_id, str):
        normalized = business_id.strip()
        if normalized:
            return normalized
        raise ValueError("business_id must be a non-empty string or list of strings.")
    if isinstance(business_id, Sequence) and business_id:
        first = business_id[0]
        if isinstance(first, str):
            normalized = first.strip()
        else:
            normalized = str(first).strip()
        if normalized:
            return normalized
    raise ValueError("business_id must be a non-empty string or list of strings.")


async def _call_local_business_tool(query: str) -> str:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
    )

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_local_business_data",
                {"query": query},
            )

    if hasattr(result, "content") and result.content:
        content = result.content[0]
        if hasattr(content, "text"):
            return content.text

    return str(result)


# Shared MCP invocation wrapper for review-by-business-id calls.
async def _call_business_reviews_tool(
    business_id: str,
    limit: int = 30,
    sort_by: str = "most_relevant",
    language: str = "en",
    max_chars_per_review: int = 400,
) -> str:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
    )

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_business_reviews_by_id",
                {
                    "business_id": business_id,
                    "limit": limit,
                    "sort_by": sort_by,
                    "language": language,
                    "max_chars_per_review": max_chars_per_review,
                },
            )

    if hasattr(result, "content") and result.content:
        content = result.content[0]
        if hasattr(content, "text"):
            return content.text

    return str(result)


def get_loca_bussiness_data(query: str) -> str:
    """Proxy local business search to the MCP server."""
    return asyncio.run(_call_local_business_tool(query))


def get_business_reviews(
    business_id: str | Sequence[str],
    limit: int = 30,
    sort_by: str = "most_relevant",
    language: str = "en",
    max_chars_per_review: int = 400,
) -> str:
    """Proxy business review search to the MCP server."""
    normalized_business_id = _normalize_business_id(business_id)
    return asyncio.run(
        _call_business_reviews_tool(
            business_id=normalized_business_id,
            limit=limit,
            sort_by=sort_by,
            language=language,
            max_chars_per_review=max_chars_per_review,
        )
    )


@tool("get_bussiness")
def get_loca_bussiness_data_tool(query: str) -> str:
    """LangChain-compatible tool wrapper for MCP local business search."""
    return get_loca_bussiness_data(query)


@tool("get_business_reviews")
def get_business_reviews_tool(
    business_id: str | list[str],
    limit: int = 30,
    sort_by: str = "most_relevant",
    language: str = "en",
    max_chars_per_review: int = 400,
) -> str:
    """LangChain-compatible tool wrapper to fetch reviews by business id."""
    return get_business_reviews(
        business_id=business_id,
        limit=limit,
        sort_by=sort_by,
        language=language,
        max_chars_per_review=max_chars_per_review,
    )
