import dotenv
from mcp.server.fastmcp import FastMCP

try:
    # Works when imported as package module.
    from .tools.local_bussiness_tools_rapid import fetch_business_reviews_by_id, fetch_local_business_data
except ImportError:
    # Works when executed directly as a script.
    from tools.local_bussiness_tools_rapid import fetch_business_reviews_by_id, fetch_local_business_data

dotenv.load_dotenv()

mcp = FastMCP("local-business-server")


@mcp.tool(name="get_local_business_data")
def get_local_business_data(query: str) -> str:
    """Search local businesses and reviews for the given query."""
    return fetch_local_business_data(query)


@mcp.tool(name="get_business_reviews_by_id")
def get_business_reviews_by_id(
    business_id: str,
    limit: int = 20,
    sort_by: str = "most_relevant",
    language: str = "en",
    max_chars_per_review: int = 400,
) -> str:
    """Fetch review texts for a business id with token-safe trimming."""
    return fetch_business_reviews_by_id(
        business_id=business_id,
        limit=limit,
        sort_by=sort_by,
        language=language,
        max_chars_per_review=max_chars_per_review,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
