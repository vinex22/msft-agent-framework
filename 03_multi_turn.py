"""
=============================================================
 LESSON 3: MULTI-TURN CONVERSATIONS
=============================================================

The problem:
------------
In Lesson 1, each agent.run() was independent — the agent had no
memory of previous questions. It's like talking to someone with
amnesia every time.

  Turn 1: "My name is Vinay"  → Agent: "Nice to meet you, Vinay!"
  Turn 2: "What's my name?"   → Agent: "I don't know your name."  ← BAD

The solution: Sessions
----------------------
A Session is a container that holds conversation history.
When you pass a session to agent.run(), the agent can see
everything said before.

  session = agent.create_session()

  Turn 1: agent.run("My name is Vinay", session=session)
    → Session now contains: [user: "My name is Vinay", assistant: "Nice to meet you!"]

  Turn 2: agent.run("What's my name?", session=session)
    → Agent sees the full history → "Your name is Vinay!"  ← GOOD

Key Concepts:
- AgentSession: Holds conversation history in memory
- agent.create_session(): Creates a new session
- session=session: Pass it to every agent.run() call
- Same session = continuous conversation
- New session = fresh start (no memory)

Run:  .venv/bin/python 03_multi_turn.py
Docs: https://learn.microsoft.com/en-us/agent-framework/get-started/multi-turn
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

# ── Create the Agent ────────────────────────────────────────
client = FoundryChatClient(
    project_endpoint=PROJECT_ENDPOINT,
    model=MODEL_DEPLOYMENT_NAME,
    credential=DefaultAzureCredential(),
)

agent = Agent(
    client=client,
    name="ConversationAgent",
    instructions="You are a friendly assistant. Keep your answers brief.",
)


async def main():
    # ── Create a session ────────────────────────────────────
    #   This is the "memory" for our conversation.
    session = agent.create_session()

    # ── Multi-turn conversation ─────────────────────────────
    #   Each turn builds on the previous one because they share a session.
    turns = [
        "My name is Vinay and I love building AI agents.",
        "What do you remember about me?",
        "Based on my interests, suggest a fun weekend project.",
    ]

    for i, message in enumerate(turns, 1):
        print(f"\n{'─' * 50}")
        print(f"Turn {i}: {message}")

        # Pass session= to maintain conversation context
        result = await agent.run(message, session=session)
        print(f"Agent: {result}")

    # ── Without a session (no memory) ───────────────────────
    #   This shows what happens WITHOUT a session — the agent
    #   has no idea what was said before.
    print(f"\n{'═' * 50}")
    print("WITHOUT SESSION (fresh start, no memory):")
    print("═" * 50)

    result = await agent.run("What do you remember about me?")
    print(f"Agent: {result}")


if __name__ == "__main__":
    asyncio.run(main())
