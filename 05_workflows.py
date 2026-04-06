"""
=============================================================
 LESSON 5: WORKFLOWS
=============================================================

What's a Workflow?
------------------
So far, we've built single agents. But what if you need multiple
steps that chain together?

  Input → Step 1 (process) → Step 2 (transform) → Output

A Workflow is a pipeline. Each step is called an "Executor".
Data flows from one executor to the next via edges.

Think of it like an assembly line:
  Raw text → [UPPERCASE it] → [REVERSE it] → Final output
  "hello"  →    "HELLO"     →   "OLLEH"    → done!

Key Concepts:
- Executor: A single processing step (a class or a decorated function)
- @handler: Marks the method that processes input in a class-based executor
- @executor: Marks a function as a standalone executor
- WorkflowBuilder: Connects executors with edges (Step1 → Step2)
- ctx.send_message(): Pass output to the NEXT step
- ctx.yield_output(): Produce the FINAL workflow output
- workflow.run(): Execute the entire pipeline

Two ways to define executors:
1. Class-based: class MyStep(Executor) with @handler method
2. Function-based: @executor decorator on a plain function

This example does NOT use an LLM — workflows are about
orchestrating steps, not necessarily AI.

Run:  .venv/bin/python 05_workflows.py
Docs: https://learn.microsoft.com/en-us/agent-framework/get-started/workflows
=============================================================
"""

import asyncio
from typing import Never
from dotenv import load_dotenv

load_dotenv(override=True)

from agent_framework import Executor, handler, executor, WorkflowBuilder, WorkflowContext


# ── Step 1: Class-based executor ────────────────────────────
#   Converts input text to UPPERCASE.
#   Uses ctx.send_message() to forward to the next step.

class UpperCase(Executor):
    def __init__(self, id: str):
        super().__init__(id=id)

    @handler
    async def to_upper_case(self, text: str, ctx: WorkflowContext[str]) -> None:
        """Convert input to uppercase and forward to the next node."""
        print(f"  [UpperCase] '{text}' → '{text.upper()}'")
        await ctx.send_message(text.upper())


# ── Step 2: Function-based executor ─────────────────────────
#   Reverses the string and yields the FINAL output.
#   Uses ctx.yield_output() because this is the last step.

@executor(id="reverse_text")
async def reverse_text(text: str, ctx: WorkflowContext[Never, str]) -> None:
    """Reverse the string and yield the final workflow output."""
    reversed_text = text[::-1]
    print(f"  [Reverse]   '{text}' → '{reversed_text}'")
    await ctx.yield_output(reversed_text)


# ── Build the workflow ──────────────────────────────────────
#   Connect the steps: UpperCase → reverse_text
#   The WorkflowBuilder creates the pipeline.

def create_workflow():
    """Build the workflow: UpperCase → reverse_text."""
    upper = UpperCase(id="upper_case")
    return WorkflowBuilder(start_executor=upper).add_edge(upper, reverse_text).build()


async def main():
    workflow = create_workflow()

    print("=" * 50)
    print("WORKFLOW: UpperCase → Reverse")
    print("=" * 50)

    inputs = ["hello world", "agent framework", "vinay"]

    for text in inputs:
        print(f"\nInput: '{text}'")
        events = await workflow.run(text)
        outputs = events.get_outputs()
        print(f"Output: {outputs}")


if __name__ == "__main__":
    asyncio.run(main())
