"""
=============================================================
 LESSON 4: MEMORY & PERSISTENCE (Context Providers)
=============================================================

Session vs. Memory:
-------------------
In Lesson 3, sessions gave the agent conversation history.
But that history is just raw messages — the agent replays them every time.

Context Providers are smarter. They can:
- Extract key facts from conversations (e.g. user's name)
- Store them in session state (a dictionary)
- Inject personalized instructions on every turn

Think of it like this:
- Session = raw chat transcript (everything said)
- Context Provider = personal notebook (extracted key facts)

How it works:
1. before_run(): Runs BEFORE the LLM call. Injects context into the prompt.
2. after_run(): Runs AFTER the LLM call. Extracts and stores facts from the conversation.

  Turn 1: User says "My name is Vinay"
    → after_run() extracts "Vinay" and stores it in session state
  Turn 2: User asks anything
    → before_run() sees name="Vinay" in state, injects "Address this user as Vinay"

Key Concepts:
- ContextProvider: Base class for custom memory logic
- before_run(): Hook that runs before each LLM call (read state → inject context)
- after_run(): Hook that runs after each LLM call (read messages → update state)
- session.state: A dictionary that persists across turns within a session
- context.extend_instructions(): Adds extra instructions to the prompt dynamically

Run:  .venv/bin/python 04_memory.py
Docs: https://learn.microsoft.com/en-us/agent-framework/get-started/memory
=============================================================
"""

import os
import asyncio
from typing import Any
from dotenv import load_dotenv

load_dotenv(override=True)

from agent_framework import Agent, AgentSession, ContextProvider, SessionContext
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

# ── Config ──────────────────────────────────────────────────
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1")


# ── Custom Context Provider ─────────────────────────────────
#   This is YOUR custom memory logic.
#   It extracts the user's name from conversation and remembers it.

class UserMemoryProvider(ContextProvider):
    """A context provider that remembers user info in session state."""

    DEFAULT_SOURCE_ID = "user_memory"

    def __init__(self):
        super().__init__(self.DEFAULT_SOURCE_ID)

    async def before_run(
        self,
        *,
        agent: Any,
        session: AgentSession | None,
        context: SessionContext,
        state: dict[str, Any],
    ) -> None:
        """
        Runs BEFORE each LLM call.
        Reads from state and injects personalized instructions.
        """
        user_name = state.get("user_name")
        if user_name:
            # We know the user's name — tell the LLM to use it
            context.extend_instructions(
                self.source_id,
                f"The user's name is {user_name}. Always address them by name.",
            )
            print(f"  [Memory] Injecting: user_name={user_name}")
        else:
            # We don't know the name yet — ask for it
            context.extend_instructions(
                self.source_id,
                "You don't know the user's name yet. Ask for it politely.",
            )
            print("  [Memory] No user name stored yet")

    async def after_run(
        self,
        *,
        agent: Any,
        session: AgentSession | None,
        context: SessionContext,
        state: dict[str, Any],
    ) -> None:
        """
        Runs AFTER each LLM call.
        Scans messages for "my name is ..." and stores the name.
        """
        for msg in context.input_messages:
            text = msg.text if hasattr(msg, "text") else ""
            if isinstance(text, str) and "my name is" in text.lower():
                name = text.lower().split("my name is")[-1].strip().split()[0].capitalize()
                state["user_name"] = name
                print(f"  [Memory] Extracted and stored: user_name={name}")


# ── Create Agent with the Context Provider ──────────────────
client = FoundryChatClient(
    project_endpoint=PROJECT_ENDPOINT,
    model=MODEL_DEPLOYMENT_NAME,
    credential=DefaultAzureCredential(),
)

agent = Agent(
    client=client,
    name="MemoryAgent",
    instructions="You are a friendly assistant.",
    # This is where you plug in your context provider(s)
    context_providers=[UserMemoryProvider()],
)


async def main():
    session = agent.create_session()

    # Turn 1: Agent doesn't know us yet — should ask for name
    print(f"\n{'─' * 50}")
    print("Turn 1: Hello! What's the square root of 9?")
    result = await agent.run("Hello! What's the square root of 9?", session=session)
    print(f"Agent: {result}")

    # Turn 2: We tell it our name — after_run() will extract and store it
    print(f"\n{'─' * 50}")
    print("Turn 2: My name is Vinay")
    result = await agent.run("My name is Vinay", session=session)
    print(f"Agent: {result}")

    # Turn 3: Agent should now address us by name (injected by before_run())
    print(f"\n{'─' * 50}")
    print("Turn 3: What is 2 + 2?")
    result = await agent.run("What is 2 + 2?", session=session)
    print(f"Agent: {result}")

    # Inspect what's stored in session state
    provider_state = session.state.get("user_memory", {})
    print(f"\n{'═' * 50}")
    print(f"Session State: {provider_state}")
    print(f"Stored user name: {provider_state.get('user_name')}")


if __name__ == "__main__":
    asyncio.run(main())
