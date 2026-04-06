"""
=============================================================
 LESSON 1: YOUR FIRST AGENT
=============================================================

What is an AI Agent?
--------------------
Think of an agent as a smart assistant you build. At its simplest:

  YOU  →  give it instructions  →  AGENT  →  talks to an LLM  →  RESPONSE

An LLM (Large Language Model) like GPT is the "brain".
The Agent Framework is the "body" — it connects your code to that brain.

Key Concepts:
- Agent: Your assistant. It has instructions (personality/rules) and a client (connection to the LLM).
- Client: The bridge between your agent and the LLM service (Azure AI Foundry).
- Instructions: A system prompt telling the agent how to behave.
- run(): Send a question, get an answer.
- stream=True: Get the answer word-by-word as it's generated (like ChatGPT typing).

What you'll learn:
1. How to create a basic agent
2. How to get a complete response
3. How to stream a response token-by-token

Run:  .venv/bin/python 01_first_agent.py
Docs: https://learn.microsoft.com/en-us/agent-framework/get-started/your-first-agent
=============================================================
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

# ── Config ──────────────────────────────────────────────────
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")

# ── Step 1: Create a client (the bridge to the LLM) ─────────
#   FoundryChatClient connects to Azure AI Foundry.
#   - project_endpoint: WHERE your LLM lives (your Foundry project URL)
#   - model: WHICH LLM to use (e.g. gpt-4.1, gpt-5.4)
#   - credential: HOW to authenticate (DefaultAzureCredential uses your `az login`)
client = FoundryChatClient(
    project_endpoint=PROJECT_ENDPOINT,
    model=MODEL_DEPLOYMENT_NAME,
    credential=DefaultAzureCredential(),
)

# ── Step 2: Create the agent ────────────────────────────────
#   The Agent combines:
#   - client: the LLM connection
#   - name: a label for your agent
#   - instructions: the "system prompt" — tells the agent who it is and how to behave
agent = Agent(
    client=client,
    name="HelloAgent",
    instructions="You are a friendly assistant. Keep your answers brief and fun.",
)


async def main():
    # ── Step 3a: Non-streaming — get the complete response at once ──
    #   Like sending a text message and waiting for the full reply.
    print("=" * 50)
    print("NON-STREAMING (complete response)")
    print("=" * 50)

    result = await agent.run("What is the capital of France?")
    print(f"Agent: {result}")

    # ── Step 3b: Streaming — get tokens as they are generated ───────
    #   Like watching someone type in real-time.
    #   Useful for long responses — user sees output immediately.
    print(f"\n{'=' * 50}")
    print("STREAMING (word by word)")
    print("=" * 50)

    print("Agent: ", end="", flush=True)
    async for chunk in agent.run("Tell me a one-sentence fun fact about space.", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()  # newline at the end


if __name__ == "__main__":
    asyncio.run(main())
