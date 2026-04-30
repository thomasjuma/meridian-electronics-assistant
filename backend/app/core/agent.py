from typing import List, Dict
from agents import Agent, Runner

# Define the agent
chat_agent = Agent(
    name="Support Agent",
    instructions="You are a helpful customer support assistant.",
    model="gpt-4.1-mini"
)

async def agent_chat(messages: List[Dict]) -> str:
    """Chat with the agent"""
    return await Runner.run(chat_agent, messages)