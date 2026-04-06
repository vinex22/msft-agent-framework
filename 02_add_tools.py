"""
=============================================================
 LESSON 2: ADD TOOLS
=============================================================

Why tools?
----------
A plain agent can only TALK. It knows things from its training data,
but it can't DO things — it can't check the weather, query a database,
or call an API. Tools fix that.

How tools work:
1. You write a normal Python function.
2. You decorate it with @tool.
3. You give it to the agent.
4. The LLM decides WHEN to call your function based on the user's question.

  User: "What's the weather in Tokyo?"
    ↓
  LLM thinks: "I need the get_weather tool for this"
    ↓
  Agent calls YOUR get_weather("Tokyo") function
    ↓
  Your function returns "Sunny, 25°C"
    ↓
  LLM formats a nice response: "It's sunny and 25°C in Tokyo!"

The LLM never runs your code — it just decides to call it.
YOUR code runs on YOUR machine/server.

Key Concepts:
- @tool decorator: Marks a function as available to the agent
- Type hints + docstrings: The LLM reads these to understand what the tool does
- tools=[...]: Pass your tools when creating the agent
- approval_mode: Controls whether the user must approve tool calls

Run:  .venv/bin/python 02_add_tools.py
Docs: https://learn.microsoft.com/en-us/agent-framework/get-started/add-tools
=============================================================
"""

import os
import asyncio
from random import randint
from typing import Annotated
from dotenv import load_dotenv

load_dotenv(override=True)

from pydantic import Field
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

# ── Config ──────────────────────────────────────────────────
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")


# ── Define Tools ────────────────────────────────────────────
#   These are NORMAL Python functions. The @tool decorator tells
#   the Agent Framework to expose them to the LLM.
#
#   IMPORTANT: The docstring and parameter descriptions are what
#   the LLM reads to decide when/how to call the tool.
#   Good descriptions = better tool usage.

@tool
def get_weather(
    location: Annotated[str, Field(description="The city or location to get weather for.")],
) -> str:
    """Get the current weather for a given location."""
    # In real life, you'd call a weather API here.
    # This is a fake implementation for learning.
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


@tool
def calculate(
    expression: Annotated[str, Field(description="A math expression like '2 + 2' or '(100 * 1.1) / 3'")],
) -> str:
    """Safely evaluate a math expression."""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: Only numbers and +-*/.() are allowed"
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


# ── Create the Agent with tools ─────────────────────────────
#   Notice tools=[get_weather, calculate] — this is how you
#   "give" the tools to the agent.
client = FoundryChatClient(
    project_endpoint=PROJECT_ENDPOINT,
    model=MODEL_DEPLOYMENT_NAME,
    credential=DefaultAzureCredential(),
)

agent = Agent(
    client=client,
    name="ToolAgent",
    instructions="""You are a helpful assistant with two abilities:
    1. Check the weather in any city (use the get_weather tool) and always use emoji in responses about weather 🌤️🌧️.⛈️
    2. Do math calculations (use the calculate tool)
    Always use your tools when relevant. Be concise.""",
    tools=[get_weather, calculate],
)


async def main():
    questions = [
        # This should trigger the get_weather tool
        "What's the weather like in all the 28 capitals of states in India?",
        # This should trigger the calculate tool
        "If a pizza costs $12.50 and I want to split it among 3 people, how much does each pay?",
        # This should NOT trigger any tool — just the LLM's knowledge
        "Who wrote Romeo and Juliet?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'─' * 50}")
        print(f"Question {i}: {question}")
        result = await agent.run(question)
        print(f"Agent: {result}")


if __name__ == "__main__":
    asyncio.run(main())
