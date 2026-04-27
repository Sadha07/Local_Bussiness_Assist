import os

import dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq

try:
    # Works when imported as backend.agent.agent
    from ..mcp_client.mcp_client import get_business_reviews_tool, get_loca_bussiness_data_tool
except ImportError:
    # Works when imported as agent.agent from backend cwd
    from mcp_client.mcp_client import get_business_reviews_tool, get_loca_bussiness_data_tool

from .prompt import SYSTEM_PROMPT

dotenv.load_dotenv()

model = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    max_retries=2,
    api_key=os.getenv("GROQ_API_KEY"),
)

agent = create_agent(
    model=model,
    tools=[get_loca_bussiness_data_tool, get_business_reviews_tool],
    system_prompt=SYSTEM_PROMPT,
)
