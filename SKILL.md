# Azure AI Foundry — Agent Framework Learnings

## Project Structure

```
.env              # PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME
.gitignore
.venv/
SKILL.md          # This file — accumulated learnings
test.py           # Scratch/utility script

── Get-Started Tutorial (from MS docs) ──
01_first_agent.py   # Lesson 1: Create agent, run, stream
02_add_tools.py     # Lesson 2: @tool decorator, function tools
03_multi_turn.py    # Lesson 3: Sessions for conversation memory
04_memory.py        # Lesson 4: ContextProvider for persistent facts
05_workflows.py     # Lesson 5: Executor pipelines (no LLM needed)
06_hosting.py       # Lesson 6: DevUI web hosting
```

## Agent Types

### 1. Prompt Agent (no-code)
- Uses only the LLM — no custom Python logic.
- Created via `AIProjectClient` + `openai_client.responses.create()`.
- Multi-turn: pass `previous_response_id` to maintain conversation.

### 2. Registered Prompt Agent
- Same as prompt agent but registered on portal with `client.agents.create_version()`.
- Definition: `PromptAgentDefinition(model=..., instructions=..., tools=[WebSearchPreviewTool()])`.
- Invoke via `extra_body={"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}}`.

### 3. Hosted Agent (code-based)
- Custom Python tools with `@tool` decorator.
- Uses `Agent` class from `agent_framework` + `FoundryChatClient`.
- Run locally: `await agent.run("question")`.
- Run as server: `from_agent_framework(agent).run()` (port 8088 in Docker).

### 4. Registered Hosted Agent (deployed container)
- Docker image pushed to ACR, registered on Foundry, deployed via CLI.
- Uses `HostedAgentDefinition` with container config (cpu, memory, image, env vars).
- Requires `ProtocolVersionRecord(protocol=AgentProtocol.RESPONSES, version="v1")`.
- Header: `{"Foundry-Features": "HostedAgents=V1Preview"}`.

## Key SDK Classes & Packages

| Package | Class | Use |
|---|---|---|
| `azure-ai-projects` | `AIProjectClient` | Foundry project operations, agent registration |
| `agent-framework-core` | `Agent`, `@tool` | Core agent + tool decorator |
| `agent-framework-foundry` | `FoundryChatClient` | Local agent with Foundry backend |
| `agent-framework-azure-ai` | `AzureAIAgentClient` | Container agent client (Docker only) |
| `agent-framework-openai` | `OpenAIChatClient` | Generic OpenAI/Azure OpenAI client |
| `agent-framework-devui` | `serve()` | Local browser UI for testing |
| `azure-ai-agentserver-agentframework` | `from_agent_framework()` | HTTP hosting adapter for containers |

## Authentication & Identity

- **Local development**: `DefaultAzureCredential()` (picks up `az login` session).
- **Hosted containers on Foundry**: `DefaultAzureCredential()` resolves to the **Foundry project's system-assigned managed identity**.
- **Portal location**: Azure AI services → your account → Identity blade.
- No API keys needed — managed identity throughout.

## Client Selection Gotchas

- `FoundryChatClient` — use for **Foundry project endpoints** (`https://<account>.services.ai.azure.com/api/projects/<project>`).
  - Param: `project_endpoint=` (not `endpoint=`).
- `OpenAIChatClient` — use for **raw Azure OpenAI endpoints** (`https://<account>.services.ai.azure.com`).
  - Azure auth param: `credential=` (not `azure_ad_token_provider=`).
  - Needs base endpoint without `/api/projects/...` path.
  - Uses `/openai/v1/` URL path internally.
- `AzureAIAgentClient` — **only available inside containers** (from `agent-framework-azure-ai`).
  - Not importable in local venv alongside DevUI.

## API Versions (Azure OpenAI Responses API)

- `2025-03-01-preview` — minimum for Responses API.
- `2025-04-01-preview` — works.
- `2025-02-01-preview` and earlier — NOT supported for Responses API.
- `FoundryChatClient` handles API version automatically (preferred).

## DevUI (Local Testing)

```bash
pip install agent-framework-devui --pre
```

```python
from agent_framework.devui import serve
serve(entities=[agent], auto_open=True, port=8080)
```

- Web UI at `http://localhost:8080`.
- Also exposes OpenAI-compatible API at `http://localhost:8080/v1`.
- CLI alternative: `devui ./agents --port 8080`.

## Deployment Steps (Registered Hosted Agent)

1. Find resource group: `az resource list --name $ACCOUNT --resource-type Microsoft.CognitiveServices/accounts`
2. Create ACR: `az acr create --name $ACR_NAME --sku Basic`
3. Build & push: `docker build --platform linux/amd64 -t $IMAGE ./hosted_app && docker push $IMAGE`
4. Grant ACR pull: assign `AcrPull` role to Foundry project's managed identity on the ACR
5. Create capability host: `az rest --method put` to `.../capabilityHosts/accountcaphost?api-version=2025-10-01-preview`
6. Register agent: `client.agents.create_version()` with `HostedAgentDefinition`
7. Start: `az cognitiveservices agent start --account-name ... --project-name ... --name ... --agent-version ...`

## Endpoint Format

```
PROJECT_ENDPOINT = https://<account>.services.ai.azure.com/api/projects/<project>
  ├── account name: first segment before .services
  └── project name: last segment after /projects/
```

## Tips

- Docker image MUST be `--platform linux/amd64` for Foundry.
- Container exposes port 8088 (hosting adapter default).
- Tools can be shared across local/container by extracting to a separate `tools.py`.
- `from_agent_framework(agent).run()` is the hosting adapter entry point.
- `WebSearchPreviewTool()` gives prompt agents web search capability.
- Environment variables (`AZURE_AI_PROJECT_ENDPOINT`, `MODEL_NAME`) are injected into containers via `HostedAgentDefinition.environment_variables`.

## Deleting a Hosted Agent

Must follow this order — agent deletion fails if containers are still associated:

```bash
# 1. Stop the container
az cognitiveservices agent stop \
  --account-name $ACCOUNT_NAME \
  --project-name $PROJECT_NAME \
  --name $AGENT_NAME \
  --agent-version <version>

# 2. Delete the deployment (removes the container)
az cognitiveservices agent delete-deployment \
  --account-name $ACCOUNT_NAME \
  --project-name $PROJECT_NAME \
  --name $AGENT_NAME \
  --agent-version <version>

# 3. Wait for container deletion to complete (takes a few minutes)

# 4. Delete the agent
client.agents.delete(agent_name="time-calc-agent")
```

- `stop` alone is NOT enough — must also `delete-deployment`.
- Container deletion is async; wait until status is no longer "Deleting".
- Cannot delete the agent while containers are in any state (active, stopped, or deleting).
