# FoundryChatClient (Foundry project endpoint)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Source: https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/model-providers/microsoft-foundry
> - Page last updated (page metadata): 2026-10-06
> - Library version(s): agent-framework-foundry 1.15.0, agent-framework-core 1.22.0 (both pinned in inputs/references.md)
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)

## Install

```bash
pip install agent-framework-foundry
```

## Configuration (env names used by the framework)

```bash
FOUNDRY_PROJECT_ENDPOINT="https://<your-account>.services.ai.azure.com/api/projects/<your-project>"
FOUNDRY_MODEL="gpt-4o-mini"
```

## Create an agent with FoundryChatClient

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

agent = Agent(
    client=FoundryChatClient(
        project_endpoint="https://your-account.services.ai.azure.com/api/projects/your-project",
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    ),
    name="FoundryWeatherAgent",
    instructions="You are a helpful assistant.",
)
```

## Doc statement

> `FoundryChatClient` is the Foundry-first Python path for direct inference and supports tools, structured outputs, and streaming.

## Doc statement (when this client applies)

> If you have a standalone Azure OpenAI resource endpoint (`https://<your-resource>.openai.azure.com`), use the Python guidance on the [OpenAI provider page](openai).

