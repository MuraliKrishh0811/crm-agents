# ollama Python client (README at tag v0.6.3)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Source: https://raw.githubusercontent.com/ollama/ollama-python/v0.6.3/README.md (repo: https://github.com/ollama/ollama-python)
> - Library version(s): ollama 0.6.3 (pinned)
> - Date retrieved: 2026-10-15
> - Status: Verbatim from the pinned tag's README; not yet run locally. The README uses a `gemma4` example model: our model is `llama3.1:8b`, set through `OLLAMA_MODEL`.

## Install

```sh
pip install ollama
```

## Chat

```python
from ollama import chat
from ollama import ChatResponse

response: ChatResponse = chat(
  model='gemma4',
  messages=[
    {
      'role': 'user',
      'content': 'Why is the sky blue?',
    },
  ],
)
print(response['message']['content'])
# or access fields directly from the response object
print(response.message.content)
```

## Custom client (host, headers)

```python
from ollama import Client

client = Client(host='http://localhost:11434', headers={'x-some-header': 'some-value'})
response = client.chat(
  model='gemma4',
  messages=[
    {
      'role': 'user',
      'content': 'Why is the sky blue?',
    },
  ],
)
```

## Async client

```python
import asyncio
from ollama import AsyncClient


async def chat():
  message = {'role': 'user', 'content': 'Why is the sky blue?'}
  response = await AsyncClient().chat(model='gemma4', messages=[message])


asyncio.run(chat())
```

## Ps (loaded models)

```python
ollama.ps()
```

## Errors

```python
model = 'does-not-yet-exist'

try:
  ollama.chat(model)
except ollama.ResponseError as e:
  print('Error:', e.error)
  if e.status_code == 404:
    ollama.pull(model)
```

## chat() signature, non-streaming overload (source file)

_From https://raw.githubusercontent.com/ollama/ollama-python/v0.6.3/ollama/_client.py. Confirms `format`, `options` and `keep_alive` parameters exist at 0.6.3._

```python
  def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    tools: Optional[Sequence[Union[Mapping[str, Any], Tool, Callable]]] = None,
    stream: Literal[False] = False,
    think: Optional[Union[bool, str]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> ChatResponse: ...
```

