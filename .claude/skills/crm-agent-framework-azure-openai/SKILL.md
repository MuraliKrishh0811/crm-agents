---
name: crm-agent-framework-azure-openai
description: Microsoft Agent Framework (Python) with Foundry or Azure OpenAI for the live ChatModelProvider - client choice (FoundryChatClient first, agent_framework.openai with Azure routing second), pinned install set, structured output, and the changelog findings. All UNVERIFIED until real access exists. Use when writing or reviewing the live model adapter, its config, or its contract tests.
---

# Microsoft Agent Framework with Foundry / Azure OpenAI (live model path, UNVERIFIED)

## Always true (repeated in every project skill)

- **Everything is real.** The live adapter is a real implementation written from current docs. No mocking, stubs, canned or hardcoded responses, no hardcoded snippets standing in for behavior.
- **Ollama is the local fallback.** Local mode (Ollama) is the working system in Phase 1; this live path is off by default (R3) and cannot run until IT provides access.
- **Never read `.env`.** Use `example.env` only.
- **`REQUIREMENTS.md` is authoritative** (sections 6, 12). Only `inputs/decisions.md` can override it.

## Status

Everything here is **UNVERIFIED**: copied from docs read on 2026-10-15, never run against a service. Label the code `implemented, unverified`. Contract tests (TR-7) run the real adapter against sample responses shaped like real output and are labeled contract tests, never "live verification".

## Role in the architecture

Agent Framework lives only inside the live `ChatModelProvider` adapters (`crm-provider-pattern`). Agents hand the adapter `complete(messages, output_schema)`; the adapter builds an `Agent(client=...)`, calls it with `options={"response_format": <Pydantic model>}`, reads `response.value`, and still validates and retries per the interface contract. Temperature low; no time arithmetic by the model (R4).

## Which client: depends on what IT provisions

1. **First choice: `FoundryChatClient`** (`agent_framework.foundry`), for a Foundry project endpoint (`https://<account>.services.ai.azure.com/api/projects/<project>`). Docs call it the Foundry-first Python path and say it supports tools, structured outputs and streaming. Snippet: [foundry-chat-client.md](snippets/foundry-chat-client.md).
2. **Second: `OpenAIChatClient` / `OpenAIChatCompletionClient` with Azure routing** (`agent_framework.openai`, pass `azure_endpoint` and `credential`, set `api_version`), for a standalone Azure OpenAI resource endpoint (`https://<resource>.openai.azure.com`). Snippet: [openai-client-azure-routing.md](snippets/openai-client-azure-routing.md). Gotcha from the docs: if `OPENAI_API_KEY` is set, the generic clients stay on OpenAI unless explicit Azure routing inputs are passed.
3. The old `AzureOpenAI*` Python classes were removed from `agent_framework.azure`; do not use them.

The choice is made on the first day with access and recorded in `docs/first_day_with_access.md`. Select by config (`MODEL_PROVIDER` = `ollama` | `foundry` | `azure_openai`); both live clients sit behind the same adapter interface.

## Install set (exact pins; do not install the meta-package)

| Package | Version | Pin source |
|---|---|---|
| `agent-framework-core` | 1.22.0 | `inputs/references.md` (install note; version of `agent-framework`) |
| `agent-framework-foundry` | 1.15.0 | `inputs/references.md` |
| `agent-framework-openai` | 1.17.0 | `inputs/references.md` |
| `azure-identity` | 1.26.0 | `inputs/references.md` |
| `ollama` | 0.6.3 | `inputs/references.md` (local mode) |
| `msgraph-sdk` | 1.64.0 | `inputs/references.md` (Graph) |

**Do not `pip install agent-framework`.** Its only dependency is `agent-framework-core[all]==1.22.0`, and the `all` extra includes `agent-framework-ollama`, which requires `ollama>=0.5.3,<0.5.4` and conflicts with the pinned `ollama==0.6.3` used by local mode (PyPI JSON metadata, read 2026-10-15; the same install note is in `inputs/references.md`).

**Dependency dry-run (2026-10-16, project `.venv`, Python 3.14.4, pip 26.2.1):** `python -m pip install --dry-run` of exactly the six pins above exited 0 with no conflicts and no warnings, and did not resolve `agent-framework-ollama`. It resolved, among others, `openai` 3.31.0, `azure-ai-projects` 2.7.0, `pydantic` 2.14.1, `httpx` 0.28.1, `msgspec` 0.22.0. Transitive packages are not pinned by this set, so create a lock file in slice 1. A dry-run proves resolvability only, not that imports or behavior work: run `pip check` and a real import after the first install.

## Structured output

`Agent` takes `options={"response_format": Model}` (or a JSON schema dict) and returns the parsed object in `response.value`. Snippet: [structured-output.md](snippets/structured-output.md). Docs show two construction forms (`Agent(client=...)` and `client.as_agent(...)`); pick one in slice 2 after running it.

## Changelog check (required before using any API)

Source: https://github.com/microsoft/agent-framework/blob/main/python/CHANGELOG.md (read as raw file, releases 1.17.0 to 1.22.0, 2026-09-03 to 2026-10-15; earlier releases not read). Relevant entries:

- **1.22.0 [BREAKING]**: content identity, hosted execution, protocol metadata, replay and stream-merge semantics consolidated across core, foundry, openai (and others). Pre-1.22 runtimes cannot read stored records containing `hosted` or `merge_mode`. We pin exactly; never mix versions against one store.
- 1.22.0: `Message` given a single string is one text item (not one per character); openai reads the Azure OpenAI API version before applying defaults; ollama/openai chat clients gain configurable service URLs.
- 1.20.0: openai metadata defaults isolated from Azure-routed clients (fix).
- 1.18.0 [BREAKING]: Lab removed from `core[all]`; foundry supports Azure AI Projects through 2.6 with OpenAI 3.x.
- No entry in that range renames `Agent` or `FoundryChatClient`. Re-read the changelog before any version bump.

## Authentication, tracing and request configuration (implemented, unverified)

Research checked against official docs and framework source on 2026-10-16. These are reference API shapes for the live adapter, not live verification; confirm them against the pinned packages during implementation.

### Authentication

Use an explicit credential: `AzureCliCredential()` for local development with live access; `ManagedIdentityCredential()` for a system-assigned identity in Azure, or `ManagedIdentityCredential(client_id=managed_identity_client_id)` for a user-assigned identity. Import from `azure.identity.aio` for async adapters and close the credential at shutdown. Pass it as `credential` to either live client. Do not silently fall back to developer credentials in production. Microsoft recommends a specific production credential instead of an unrestricted `DefaultAzureCredential` chain. Hosting and identity selection remain deferred under D8; confirm resource authorization with IT. [Credential-chain guidance](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication/credential-chains), [managed identity guidance](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication/user-assigned-managed-identity).

### App Insights and Foundry tracing

Configure telemetry once at startup, only for the live path. Add and lock `azure-monitor-opentelemetry` separately when implementing this integration; it is not in the six-package install set above. Current docs recommend `>=1.8.10,<2` for HTTPX trace correlation.

- Foundry: connect the project to Application Insights, then call `await client.configure_azure_monitor(enable_live_metrics=False)` before creating/running the agent. The client obtains the project's connection string.
- Standalone Azure OpenAI: pass the configured Application Insights connection string explicitly:

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from agent_framework.observability import enable_instrumentation

configure_azure_monitor(
    connection_string=applicationinsights_connection_string,
    enable_live_metrics=False,
)
enable_instrumentation(enable_sensitive_data=False)
```

For Foundry, also call `enable_instrumentation(enable_sensitive_data=False)` after its setup. Do not additionally call `configure_otel_providers()` when Azure Monitor owns the providers. Attach the application's run ID to its parent span and structured logs. Keep prompts, mail bodies and model responses out of telemetry. Standalone agents need registration with the same OpenTelemetry agent ID to appear in Foundry. [Observability setup](https://learn.microsoft.com/en-us/agent-framework/agents/observability).

### Timeouts and retries

`OpenAIChatClient` accepts `timeout` in seconds and an injected SDK client via `async_client`; `max_retries` is an SDK setting, not a framework constructor argument. `FoundryChatClient` creates its SDK client through `AIProjectClient.get_openai_client()` and exposes neither timeout nor retry constructor parameters. Both use the inherited public `client` attribute. Configure the SDK client once, before requests:

```python
client.client = client.client.with_options(
    timeout=request_timeout_s,
    max_retries=transport_max_retries,
)
```

Validate a finite positive timeout and a nonnegative integer retry count in application config. The SDK retries connection failures, 408, 409, 429 and 5xx responses with backoff; avoid another transport retry loop. Schema-validation retries belong to the adapter contract and need a separate bounded budget. Wrap the complete operation, including validation retries, in `asyncio.timeout(total_timeout_s)` to bound overall latency. Close SDK clients and credentials at shutdown; SDK copies share their HTTP transport. [OpenAI client source](https://github.com/microsoft/agent-framework/blob/main/python/packages/openai/agent_framework_openai/_chat_client.py), [Foundry client source](https://github.com/microsoft/agent-framework/blob/main/python/packages/foundry/agent_framework_foundry/_chat_client.py), [SDK retry and timeout configuration](https://github.com/openai/openai-python#retries).

### Explicit environment mapping

Read application configuration once and pass these constructor arguments explicitly. Reject missing or blank values for the selected live provider before client construction; leave live clients unconstructed for `MODEL_PROVIDER=ollama`.

| Application variable in `example.env` | Constructor argument |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | `FoundryChatClient(project_endpoint=...)` |
| `FOUNDRY_MODEL` | `FoundryChatClient(model=...)` |
| `AZURE_OPENAI_ENDPOINT` | `OpenAIChatClient(azure_endpoint=...)` (also applies to `OpenAIChatCompletionClient`) |
| `AZURE_OPENAI_DEPLOYMENT` | `model=...` on either Azure-routed OpenAI client; use the deployment name |
| `AZURE_OPENAI_API_VERSION` | `api_version=...` on either Azure-routed OpenAI client |

Pass `credential` explicitly as well. `AZURE_OPENAI_DEPLOYMENT` is our configuration name: do not rely on the framework's `AZURE_OPENAI_CHAT_MODEL`, `AZURE_OPENAI_CHAT_COMPLETION_MODEL` or `AZURE_OPENAI_MODEL` fallbacks. Do not pass `env_file_path` or load `.env`. Managed-identity selection, telemetry connection string and request budgets are additional application settings to document in `example.env` when the adapter is implemented; they are not existing entries. [Provider routing and environment names](https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/model-providers/openai).

## Sources

Docs hub https://learn.microsoft.com/en-us/agent-framework/ ; Foundry provider, OpenAI provider and structured-outputs pages (URLs and page dates in each snippet header); repo https://github.com/microsoft/agent-framework. Retrieved 2026-10-15. Snippets are reference excerpts of API shape; values in project code come from config.
