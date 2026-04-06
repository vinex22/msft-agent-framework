"""
=============================================================
 LESSON 6: HOST YOUR AGENT
=============================================================

Why host?
---------
So far, we've been running agents from the command line.
But in production, other apps/users/agents need to REACH your agent
over a network. That means hosting it as a service.

Hosting Options:
----------------
┌──────────────────────────────┬──────────────────────────────────┐
│ Option                       │ Best for                         │
├──────────────────────────────┼──────────────────────────────────┤
│ DevUI                        │ Local testing in a browser       │
│ A2A Protocol                 │ Agent-to-agent communication     │
│ OpenAI-Compatible Endpoints  │ Apps using OpenAI SDK            │
│ Azure Functions (Durable)    │ Serverless, long-running tasks   │
│ AG-UI Protocol               │ Web frontend AI apps             │
│ Foundry Hosted Agents        │ Managed containers on Azure      │
└──────────────────────────────┴──────────────────────────────────┘

In Python, the simplest hosting options are:

1. DevUI (what we used before):
   pip install agent-framework-devui --pre
   serve(entities=[agent], auto_open=True)

2. Foundry Hosted Agents (Docker container on Azure):
   - See SKILL.md "Deployment Steps" section for full walkthrough

This file demonstrates DevUI hosting — the easiest way to test
your agent with a web UI.

Run:  .venv/bin/python 06_hosting.py
Then: open http://localhost:8080
Docs: https://learn.microsoft.com/en-us/agent-framework/get-started/hosting
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
from agent_framework.devui import serve
from azure.identity import DefaultAzureCredential

# ── Config ──────────────────────────────────────────────────
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")


# ── Tools ───────────────────────────────────────────────────
@tool
def get_weather(
    location: Annotated[str, Field(description="The city to get weather for.")],
) -> str:
    """Get the current weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


# ── Create the Agent ────────────────────────────────────────
client = FoundryChatClient(
    project_endpoint=PROJECT_ENDPOINT,
    model=MODEL_DEPLOYMENT_NAME,
    credential=DefaultAzureCredential(),
)

agent = Agent(
    client=client,
    name="WeatherAgent",
    instructions="You are a helpful weather assistant. Use the get_weather tool to answer questions.",
    tools=[get_weather],
)


# ── Host with DevUI ─────────────────────────────────────────
#   This starts a web server at http://localhost:8080
#   with an interactive UI to chat with your agent.
#
#   It also exposes an OpenAI-compatible API at http://localhost:8080/v1
#   so any app using the OpenAI SDK can talk to your agent:
#
#     from openai import OpenAI
#     client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")
#     response = client.responses.create(
#         metadata={"entity_id": "WeatherAgent"},
#         input="What's the weather in Tokyo?"
#     )

if __name__ == "__main__":
    print("Starting DevUI at http://localhost:8080 ...")
    print("Press Ctrl+C to stop.\n")
    serve(entities=[agent], auto_open=True, port=8080)
