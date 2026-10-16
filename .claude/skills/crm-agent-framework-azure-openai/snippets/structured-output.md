# Structured output with Agent (response_format)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Source: https://learn.microsoft.com/en-us/agent-framework/agents/structured-outputs
> - Page last updated (page metadata): 2026-08-25
> - Library version(s): agent-framework-core 1.22.0, agent-framework-openai 1.17.0, pydantic 2.14.1 (PyPI latest; core requires pydantic>=2,<3)
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)
>
> Page statement: "The `Agent` uses the `response_format` key in the `options` dict to specify the desired output schema."
> The page's own example builds the agent with `OpenAIChatCompletionClient(...).as_agent(...)`; the Foundry/OpenAI/Ollama provider pages build it with `Agent(client=...)`. Both forms appear in current docs. TODO: pick one form in slice 2 after running against the pinned versions.

## Pydantic model

```python
from pydantic import BaseModel

class PersonInfo(BaseModel):
    """Information about a person."""
    name: str | None = None
    age: int | None = None
    occupation: str | None = None
```

## Agent on Azure OpenAI Chat Completions

```python
import os
from agent_framework.openai import OpenAIChatCompletionClient
from azure.identity import AzureCliCredential

# Create the agent using Azure OpenAI Chat Client
agent = OpenAIChatCompletionClient(
    model=os.environ["AZURE_OPENAI_CHAT_COMPLETION_MODEL"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    credential=AzureCliCredential(),
).as_agent(
    name="HelpfulAssistant",
    instructions="You are a helpful assistant that extracts person information from text."
)
```

## Run with response_format

```python
response = await agent.run(
    "Please provide information about John Smith, who is a 35-year-old software engineer.",
    options={"response_format": PersonInfo},
)
```

## Read the parsed result

```python
if response.value:
    person_info = response.value
    print(f"Name: {person_info.name}, Age: {person_info.age}, Occupation: {person_info.occupation}")
else:
    print("No structured data found in response")
```

## JSON schema mapping instead of a model

```python
person_info_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "occupation": {"type": "string"},
    },
    "required": ["name", "age", "occupation"],
}

response = await agent.run(
    "Please provide information about John Smith, who is a 35-year-old software engineer.",
    options={"response_format": person_info_schema},
)

if response.value:
    person_info = response.value
    print(f"Name: {person_info['name']}, Age: {person_info['age']}, Occupation: {person_info['occupation']}")
```

## Streaming then get_final_response()

```python
# Stream updates in real time, then get the structured result
stream = agent.run(query, stream=True, options={"response_format": PersonInfo})
async for update in stream:
    print(update.text, end="", flush=True)

# get_final_response() returns the AgentResponse with the parsed value
final_response = await stream.get_final_response()

if final_response.value:
    person_info = final_response.value
    print(f"Name: {person_info.name}, Age: {person_info.age}, Occupation: {person_info.occupation}")
```

