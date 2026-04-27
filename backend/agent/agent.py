import os

import dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver

try:
    # Works when imported as backend.agent.agent
    from ..mcp_client.mcp_client import get_business_reviews_tool, get_loca_bussiness_data_tool
except ImportError:
    # Works when imported as agent.agent from backend cwd
    from mcp_client.mcp_client import get_business_reviews_tool, get_loca_bussiness_data_tool

from .prompt import SYSTEM_PROMPT

dotenv.load_dotenv()

model = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    max_retries=2,
    api_key=os.getenv("GROQ_API_KEY"),
)

memory = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[get_loca_bussiness_data_tool, get_business_reviews_tool],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=memory,
)
