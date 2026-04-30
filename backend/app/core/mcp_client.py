import requests
import json
from agents.mcp import MCPServerSse, MCPServerStreamableHttp
from agents import Agent, Runner, trace
from typing import Optional


HTTP_URL = "https://order-mcp-74afyau24q-uc.a.run.app/mcp"

instructions = "You are an agent that uses MCP tools to answer queries."
model = "gpt-4.1"
request = "Please check the tools provided by the Meridian Electronics MCP server and summarize their capabilities."

async def get_mcp_server(url: str) -> Optional[MCPServerStreamableHttp]:
    try:
        return MCPServerStreamableHttp(name="Meridian Electronics", params={"url": url})
    except Exception as e:
        print("Error connecting to MCP server:", e)
        return None