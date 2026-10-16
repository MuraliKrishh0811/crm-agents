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

## TODO / not yet researched

Auth for production (docs warn that `DefaultAzureCredential` needs care; REQUIREMENTS section 12 prefers managed identity; `AzureCliCredential` in snippets is a developer convenience); App Insights and Foundry tracing wiring; retry/timeout options on the clients; the `FOUNDRY_*` / `AZURE_OPENAI_*` env names are the framework's, ours are mapped from `example.env` explicitly rather than relying on framework env fallback.

## Sources

Docs hub https://learn.microsoft.com/en-us/agent-framework/ ; Foundry provider, OpenAI provider and structured-outputs pages (URLs and page dates in each snippet header); repo https://github.com/microsoft/agent-framework. Retrieved 2026-10-15. Snippets are reference excerpts of API shape; values in project code come from config.
