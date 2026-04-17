"""
=============================================================
 LESSON 8: MODEL ROUTER — ROUTING MODE COMPARISON
=============================================================

Routing modes (set at deployment time in the Foundry portal):
- Balanced : default — good cost/quality tradeoff
- Quality  : prefers larger/reasoning models (best for hard tasks)
- Cost     : prefers small/cheap models (best for high-volume simple tasks)

This sample sends the SAME prompts to up to 3 different model-router
deployments (one per mode) and shows which underlying model each picked,
plus response latency and token usage. That lets you see the tradeoffs
side-by-side.

── Prerequisite: deploy up to 3 model-router deployments ───
In the Foundry portal (Models + endpoints → Deploy model → model-router):
   1. Deploy "model-router-balanced"  with Routing mode = Balanced
   2. Deploy "model-router-quality"   with Routing mode = Quality
   3. Deploy "model-router-cost"      with Routing mode = Cost

Then add to .env:
   ROUTER_BALANCED_DEPLOYMENT=model-router-balanced
   ROUTER_QUALITY_DEPLOYMENT=model-router-quality
   ROUTER_COST_DEPLOYMENT=model-router-cost

Any deployment not configured in .env is skipped.

Run:  .\.venv\Scripts\python.exe 08_router_modes.py
=============================================================
"""

import os
import time
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")

# Map of mode name → env var holding the deployment name for that mode.
MODES = {
    "Balanced": os.getenv("ROUTER_BALANCED_DEPLOYMENT"),
    "Quality":  os.getenv("ROUTER_QUALITY_DEPLOYMENT"),
    "Cost":     os.getenv("ROUTER_COST_DEPLOYMENT"),
}

# If none set, fall back to the single router deployment from lesson 7.
if not any(MODES.values()):
    fallback = os.getenv("ROUTER_DEPLOYMENT_NAME", "model-router")
    print(f"[info] No per-mode deployments set; using single deployment '{fallback}' for all modes.")
    MODES = {f"Default ({fallback})": fallback}

# Prompts across the difficulty spectrum.
PROMPTS = [
    ("Easy",   "Translate 'good morning' to Spanish."),
    ("Medium", "In 3 sentences, explain why the sky is blue."),
    ("Hard",   "Prove that sqrt(2) is irrational. Show each step."),
]


def _extract(result):
    """Pull model name + token usage from the provider payload."""
    model = "unknown"
    usage = {}
    candidates = []
    raw = getattr(result, "raw_representation", None)
    if raw is not None:
        candidates.append(raw)
    for msg in getattr(result, "messages", []) or []:
        r = getattr(msg, "raw_representation", None)
        if r is not None:
            candidates.append(r)

    for c in candidates:
        if isinstance(c, dict):
            model = c.get("model") or c.get("model_name") or model
            if "usage" in c and isinstance(c["usage"], dict):
                usage = c["usage"]
        else:
            for attr in ("model", "model_name"):
                v = getattr(c, attr, None)
                if v:
                    model = str(v)
            u = getattr(c, "usage", None)
            if u is not None:
                usage = {
                    "prompt_tokens":     getattr(u, "prompt_tokens", None),
                    "completion_tokens": getattr(u, "completion_tokens", None),
                    "total_tokens":      getattr(u, "total_tokens", None),
                }
    return model, usage


async def run_prompt(mode: str, deployment: str, prompt: str) -> dict:
    client = FoundryChatClient(
        project_endpoint=PROJECT_ENDPOINT,
        model=deployment,
        credential=DefaultAzureCredential(),
    )
    agent = Agent(
        client=client,
        name=f"Router-{mode}",
        instructions="Answer concisely. Show reasoning for math problems.",
    )
    t0 = time.perf_counter()
    result = await agent.run(prompt)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    model, usage = _extract(result)
    return {
        "mode": mode,
        "deployment": deployment,
        "model": model,
        "latency_ms": elapsed_ms,
        "tokens": usage.get("total_tokens"),
        "answer": str(result),
    }


async def main():
    active = {m: d for m, d in MODES.items() if d}
    print("=" * 72)
    print("Routing-mode comparison")
    print(f"Active modes: {list(active.keys())}")
    print("=" * 72)

    for level, prompt in PROMPTS:
        print(f"\n{'─' * 72}")
        print(f"[{level}] {prompt}")
        print("─" * 72)

        # Run all active modes in parallel for each prompt
        results = await asyncio.gather(
            *(run_prompt(mode, dep, prompt) for mode, dep in active.items())
        )

        # Summary table
        print(f"\n{'Mode':<12} {'Routed model':<32} {'Latency':>9} {'Tokens':>8}")
        for r in results:
            print(
                f"{r['mode']:<12} {r['model']:<32} "
                f"{r['latency_ms']:>6} ms {str(r['tokens'] or '-'):>8}"
            )

        # Answers
        for r in results:
            preview = r["answer"].replace("\n", " ")
            if len(preview) > 220:
                preview = preview[:217] + "..."
            print(f"\n  → [{r['mode']}] {preview}")


if __name__ == "__main__":
    asyncio.run(main())
