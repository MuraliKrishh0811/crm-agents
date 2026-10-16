---
name: crm-provider-pattern
description: The provider pattern for CRM Agents - the four interfaces (MailProvider, CalendarProvider, ChatModelProvider, CrmRepository), their local fallbacks (.eml replay, mock calendar JSON, Ollama, SQLite) and live adapters, and how Agent Framework fits so live and local share one set of agent logic. Use when adding or changing any provider, agent dependency, or configuration switch between local and live.
---

# Provider pattern and local fallbacks

## Always true (repeated in every project skill)

- **Everything is real.** Agents, Graph calls and provider adapters are real implementations. No mocking, stubs, canned or hardcoded responses, no hardcoded snippets standing in for behavior.
- **Ollama is the local fallback.** Local mode (Ollama, `.eml` files, mock calendar JSON, SQLite) is the working system in Phase 1 and the default.
- **Never read `.env`.** Use `example.env` only.
- **`REQUIREMENTS.md` is authoritative** (sections 6, 11 and 12 govern this skill). Only `inputs/decisions.md` can override it.

## Rule

Agents (Ingestion, Stage Classifier, Summary and Next Action, Scheduler, CRM Writer) and the Orchestrator depend on the four provider interfaces only (R2). They never import Graph, Azure, Ollama, Agent Framework, file-system readers or a database driver. Configuration picks the implementation per provider; the active provider and model are recorded in the audit log for every call (FR-AUD-1, FR-CFG-1).

## Interfaces (language-neutral, from REQUIREMENTS section 6)

```
MailProvider:      list_new_messages(since) -> [Email]; get_message(id) -> Email;
                   create_reply_draft(thread, body) -> DraftRef; send_draft(draft_ref)  # only after approval
CalendarProvider:  get_availability(users, start, end) -> per-user [{start,end,showAs}];
                   create_event(event) -> EventRef; update_event(event_key, changes) -> EventRef;
                   find_event(event_key) -> Event | None
ChatModelProvider: complete(messages, output_schema) -> validated structured result  # validate; retry on malformed
CrmRepository:     customers, contacts, emails, engagements, meetings, stage_history, next_actions,
                   scheduling_requests, audit entries
                   + customers_by_stage, stale_leads, next_actions_due(range), customer_timeline(customer_id)
```

## Implementations

| Interface | Local (working, Phase 1) | Live (written from docs, UNVERIFIED, off by default) |
|---|---|---|
| MailProvider | Parses `.eml` (Message-ID, In-Reply-To, References, Date with offset, From/To/Cc, multipart, attachments); replays in date order against the simulated clock | Microsoft Graph (`crm-graph-integration`) |
| CalendarProvider | Reads mock calendar JSON (Graph event shape, `showAs` values); **also persists meetings the system creates** so later availability sees them | Microsoft Graph |
| ChatModelProvider | Ollama `llama3.1:8b` (`crm-ollama-local-model`) | Foundry project endpoint or Azure OpenAI resource endpoint via Agent Framework (`crm-agent-framework-azure-openai`) |
| CrmRepository | SQLite | Azure SQL or Dataverse (undecided, D3 defers); stays behind the interface |

Live adapters refuse to start without their configuration and are labeled `implemented, unverified` in code, docs and the audit view. A health-check fallback from live to local is optional; if built, log it.

## How Agent Framework and ChatModelProvider fit (one set of agent logic)

```
CRM API -> Orchestrator (interface; plain Python implementation, D9)
Orchestrator + agents (our code: prompts, Pydantic output schemas, deterministic scheduling)
        |  complete(messages, output_schema)
   ChatModelProvider  <- the only seam
     |-- OllamaProvider   : ollama Python client, format=schema, validate, retry   (local)
     |-- FoundryProvider  : Agent Framework Agent(client=FoundryChatClient)         (live, UNVERIFIED)
     `-- AzureOpenAIProvider: Agent Framework Agent(client=OpenAIChatClient + Azure routing) (live, UNVERIFIED)
```

- Agent Framework is an implementation detail inside the live adapters. Agent logic never sees it, so live and local run the same prompts, schemas and scheduling code.
- Every adapter honors the same contract: return a result that validates against the caller's schema, retry a bounded number of times on malformed output, raise a typed error otherwise (the pipeline records it and continues, section 14).
- **Orchestration (D9):** a plain Python orchestrator behind an `Orchestrator` interface for Phase 1. The CRM API calls the interface, never a concrete class, so the implementation can change later. Reason recorded in `inputs/decisions.md`: the pipeline is fixed with a human approval gate, which is easier to test, and the framework's workflow and Ollama packages are beta. Revisit Agent Framework Workflows once live access exists and record the outcome in `decisions.md`; until then do not introduce Workflows.

## Idempotency and approval at the provider seam

- `MailProvider` and `CrmRepository` dedupe on Message-ID (FR-ING-5); meetings on iCalUId or a stable internal key (R6). Replaying the full set twice yields identical CRM state (TR-6).
- `send_draft`, `create_event`, `update_event` are called only from the approval path (R5, FR-APP-2).
- Anything local mode cannot truly produce (Teams join link) is stored with a `simulated` flag and shown as simulated (R10).

## Config switches (names from `example.env`)

`PROVIDER_MODE` (`local` default), `MAIL_PROVIDER`, `CALENDAR_PROVIDER`, `MODEL_PROVIDER` (`ollama` | `foundry` | `azure_openai`), `DATABASE_URL`, `DATA_DIR`, `SIMULATED_NOW` (naive local time) with `SIMULATED_TZ` (IANA zone). All keys, including the Ollama and live-model ones, are in `example.env`. Suggested package layout belongs in the implementation plan, not here.
