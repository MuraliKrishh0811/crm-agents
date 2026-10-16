# Agent Framework OllamaChatClient (OPTIONAL; dependency conflict with ollama 0.6.3)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Source: https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/model-providers/ollama
> - Page last updated (page metadata): 2026-10-15
> - Library version(s): agent-framework-ollama 1.0.0b261015 (beta, pinned); it requires ollama>=0.5.3,<0.5.4 (PyPI metadata, retrieved 2026-10-15)
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)
>
> **Conflict:** `ollama` 0.6.3 (pinned for Skill 4) cannot be installed in the same environment as `agent-framework-ollama` 1.0.0b261015. `pip install agent-framework==1.22.0` also pulls it in through `agent-framework-core[all]`. See `crm-agent-framework-azure-openai/SKILL.md`.

## Install (native Ollama)

```bash
pip install agent-framework-ollama --pre
```

## Configuration (native Ollama)

```bash
OLLAMA_MODEL="llama3.2"
```

## Create an Ollama agent (native client)

```python
import asyncio
from agent_framework import Agent
from agent_framework.ollama import OllamaChatClient

async def main():
    agent = Agent(
        client=OllamaChatClient(),
        name="HelpfulAssistant",
        instructions="You are a helpful assistant running locally via Ollama.",
    )
    result = await agent.run("What is the largest city in France?")
    print(result)

asyncio.run(main())
```

## Doc statement

> The native client connects to `http://localhost:11434` by default. Override it with the `OLLAMA_HOST` environment variable or the `host` constructor argument.

