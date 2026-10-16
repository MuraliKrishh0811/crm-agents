# Ollama docs: structured output, context length, keep-alive and preload

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Sources: https://docs.ollama.com/capabilities/structured-outputs , https://docs.ollama.com/faq , https://docs.ollama.com/context-length (raw `.md` renderings)
> - Library version(s): Ollama server v0.40.5 was the latest release on 2026-10-15; ollama (Python) 0.6.3
> - Date retrieved: 2026-10-15
> - Status: Verbatim from docs; not yet run locally. The docs' example model names (`gpt-oss`, `mistral`, `llama3.2`) are not ours.
>
> **TODO (verify in slice 1 against a running Ollama):** the docs show preload only as `curl ... -d '{"model": "mistral"}'`. The Python equivalent (`chat(model=..., messages=[], keep_alive=...)`) is NOT documented; confirm it works with ollama 0.6.3 before relying on it.
> **Doc inconsistency:** the FAQ says the default context is 4096 tokens; the context-length page says it depends on VRAM (<24 GiB: 4k). On the 16 GB MacBook Air M4 treat the default as unconfirmed and always pass `num_ctx` explicitly, then check the `CONTEXT` column of `ollama ps`.

## Structured output with a JSON schema (Pydantic)

```python
from ollama import chat
from pydantic import BaseModel

class Pet(BaseModel):
  name: str
  animal: str
  age: int
  color: str | None
  favorite_toy: str | None

class PetList(BaseModel):
  pets: list[Pet]

response = chat(
  model='gpt-oss',
  messages=[{'role': 'user', 'content': 'I have two cats named Luna and Loki...'}],
  format=PetList.model_json_schema(),
)

pets = PetList.model_validate_json(response.message.content)
print(pets)
```

## Doc note: ground the model with the schema in the prompt

> It is ideal to also pass the JSON schema as a string in the prompt to ground the model's response.

## Doc tips for reliable structured outputs

> * Define schemas with Pydantic (Python) or Zod (JavaScript) so they can be reused for validation.
> * Lower the temperature (e.g., set it to `0`) for more deterministic completions.

## Context window via API options

_FAQ: 'How can I specify the context window size?'_

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?",
  "options": {
    "num_ctx": 4096
  }
}'
```

## Server default via environment variable

```shell
OLLAMA_CONTEXT_LENGTH=8192 ollama serve
```

## Context length defaults by VRAM (context-length page)

> Ollama defaults to the following context lengths based on VRAM:
>
> * < 24 GiB VRAM: 4k context
> * 24-48 GiB VRAM: 32k context
> * >= 48 GiB VRAM: 256k context

## Check allocated context and offloading

_context-length page; run `ollama ps` and read PROCESSOR and CONTEXT._

```
NAME             ID              SIZE      PROCESSOR    CONTEXT    UNTIL
gemma4:latest    c6eb396dbd59    9.6 GB    100% GPU     131072     2 minutes from now
```

## Preload with an empty chat request (HTTP)

_FAQ: 'How can I preload a model into Ollama to get faster response times?'_

```shell
curl http://localhost:11434/api/chat -d '{"model": "mistral"}'
```

## Doc statement (default keep-alive)

> By default models are kept in memory for 5 minutes before being unloaded.

## Doc statement (keep_alive values)

> The `keep_alive` parameter can be set to:
>
> * a duration string (such as "10m" or "24h")
> * a number in seconds (such as 3600)
> * any negative number which will keep the model loaded in memory (e.g. -1 or "-1m")
> * '0' which will unload the model immediately after generating a response

## Preload and keep loaded (HTTP)

```shell
curl http://localhost:11434/api/generate -d '{"model": "llama3.2", "keep_alive": -1}'
```

## Doc statement (precedence)

> The `keep_alive` API parameter with the `/api/generate` and `/api/chat` API endpoints will override the `OLLAMA_KEEP_ALIVE` setting.

