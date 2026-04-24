import os
import dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver  

from local_bussiness_tools import (
    get_loca_bussiness_data
)
from prompt import SYSTEM_PROMPT

dotenv.load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",
    max_retries=2,
    api_key=os.getenv('GROQ_API_KEY')
)

memory = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[
        get_loca_bussiness_data
    ],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=memory
)

