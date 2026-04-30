from contextlib import AsyncExitStack
from typing import Any
import re
import string
import secrets
from agents import Agent, Runner, trace

from app.core.mcp_client import HTTP_URL, get_mcp_server    
from app.core.customer import get_customer_tool

MAX_TURNS = 25
ALPHANUM = string.ascii_lowercase + string.digits 
INSTRUCTIONS = (
    "You are a helpful customer support assistant. Please use the tools "
    "provided to you to answer the user's queries."
)

def make_trace_id(tag: str) -> str:
    """
    Return a string of the form 'trace_<tag><random>',
    where the total length after 'trace_' is 32 chars.
    """
    safe_tag = re.sub(r"[^a-zA-Z0-9_-]", "_", tag).lower().strip("_")
    if not safe_tag:
        safe_tag = "support"
    tag_part = f"{safe_tag}_"
    if len(tag_part) > 32:
        tag_part = tag_part[:32]
    pad_len = max(0, 32 - len(tag_part))
    random_suffix = ''.join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag_part}{random_suffix}"

class Support:
    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        self.name = name
        self.model_name = model_name

    async def create_agent(self, support_mcp_servers: list[Any]) -> Agent:
        tool = await get_customer_tool(support_mcp_servers, self.model_name)
        return Agent(
            name=self.name,
            instructions=INSTRUCTIONS,
            model=self.model_name,
            tools=[tool],
            mcp_servers=support_mcp_servers,
        )

    async def run_chat(self, messages: list[dict[str, str]]):
        trace_name = f"{self.name}-support"
        trace_id = make_trace_id(self.name.lower())

        with trace(trace_name, trace_id=trace_id):
            async with AsyncExitStack() as stack:
                support_server = await get_mcp_server(HTTP_URL)
                if support_server is None:
                    raise RuntimeError("Could not connect to the Support MCP server.")
                support_mcp_servers = [await stack.enter_async_context(support_server)]
                agent = await self.create_agent(support_mcp_servers)
                return await Runner.run(agent, messages, max_turns=MAX_TURNS)
