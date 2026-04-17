"""
=============================================================
 LESSON 7: MODEL ROUTER
=============================================================

What is model-router?
---------------------
`model-router` is a special Foundry deployment that automatically picks the
best underlying model for each request (e.g. routes simple questions to a
cheap/fast model, hard reasoning to a larger model). You call it just like
any other deployment — but under the hood it dispatches to different models.

Why use it?
- Lower cost: cheap model for easy prompts, big model only when needed
- Simpler code: one deployment name, no manual routing logic
- Transparency: the response reports which underlying model answered

What this sample shows:
1. Point an agent at the `model-router` deployment
2. Ask prompts of varying difficulty
3. Inspect the response metadata to see which model the router picked

Run:  .\.venv\Scripts\python.exe 07_model_router.py
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
# Override the default; this lesson specifically uses the router deployment.
ROUTER_DEPLOYMENT = os.getenv("ROUTER_DEPLOYMENT_NAME", "model-router")

# ── Create a client pointing at model-router ────────────────
client = FoundryChatClient(
    project_endpoint=PROJECT_ENDPOINT,
    model=ROUTER_DEPLOYMENT,
    credential=DefaultAzureCredential(),
)

agent = Agent(
    client=client,
    name="RoutedAgent",
    instructions=(
        "You are a helpful assistant. Answer concisely. "
        "If the user asks a math/reasoning question, show your steps."
    ),
)

# A mix of easy, medium, and hard prompts so the router has reason
# to pick different underlying models.
PROMPTS = [
    # Easy → router should pick a small/cheap model
    "Say hello in French.",
    # Medium → general knowledge
    "In 2 sentences, explain what a black hole is.",
    # Hard → multi-step reasoning / math
    (
        "A train leaves city A at 9:00 AM traveling 80 km/h. "
        "Another train leaves city B (400 km away) at 10:00 AM "
        "traveling 120 km/h toward city A. At what time do they meet? "
        "Show your reasoning step by step."
    ),
]


def _extract_routed_model(result) -> str:
    """Best-effort extraction of which underlying model the router chose.

    The exact field depends on SDK version; we probe a few common places
    and fall back to 'unknown'.
    """
    # agent_framework AgentRunResponse usually exposes .raw_representation
    # or .messages[*].raw_representation with the provider payload.
    candidates = []
    raw = getattr(result, "raw_representation", None)
    if raw is not None:
        candidates.append(raw)
    for msg in getattr(result, "messages", []) or []:
        r = getattr(msg, "raw_representation", None)
        if r is not None:
            candidates.append(r)

    for c in candidates:
        # dict-like
        if isinstance(c, dict):
            for key in ("model", "model_name", "deployment"):
                if key in c and c[key]:
                    return str(c[key])
        # object-like
        for attr in ("model", "model_name", "deployment"):
            v = getattr(c, attr, None)
            if v:
                return str(v)
    return "unknown"


async def main():
    print("=" * 60)
    print(f"Using deployment: {ROUTER_DEPLOYMENT}")
    print("=" * 60)

    for i, prompt in enumerate(PROMPTS, 1):
        print(f"\n── Prompt {i} ──")
        print(f"User: {prompt}")

        result = await agent.run(prompt)
        routed_to = _extract_routed_model(result)

        print(f"Routed to: {routed_to}")
        print(f"Agent: {result}")


if __name__ == "__main__":
    asyncio.run(main())
