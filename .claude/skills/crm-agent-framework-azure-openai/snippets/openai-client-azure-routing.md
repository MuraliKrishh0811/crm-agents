# agent_framework.openai with Azure routing (Azure OpenAI resource endpoint)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Source: https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/model-providers/openai
> - Page last updated (page metadata): 2026-10-02
> - Library version(s): agent-framework-openai 1.17.0 (pinned), agent-framework-core 1.22.0, azure-identity 1.26.0 (all pinned in inputs/references.md)
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)

## Install

```bash
pip install agent-framework-openai
```

## Install (credential= auth)

```bash
pip install azure-identity
```

## Azure configuration (env names used by the framework)

```bash
AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com"
AZURE_OPENAI_CHAT_MODEL="gpt-4o-mini"
# Optional shared fallback:
# AZURE_OPENAI_MODEL="gpt-4o-mini"
AZURE_OPENAI_API_VERSION="your-api-version"
```

## Create an agent routed to Azure OpenAI (Responses API)

```python
import asyncio
import os
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from azure.identity import AzureCliCredential

async def main():
    agent = Agent(
        client=OpenAIChatClient(
            model=os.environ["AZURE_OPENAI_CHAT_MODEL"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            credential=AzureCliCredential(),
        ),
        name="AzureOpenAIResponsesAgent",
        instructions="You are a helpful assistant.",
    )

    result = await agent.run("Hello!")
    print(result)

asyncio.run(main())
```

## Doc statement (routing rules)

> In Python, Azure OpenAI now uses the same `agent_framework.openai` clients shown here. Pass explicit Azure routing inputs such as `credential` or `azure_endpoint` when you want Azure routing, then set `api_version` for the Azure API surface you want to use. If `OPENAI_API_KEY` is configured, the generic clients stay on OpenAI even when `AZURE_OPENAI_*` variables are also present. If you already have a full `.../openai/v1` URL, use `base_url` instead of `azure_endpoint`. For Microsoft Foundry project endpoints and the Foundry Agent Service, see the [Microsoft Foundry provider page](microsoft-foundry). For local runtimes, see [Foundry Local](foundry-local).

## Doc statement (Chat Completions client)

> Use `OpenAIChatClient` for Responses or `OpenAIChatCompletionClient` for Chat Completions.

