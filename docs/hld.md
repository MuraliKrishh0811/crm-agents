# High-Level Design (HLD)

Status: draft for review, updated 2026-10-16 after every design question (OQ-1 to OQ-33) was resolved in `inputs/decisions.md` ("Design decisions") and `REQUIREMENTS.md` was edited to match (sections 6, 9, 13, 17; FR-SCH-2, FR-APP-1, FR-APP-2, FR-APP-4, TR-13). Phase 1 (local only). **No application code exists yet**; this document describes the design that `REQUIREMENTS.md` calls for.

Authority and terms:

- `REQUIREMENTS.md` is authoritative. Decisions D1-D9 and the resolved design questions come from `inputs/decisions.md`. The architecture source is `docs/architecture/eraser-code.txt` (`decisions.md` says no rendered image is kept in the repository).
- Terms follow `REQUIREMENTS.md` and the project skills in `.claude/skills/`. IDs (`FR-`, `TR-`, `R`) are cited where relevant.
- Anything about live Microsoft Graph, Entra ID or Azure OpenAI/Foundry behavior is marked **UNVERIFIED**: it is written from documentation and has never run against a service (section 18 of the requirements).
- This document makes no new decisions. `OQ-n` numbers match `inputs/decisions.md`, which points here. All of OQ-1 to OQ-33 are resolved and shown in section 12.1; section 12.2 lists what is still open, with the slice that needs each item; section 13 records the inconsistencies found in the inputs and how they were resolved. Companion documents: [lld.md](lld.md), [api.md](api.md), [demo.md](demo.md), [first_day_with_access.md](first_day_with_access.md).

## 1. Purpose and scope

A CRM-style application where agents read customer emails and internal calendars to (1) track each customer through the lifecycle (current stage, engagement history, next action) and (2) schedule meetings: when a customer offers times by email, check internal availability, propose common slots, and, **only after a person approves**, create or update the Outlook/Teams meeting and record it in the CRM (requirements section 2).

In scope (section 4): email ingestion, customer matching, stage classification, summaries and next actions; scheduling including conflicts, no-overlap counter-proposals, clarification requests and rescheduling; CRM API, web dashboard, approval flow, audit trail; Teams Copilot agent (after the dashboard, D6).

Out of scope: reading the customer's own calendar (their availability comes only from their emails); sending or booking without approval (R5); channels other than email; replacing an enterprise CRM product.

## 2. Context

```
 External customer ---- email only ---->  Mailbox
                                           live: Exchange Online via Microsoft Graph   (UNVERIFIED)
                                           local: .eml files replayed in date order

 Internal team --- browser ------------>  Web Dashboard (React, Vite, TypeScript; D2)  -+
 Internal team --- Teams (later, D6) -->  Teams Copilot Agent                           -+--> CRM API
```

| Actor | Role |
|---|---|
| External customer | Communicates by email only. Never uses the system directly |
| Internal team member (account executive, solutions engineer) | Reviews proposals and **approves, edits or rejects** (FR-APP-1) |
| Approver | **Phase 1:** a configured local user name, with no login screen, recorded on every approval; the API listens on localhost only (OQ-13, resolved). **Live:** real authentication with Entra ID is designed in [api.md](api.md), marked UNVERIFIED, and built after live access exists; the live approver and permissions are for IT (D7) |

## 3. Components

Source of this picture: requirements section 6 and `docs/architecture/eraser-code.txt` (updated).

```
UI:        Web Dashboard, Teams Copilot Agent            (both call the same API)
              |
Backend:   CRM API -> Orchestrator (D9) -> agents:
              Ingestion | Stage Classifier | Summary and Next Action | Scheduler | CRM Writer
           Orchestrator (approval handler) -> CalendarProvider, MailProvider   [after human approval only]
              |
Providers: MailProvider | CalendarProvider | ChatModelProvider | CrmRepository      (exactly four)
              |                 |                  |                   |
Local:     .eml files      mock calendar JSON     Ollama             SQLite
Live:      Graph (UNV.)    Graph (UNV.)       Foundry/Azure OpenAI   Azure SQL or Dataverse
                                              via Agent Framework    (undecided, D3)
                                              (UNV.)
Data:      CRM Store; Audit and Trace Store = audit tables written THROUGH CrmRepository
           (separate tables, same database in Phase 1)
Observability: structured logs with a run ID (local); App Insights and Foundry tracing (live, UNVERIFIED)
```

| Component | Responsibility | Requirements | Phase 1 implementation |
|---|---|---|---|
| Web Dashboard | Pipeline view, customer detail, scheduling panel with approve/edit/reject, audit view | FR-UI-1 to FR-UI-4 | React + Vite + TypeScript |
| Teams Copilot Agent | Conversational access to the same API | FR-UI-5, D6 | After the dashboard |
| CRM API | One API for both UIs: customers, timelines, next actions, scheduling requests, approvals, trigger for the agent workflow | FR-API-1, TR-13 | Python backend (D1); binds 127.0.0.1 only, configured approver (OQ-13), Origin and Host checks, CORS limited to the dashboard origin, per-run token on writes (api.md section 10.1) |
| Orchestrator | Runs the fixed pipeline of agents per email (stage 1); **its approval handler** runs the approved steps (stage 2); records audit; isolates failures | D9, FR-APP-2, FR-APP-4, FR-APP-5, FR-AUD-1, section 14 | Plain Python behind an `Orchestrator` interface |
| Ingestion Agent | Normalize email, strip quoted text, match customer, create lead, dedupe, ignore noise, handle sent mail, add contacts, store attachment metadata; **passes only the cleaned new-email text on** | FR-ING-1 to FR-ING-9 | Real code over `MailProvider` |
| Stage Classifier Agent | Propose stage with confidence, reason and extracted facts from the new text, current stage, running summary and recent engagement entries (bounded) | FR-CLS-1 to FR-CLS-4 | Real code over `ChatModelProvider` |
| Summary and Next Action Agent | Update running engagement summary; propose next action | FR-SUM-1, FR-SUM-2 | Real code over `ChatModelProvider` |
| Scheduler Agent | **Extract the offered windows**, choose attendees, evaluate availability, rank, choose one of four outcomes, **prepare** drafts (never send) | FR-SCH-1 to FR-SCH-12 | Real code; all decisions in plain code (R4), model only for text |
| CRM Writer Agent | Persist every outcome through `CrmRepository` only | FR-CRM-1, FR-CRM-2 | Real code over `CrmRepository` |
| Providers (4) | The only seam to the outside world | R2, section 6 | Local working; live written, UNVERIFIED |
| CRM Store, audit tables | Persistence; audit entries are written through `CrmRepository` | section 6, FR-AUD-1 | SQLite (D3); separate tables, same database |

## 4. The four provider interfaces

There are **exactly four**. Agents and the Orchestrator never call Graph, Azure OpenAI, Ollama, the file system or a database directly (R2). Signatures are from requirements section 6 (language-neutral):

```
MailProvider
  list_new_messages(since)            -> [Email]
  get_message(id)                     -> Email
  create_reply_draft(thread, body)    -> DraftRef
  send_draft(draft_ref)               -> void        # only after approval

CalendarProvider
  get_availability(users, start, end) -> per user: {working_hours, busy_blocks: [{start, end, showAs}]}
  create_event(event)                 -> EventRef    # online meeting if live
  update_event(event_key, changes)    -> EventRef    # reschedule / add attendee
  find_event(event_key)               -> Event | None

ChatModelProvider
  complete(messages, output_schema)   -> validated structured result   # validate; retry on malformed output

CrmRepository
  customers, contacts, emails, engagements, meetings, stage_history, next_actions,
  scheduling_requests, audit entries
  + named queries: customers_by_stage, stale_leads(days), next_actions_due(range), customer_timeline(customer_id)
```

Working hours come from the `CalendarProvider` per user and are returned by `get_availability` next to the busy blocks (requirements sections 6 and 8; OQ-6 and OQ-28, resolved). If a user has none, the default is 08:00 to 17:00 Monday to Friday `America/Chicago`.

| Interface | Local (working in Phase 1) | Live (written, UNVERIFIED, off by default) |
|---|---|---|
| MailProvider | Parses `.eml` files (Message-ID, In-Reply-To, References, Date with offset, From/To/Cc, multipart bodies, attachments); replays in date order against the simulated clock | Microsoft Graph: change-notification subscription on the Inbox plus message delta as a safety net, get message, `createReply` draft then send after approval |
| CalendarProvider | Reads the mock calendar JSON (Graph event shape, `showAs` values, per-user `workingHours`); also records meetings the system creates so later availability sees them | Microsoft Graph: `getSchedule` (intersection done in our code; per-user working hours in its response), create event as Teams meeting, update event |
| ChatModelProvider | Ollama, `llama3.1:8b` (D5), set through `OLLAMA_MODEL` | Microsoft Agent Framework with a Foundry project endpoint (`FoundryChatClient`) or an Azure OpenAI resource endpoint (`agent_framework.openai` with Azure routing); which one depends on what IT provisions |
| CrmRepository | SQLite; also stores audit entries in separate tables of the same database | Azure SQL or Dataverse, undecided (D3) |

Rules: configuration selects the implementation per provider (FR-CFG-1); the active provider and model are recorded in the audit log for every call (FR-AUD-1); live providers are disabled by default, refuse to start without configuration and are labeled `implemented, unverified` (R3); everything local mode cannot truly produce is marked simulated (R10). An optional health-check fallback from live to local is allowed by section 6; it is not designed here.

## 5. The Orchestrator (D9)

D9: **a plain Python orchestrator behind an `Orchestrator` interface for Phase 1.** Reason (in `inputs/decisions.md` and requirements section 15): the pipeline is fixed with a human approval gate, which is easier to test, and the framework's workflow and Ollama packages are beta. Agent Framework Workflows are to be revisited once live access exists, and the outcome recorded; until then they are not used.

Responsibilities:

1. **Stage 1:** for each message, run the agents in a fixed order and persist results through the CRM Writer (section 6.1).
2. **Stage 2, approval handler:** after an explicit human decision arrives through the CRM API, run the approval steps (section 6.3). The handler, not an agent, calls `CalendarProvider` (create or update event) and `MailProvider.send_draft`. Agents only prepare drafts (OQ-2, resolved).
3. Create a run ID for each workflow run and record every agent run (agent, input reference, output, provider, model, timestamp, duration, approval decision, FR-AUD-1) **through `CrmRepository`** (OQ-1, resolved).
4. Keep processing the remaining emails when one fails and record the failure in the audit log (section 14).
5. Depend only on the four provider interfaces and the agents (R2). The CRM API calls the `Orchestrator` interface, never a concrete class.

Agent Framework appears only inside the live `ChatModelProvider` adapters (UNVERIFIED), so agent logic (prompts, schemas, scheduling code) is the same for live and local.

## 6. Data flow

The system has **two separate stages**. Replay never books or sends anything; booking and sending happen only in stage 2 after a person approves (R5; requirements section 10 note).

### 6.1 Stage 1: ingestion and analysis (replay or live arrival)

1. `MailProvider` supplies the next message. Local: the next `.eml` in date order; the simulated clock (`SIMULATED_NOW`, `SIMULATED_TZ`, default `2026-10-16T10:00:00` `America/Chicago`) decides which emails have arrived. Live: change notification or delta (UNVERIFIED).
2. **Ingestion Agent**: normalize to one `Email` (FR-ING-1); strip quoted history (FR-ING-2); drop exact duplicates by Message-ID (FR-ING-5); ignore unrelated internal mail (FR-ING-6); match a customer by sender address, domain, CC contacts and thread identifiers, or create a new lead (FR-ING-3, FR-ING-4); add new contacts (FR-ING-8); store attachment metadata (FR-ING-9); handle sent and received mail alike (FR-ING-7). It passes **only the cleaned new-email text** on to the Scheduler (OQ-11, resolved).
3. **Stage Classifier Agent**: input is the new email text plus the current stage, the running summary and the most recent engagement entries, **bounded to fit the context window** (FR-CLS-1; OQ-19, resolved). Output is schema-validated (FR-CLS-2). No change on an unanswered nudge or on historical dates (FR-CLS-3). A stage change is recorded with reason and source (FR-CLS-4).
4. **Summary and Next Action Agent**: update the running summary and propose a next action (FR-SUM-1, FR-SUM-2).
5. **Scheduler Agent**, when scheduling intent is detected (FR-SCH-1): **it extracts the offered windows itself** (FR-SCH-2; OQ-11), resolving relative dates ("next Thursday") against **the email's sent date in the sender's time zone** and using the simulated clock only to discard times already in the past (OQ-5, resolved). The sender's zone is the contact's stored zone; else an explicit zone in the email text; else candidates from the `Date` header offset plus hints in the text, **validated in code**; if still ambiguous the customer is asked to confirm (FR-SCH-2; OQ-7, resolved). It evaluates availability in code using each attendee's working hours from the `CalendarProvider` (OQ-6, resolved), chooses exactly one outcome (FR-SCH-7), and stores a scheduling request in state `pending` with reasons for every accepted and rejected slot and a **prepared draft reply** (FR-SCH-11; OQ-3). It writes nothing to calendar or mail.
6. **Request lifecycle at arrival (OQ-16, resolved):** a newer email in the same thread that offers new times sets the earlier pending request to `superseded`; a withdrawal sets it to `cancelled`; a request whose offered windows are all past by the simulated clock becomes `expired`. Old requests are kept for audit. The clock stays fixed at `SIMULATED_NOW` for a run (OQ-24), so a test that needs a request to expire injects a later clock (TR-10).
7. **CRM Writer Agent**: persist everything through `CrmRepository` only (FR-CRM-1).
8. **Orchestrator**: write an audit entry per agent run through `CrmRepository`; on a failure, record it and continue.

End state of stage 1: customers at their final stage from requirements section 10; for Adventure Works, Tailspin and Wingtip a `pending` scheduling request; no meeting created or changed; nothing sent.

### 6.2 Reading

The dashboard and, later, the Teams agent call the CRM API, which reads through `CrmRepository` named queries (`customers_by_stage`, `customer_timeline`, `next_actions_due`, `stale_leads(days)`) and the audit tables (FR-API-1, FR-UI-1 to FR-UI-4).

### 6.3 Stage 2: approval

A person reviews the proposed slot(s), attendees and draft reply (FR-APP-1, FR-UI-3) and approves, edits or rejects through the CRM API. **Edit** changes only the draft reply text, is recorded as an audit entry and does not change the request state; the recorded `decision` is only `approve` or `reject` (FR-APP-1, requirements section 9; OQ-4). For the outcomes that book (`recommend_slots`, `update_existing_meeting`) approval names exactly one proposed slot by id. The decision records `decided_by` and `decided_at` (FR-APP-3; requirements section 9).

On **approve**, the Orchestrator's approval handler runs **recorded, idempotent, retryable steps** (FR-APP-5; OQ-20, resolved). It records the intent first (decision, `decided_by`, `decided_at`, approval progress `in_progress`), then runs in order:

1. **Re-check availability** for the chosen slot (FR-APP-4; OQ-18, resolved; TR-11). If a conflict has appeared, **do not book**: mark the request `needs_review` with fresh options and stop. For `counter_propose` and `request_clarification` there is no chosen slot, so the step is recorded as not applicable (OQ-29).
2. **Create or update the event**: `recommend_slots` creates it (online meeting; join link marked simulated locally); `update_existing_meeting` finds and updates the existing event and adds new attendees (FR-APP-2, FR-SCH-9).
3. **Send the confirmation**: create the confirmation reply as a mailbox draft (`MailProvider.create_reply_draft`), then `send_draft` (FR-APP-2; OQ-25). For `counter_propose` and `request_clarification` this sends the prepared reply and creates no meeting.
4. **Write the CRM updates**: meeting record (FR-CRM-2), stage change with source "an approval" (StageHistory source, OQ-3), the request state and decision.

**Approval progress** is a field of the request: `not_started`, `in_progress`, `completed`, `partially_completed`. **Each step's result is recorded as an `AgentRun` audit entry linked to the request** (requirements section 9; OQ-27). The request `state` becomes `approved` once the re-check passes (`needs_review` on a conflict). If a step fails, the progress is `partially_completed` with the failed step visible, and a retry resumes without duplicates (TR-12); there is no automatic rollback in Phase 1. On **reject** nothing is created, updated or sent and the decision is recorded (OQ-26: state `rejected`, nothing automatic). Repeating an approval creates no duplicate meeting, event or sent message (R6, TR-6). After a re-check conflict the approval progress returns to `not_started`, the proposed slots are replaced by the fresh options (the earlier ones are kept in an audit entry), and the approver approves one of the fresh options or rejects (FR-APP-4; OQ-31, OQ-32). `superseded_by` links a superseded request to the newer one, and state reasons are read from audit entries (OQ-32).

Expected end state after approval (requirements section 10): Adventure Works creates the meeting and moves to Presentation/Follow-up; Tailspin sends the counter-proposal and stays in Engagement; Wingtip updates the existing event, adds Lisa Park and stays in Presentation/Follow-up. Step-by-step sequences are in [lld.md](lld.md).

## 7. Local versus live modes

| Aspect | Local (Phase 1, default, only mode that runs; R3) | Live (UNVERIFIED) |
|---|---|---|
| Mail | `.eml` replay | Microsoft Graph |
| Calendar | Mock calendar JSON plus meetings the system creates; working hours from the file's per-user `workingHours` | Microsoft Graph; working hours from the `getSchedule` response |
| Model | Ollama `llama3.1:8b` on a MacBook Air M4, 16 GB (D5); warm-up call because idle models unload; `qwen3:8b` compared later with TR-8 | Foundry or Azure OpenAI through Agent Framework |
| CRM store and audit | SQLite (audit in separate tables, same database) | Azure SQL or Dataverse (D3 deferred) |
| Join link | Generated locally, **marked simulated** (R10) | From the created Teams meeting |
| Observability | Structured logs with a run ID | App Insights and Foundry tracing |
| API access | Localhost only; approver is a configured local user name, no login (OQ-13) | Entra ID authentication, designed in [api.md](api.md), UNVERIFIED |
| Auth to Microsoft services | None needed | Entra ID; app-only for ingestion and availability, delegated for creating meetings; permissions and approver to be confirmed with IT (D7); mailbox scoping with Exchange Online's current mechanism (RBAC for Applications is described in Microsoft's docs; confirm with IT) |

Switching to live is a configuration change, not a rebuild (section 3). Live code is contract-tested against sample responses shaped like real output (TR-7), labeled contract tests, never live verification. What to verify on the first day with access is in [first_day_with_access.md](first_day_with_access.md).

**Honest status:** nothing live has run. Graph, Entra ID, Azure OpenAI and Foundry behavior in this design is UNVERIFIED. Phase 1 results come entirely from synthetic data.

## 8. Cross-cutting concerns

| Concern | Design position |
|---|---|
| Deterministic scheduling | Time zone conversion, availability intersection, duration, working hours and blocking rules are plain code; the model classifies, extracts and drafts text only (R4) |
| Human approval | Nothing booked, updated or sent without an explicit approval action (R5); policy `requireHumanApproval` is true; the approval handler is the only caller of `send_draft`, `create_event` and `update_event` |
| API safety (Phase 1) | Unauthenticated localhost API, so a web page open in the same browser must not be able to approve (R5, TR-13). Measures from `decisions.md` ("Additional rules"; details in [api.md](api.md) section 10.1): bind 127.0.0.1 only; check `Origin` and `Host`; CORS limited to the dashboard origin; JSON content type plus the `X-CRM-Token` header on approve, fetched from `GET /session` (OQ-33); a random per-run token that is held in memory and not stored in `.env` |
| Idempotency | Emails keyed by Message-ID; meetings by iCalUId or a stable internal key (R6, OQ-9); replaying the set twice yields identical CRM state **and approving the same request twice creates no duplicates** (TR-6) |
| Time | UTC plus IANA zone everywhere; never a fixed offset between regions (R9). Relative dates use the email's sent date in the sender's zone (FR-SCH-2); the simulated clock only discards past times and decides which emails have arrived |
| Simulation labels | Join links and similar values marked simulated in data and UI (R10) |
| Secrets | No `.env` reads by Claude; `example.env` lists keys; no secrets in code, logs, tests or docs (R7) |
| Reliability | Bounded retries on model and provider calls; the pipeline continues past a failed email and records it; approval failures leave a retryable `partially_completed` state (section 14, FR-APP-5) |
| Model output quality | Every model output is schema-validated and retried on malformed output (section 6, section 11); accuracy against the answer key is reported per run (TR-8) |
| Dataset integrity | Production code never reads the answer key or special-cases dataset values (R8) |

## 9. Technology decisions

| ID | Decision | Status |
|---|---|---|
| D1 | Backend language: Python | Resolved |
| D2 | Frontend: React (Vite + TypeScript) | Resolved |
| D3 | CRM store: SQLite locally; live store deferred behind `CrmRepository` | Resolved for Phase 1 |
| D4 | Coding agent: Claude Code | Resolved |
| D5 | Local model `llama3.1:8b` (16 GB MacBook Air M4); compare `qwen3:8b` via TR-8; warm-up in the smoke test | Resolved |
| D6 | Teams agent after the web dashboard | Resolved |
| D7 | Graph permission set and approver | Deferred to IT |
| D8 | Live hosting target | Deferred, out of Phase 1 |
| D9 | Plain Python orchestrator behind an `Orchestrator` interface; revisit Workflows after live access | Resolved (now also in requirements section 15) |

Pinned libraries are in `inputs/references.md` (exact versions, no ranges). A pip dry-run of the pinned set resolved without conflicts on 2026-10-16; it was not installed. The `agent-framework` meta-package must not be installed.

## 10. Traceability

| Requirement group | Primary components |
|---|---|
| FR-ING-1 to 9 | Ingestion Agent, MailProvider, CrmRepository |
| FR-CLS-1 to 4, FR-SUM-1 to 2 | Stage Classifier, Summary and Next Action, ChatModelProvider, CRM Writer |
| FR-SCH-1 to 12 | Scheduler Agent, scheduling code, CalendarProvider (availability and working hours), ChatModelProvider (text only), CrmRepository (request states). FR-SCH-12 is tested by TR-10 |
| FR-APP-1 to 5 | CRM API, Orchestrator approval handler, Dashboard scheduling panel. Tests: TR-11 (FR-APP-4), TR-12 (FR-APP-5), TR-6 (repeat approval), TR-13 (API safety) |
| FR-CRM-1, 2 | CRM Writer, CrmRepository |
| FR-API-1, FR-UI-1 to 5 | CRM API, Dashboard, Teams agent (D6) |
| FR-AUD-1, FR-CFG-1 | Orchestrator (audit through CrmRepository), configuration (`example.env`, `config/team.json`) |
| R1 to R12 | All; see the `crm-core-rules` skill |
| TR-1 to TR-13 | `tests/` folders `agents`, `backend`, `frontend`, `smoke`; see the `crm-testing-smoke` skill |

## 11. Quality: how this is tested

Exact-match tests against `expected_outcomes.json` (TR-1, TR-2); rubric scoring for summaries and drafts (TR-3); curl and scripted checks for every endpoint (TR-4); Playwright for the dashboard flows (TR-5); replay-twice **and approve-twice** idempotency (TR-6); live contract tests (TR-7); stage accuracy per run (TR-8). The smoke test (TR-9) runs after every slice: warm-up, then (a) replay with no approval (final stages plus a pending request for Adventure Works, Tailspin and Wingtip), then (b) explicit approval through the real approval endpoint, then a no-duplicates check. Four tests were added to requirements section 13: **TR-10** request lifecycle (pending, superseded by a newer email, cancelled by a withdrawal, expired when all windows are past; FR-SCH-12), **TR-11** approval re-check (a conflict after proposal gives `needs_review` with fresh options and books nothing; FR-APP-4), **TR-12** approval failure (a forced step failure leaves `partially_completed` with the failed step visible; retry completes without duplicates; FR-APP-5, R6), **TR-13** API safety (the approve endpoint rejects a foreign Origin, a missing `X-CRM-Token` header and a wrong content type; R5).

## 12. Design questions

### 12.1 Resolved (source: `inputs/decisions.md`, "Design decisions"; the requirements prevail where they differ)

Slice = the slice (requirements section 16) that first builds on the decision: 1 providers, local mail, SQLite; 2 ingestion and classifier; 3 scheduler; 4 CRM API then dashboard; 5 live providers; 6 live switch.

| ID | Decision | Slice |
|---|---|---|
| OQ-1 | Audit entries are written through `CrmRepository` (separate tables, same database in Phase 1). Still exactly four provider interfaces; the diagram is updated | 1 |
| OQ-2 | After approval, the Orchestrator's approval handler calls `CalendarProvider` (create or update event) and `MailProvider.send_draft`. Agents only prepare drafts | 3 |
| OQ-3 | `SchedulingRequest` gets draft reply, state, decision (approve or reject), `decided_by`, `decided_at`, approval progress, fresh options, state reason and `superseded_by`; `StageHistory` source can be an email or an approval (requirements section 9) | 1 (schema) |
| OQ-4 | Edit changes only the draft reply text and is an audit entry; the request state does not change (decision is approve or reject only). For outcomes that book, approval names exactly one proposed slot by id; a tentative fallback is listed last with its warning | 3, 4 |
| OQ-5 | `SIMULATED_NOW` and `SIMULATED_TZ` override `organization.simulationNow`. The clock decides which emails have arrived and which offered times are past. Relative dates resolve against the email's sent date in the sender's zone | 1, 3 |
| OQ-6 | Working hours come from the `CalendarProvider` per user (local: `workingHours` in `mock_calendars.json`; live: from Graph); `team.json` holds policy only; default 08:00-17:00 Mon-Fri `America/Chicago` | 1, 3 |
| OQ-7 | Customer's zone: the contact's stored zone; else an explicit zone in the email text; else candidates from the `Date` offset plus hints, validated in code; if ambiguous, ask the customer to confirm (FR-SCH-2) | 2, 3 |
| OQ-8 | Customer response status is `null` in local mode and shown as "not available (simulated)"; live reads attendee response status (UNVERIFIED) | 3 |
| OQ-9 | Local event key derived deterministically from the scheduling request id; live stores the iCalUId from Graph and keeps the internal key as the idempotency key | 3 |
| OQ-10 | Relevant customer attendees: CC'd external addresses at the customer's domain on the trigger email, shown to the approver before approval | 3 |
| OQ-11 | Window extraction belongs to the Scheduler Agent (FR-SCH-2); the Ingestion Agent only passes on the cleaned new-email text | 2, 3 |
| OQ-12 | `stale_leads(days)` takes its threshold from configuration (`STALE_LEAD_DAYS=14`, confirmed as the starting value); `next_actions_due(range)` is inclusive on both ends and returns open actions only | 1, 4 |
| OQ-13 | Phase 1 API listens on localhost only; the approver is a configured local user name (`APPROVER_USER`, no login), recorded on every approval. Entra ID authentication is designed in the docs, UNVERIFIED, built after live access | 4 |
| OQ-14 | Workflow trigger returns 202; one run at a time (a second request gets 409); scope all or one message; sequential in date order; progress read with `GET` | 4 |
| OQ-15 | Availability outside the mock calendar window is unknown and not offerable, reason "no calendar data" | 3 |
| OQ-16 | Seven request states (FR-SCH-12): `pending`, `approved`, `rejected`, `superseded`, `cancelled`, `expired`, `needs_review`. A newer email in the same thread offering new times supersedes the pending request; a withdrawal cancels it; it expires when all offered windows are past; old requests are kept | 3 |
| OQ-17 | Meeting status: `scheduled`, `rescheduled`, `cancelled`. Next action status: `open`, `done`, `dismissed` | 1 (schema) |
| OQ-18 | At approval, re-check availability for the chosen slot; on a conflict do not book, mark `needs_review` with fresh options (FR-APP-4; see OQ-31, OQ-32) | 3, 4 |
| OQ-19 | Classifier input: new email text plus current stage, running summary and the most recent engagement entries, bounded to fit the context window (FR-CLS-1) | 2 |
| OQ-20 | Approval steps in order: re-check, create or update event, send confirmation, write CRM updates. Each is idempotent and recorded; a failure leaves `partially_completed`, retryable, no automatic rollback in Phase 1, failed step shown. Progress values: OQ-27 | 4 |
| OQ-21 | `PROVIDER_MODE` sets the default for all four providers; a non-empty per-provider key overrides it | 1 |
| OQ-22 | Local updates to mock-JSON events live in a writable SQLite overlay keyed by event key, merged over the read-only JSON on read; the dataset files never change | 3 |
| OQ-23 | Running summary = append-only `Engagement` entries of type `note` marked as the running summary; the latest is current | 2 |
| OQ-24 | Simulated clock fixed at `SIMULATED_NOW` for the whole run. All 32 emails are dated before it (latest 16 Oct 07:12 CT, checked from the `Date` headers), so all replay; the three scenario windows (19 to 27 Oct) are after it, so TR-10 injects a later clock to test expiry | 1 |
| OQ-25 | The approval handler calls `create_reply_draft` then `send_draft` in the "send confirmation" step; before approval only the draft text exists on the request | 3 |
| OQ-26 | After a rejection: state `rejected`, nothing automatic, optional reason recorded, a new request only when a new email arrives | 4 |
| OQ-27 | Decision, `decided_by`, `decided_at` recorded at once; `state` becomes `approved` after the re-check passes (`needs_review` on a conflict); approval progress is `not_started`, `in_progress`, `completed`, `partially_completed`; each step's result is an `AgentRun` audit entry linked to the request | 4 |
| OQ-28 | `get_availability` returns per user `working_hours` next to `busy_blocks` (requirements section 6); no new interface | 1, 3 |
| OQ-29 | For `counter_propose` and `request_clarification` there is no chosen slot, so the re-check step is recorded as not applicable; it runs for `recommend_slots` and `update_existing_meeting` | 3 |
| OQ-30 | Port from configuration (`API_PORT`); no version prefix in Phase 1 | 4 |
| OQ-31 | After a re-check conflict, approval progress returns to `not_started`; the approver approves a fresh option or rejects (FR-APP-4) | 3, 4 |
| OQ-32 | Fresh options replace the proposed slots; the earlier ones are kept in an audit entry; state reasons are read from audit entries; `superseded_by` links to the newer request | 3, 4 |
| OQ-33 | The token header is `X-CRM-Token`, fetched from `GET /session` | 4 |
| Other | **API safety** (`decisions.md`, "Additional rules"; [api.md](api.md) section 10.1): bind 127.0.0.1 only; `Origin` and `Host` checks; CORS limited to `DASHBOARD_ORIGIN`; JSON content type plus `X-CRM-Token` on approve; a random per-run token not stored in `.env`; tested by TR-13. **Repeat approval** (R6, TR-6): approving the same request twice creates no duplicates | 4 |

Configuration keys that these decisions introduced are in `example.env`: `APPROVER_USER`, `API_PORT`, `DASHBOARD_ORIGIN`, `STALE_LEAD_DAYS`. The bind address is deliberately not configurable (a security invariant, not a setting), and the per-run token is deliberately not a setting.

### 12.2 Still open, with the slice that needs each item

There is **no numbered design question left open**. `decisions.md` says any question not listed there is resolved when the slice that needs it starts and is then recorded in that file. The items below were already marked open or deferred in the inputs, the requirements or the skills; none is a new question and **none blocks Slice 1 or Slice 2**, with the one exception noted (the TR-3 scorer, needed before the Slice 2 TR-3 tests). Items marked "verify" are documentation checks that the requirements demand before the code that uses them (section 0 item 5).

| Item | Source | Slice that needs it | What is needed |
|---|---|---|---|
| Python `zoneinfo` usage (and the need for the `tzdata` package) | `crm-scheduling-time-zones` skill | 3 (zone conversion); 1 only if stored times are converted there | Verify against official Python docs before writing conversion code |
| Python form of the Ollama warm-up call; exact `ollama` client usage for structured output | `crm-ollama-local-model` skill | 2 (model provider; smoke-test warm-up) | Verify against the `ollama` 0.6.3 docs before coding |
| Lock file and a real `pip check` after the first install of the pinned set | `inputs/references.md`; dry-run only so far | 1 (first install) | Do after the first install |
| TR-3 scorer (human spot-check or a judge model) and pass threshold | `crm-testing-smoke` skill ("ask the user") | 2 (summaries), 3 (drafts) | Your decision before the TR-3 tests are written |
| Review of the taste skill and graphify contents before any install | `crm-ui-quality`, `crm-context-management` skills | 4 (taste skill); developer tool (graphify) | Read at the pinned versions, then decide; record in `decisions.md` |
| Playwright usage | `crm-testing-smoke` skill (not in `references.md`) | 4 (TR-5) | Verify against Playwright docs before writing scripts |
| `evaluated_results` entries per window or per slot | [api.md](api.md) section 7.1 | 3 (plan) | Decide in the Slice 3 plan |
| `customers_by_stage` showing empty stages | [lld.md](lld.md) section 6 | 4 | Confirm with the UI |
| How a Teams user maps to an account owner | [api.md](api.md) section 6 | After the dashboard (D6) | With the Teams agent |
| Live CRM store (Azure SQL or Dataverse) | D3 | 5 | Deferred behind `CrmRepository` |
| Foundry or Azure OpenAI client, model name, API version, credential type | `crm-agent-framework-azure-openai` skill, first-day item 2 | 5, 6 | Depends on what IT provisions |
| Graph permission set, approver, mailbox scoping, notification URL | D7, D8 | 5, 6 | Agree with IT; do not scope in code |
| `iCalUId` lookup, reschedule `PATCH` body, Sent Items ingestion, customer response status | first-day items 4, 5, 12; `crm-graph-integration` skill | 5, 6 | Verify against Graph docs, then a real tenant |
| Entra ID design (token validation, who may approve, whether the per-run token is still needed) | [api.md](api.md) section 10.2, first-day item 14 | 6 | UNVERIFIED design; with IT |
| Optional health-check fallback from live to local | requirements section 6 | 6 | Not designed; optional |

## 13. Inconsistencies noticed in the inputs: all resolved

Audit of 2026-10-16 against the edited `REQUIREMENTS.md` and `decisions.md`. The docs and skills follow the inputs; nothing in the inputs was changed by this work.

| # | Inconsistency | Resolved by |
|---|---|---|
| 1 | Approval progress after a re-check conflict, and how `needs_review` continues, were unspecified | FR-APP-4 and OQ-31 (progress returns to `not_started`; approve a fresh option or reject) |
| 2 | Section 9 had no fields for fresh options, a state reason or the superseding request | Section 9 and OQ-3, OQ-32 |
| 3 | `decisions.md` OQ-16 listed six request states, FR-SCH-12 seven | OQ-16 now lists seven |
| 4 | TR-13 did not name the custom header | TR-13 and OQ-33: `X-CRM-Token` |
| 5 | `stale_leads` had no parameter while OQ-12 gave it a threshold | Section 6: `stale_leads(days)` |
| 6 | FR-APP-1 offered "edit" while section 9 limited `decision` to approve or reject | FR-APP-1: "approve, edit draft text, or reject. Editing changes only the draft text" |
| 7 | FR-APP-2 said "send the confirmation draft" while OQ-25 creates the draft at approval | FR-APP-2: "create the confirmation reply as a mailbox draft, and send it" |
| 8 | OQ-4 ("exactly one slot") versus OQ-29 (no chosen slot for two outcomes) | OQ-4: "for outcomes that book" |
| 9 | Typo in section 17 ("TR-13 pass pass") | Fixed in section 17 |

Earlier resolved: working hours source and the `get_availability` result (section 6, section 8, OQ-6, OQ-28); the section 8 heading; two simulated-clock sources (OQ-5); the diagram's audit store and mail-provider edges (OQ-1, OQ-2); window extraction owner (OQ-11); draft, `decided_by` and `decided_at` fields (OQ-3); approval progress values and per-step records; what "edit" does; the sender's time zone (FR-SCH-2); the missing tests (TR-10 to TR-13); D9; "customer history" wording (FR-CLS-1, OQ-19); repeat-approval check (TR-6).
