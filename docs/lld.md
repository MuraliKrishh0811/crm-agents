# Low-Level Design (LLD)

Status: draft for review, updated 2026-10-16 after every design question (OQ-1 to OQ-33) was resolved in `inputs/decisions.md` and `REQUIREMENTS.md` was edited to match (sections 6, 9, 13, 17; FR-SCH-2, FR-APP-1, FR-APP-2, FR-APP-4, TR-13). Phase 1 (local only). **No application code exists yet.** This document describes modules, interfaces, data and sequences in language-neutral terms; Python (D1) is the implementation language.

Conventions:

- `REQUIREMENTS.md` is authoritative; this document follows [hld.md](hld.md) and cites `FR-`, `TR-` and `R` IDs. `OQ-n` refers to the design questions in hld.md section 12.1 (numbers match `decisions.md`); all are resolved. What is still open, by slice, is in hld.md section 12.2. This document makes no new decisions.
- Module, operation and field names are **proposals for the Slice 1 plan** unless the requirements name them (the four provider interfaces, the nine data-model entities, the four scheduling outcomes, the seven request states, the named queries, the stage enumeration).
- Everything about live Microsoft Graph, Entra ID or Azure OpenAI/Foundry behavior is **UNVERIFIED**.
- Dates and times in examples come from requirements section 10. `CT` means `America/Chicago`.

## 1. Modules and dependency rules

Illustrative module boundaries (final layout belongs to the implementation plan):

| Module | Contents | I/O? |
|---|---|---|
| `domain` | Entities, enumerations, value objects (section 5) | No |
| `config` | Reads settings from the environment (keys in `example.env`) and policy from `config/team.json`; validates; no other module reads either | Config only |
| `providers.interfaces` | The **four** interfaces and their typed errors | No |
| `providers.local` | `.eml` mail, mock calendar, Ollama model, SQLite repository | Yes (files, HTTP to Ollama, SQLite) |
| `providers.live` | Graph mail, Graph calendar, Foundry model, Azure OpenAI model; Azure SQL or Dataverse repository undecided (D3). **UNVERIFIED** | Yes (disabled by default) |
| `scheduling` | Pure functions: zones and DST, window resolution, working-hours cap, availability evaluation, blocking rules, slot generation, ranking, outcome selection | No |
| `agents` | Ingestion, Stage Classifier, Summary and Next Action, Scheduler, CRM Writer. Agents only **prepare** drafts | Only through provider interfaces |
| `orchestrator` | `Orchestrator` interface (D9), its plain Python implementation, the stage 1 pipeline and the **approval handler** | Only through interfaces |
| `audit` | `AgentRun` and approval-step recording, run ID, structured logging; **writes through `CrmRepository`** (OQ-1) | Through `CrmRepository` |
| `api` | The CRM API (see [api.md](api.md)); binds 127.0.0.1 only in Phase 1 and applies the safety checks of api.md section 10.1 (Origin, Host, CORS, content type, `X-CRM-Token`) before any handler runs | HTTP |
| composition root | Chooses implementations from configuration | n/a |

Dependency rules (R2, R4, R8):

| Module | May depend on | Must not depend on |
|---|---|---|
| `domain`, `scheduling` | standard library, data types only | any provider, agent, file system, any clock other than an injected one |
| `agents` | `domain`, `scheduling`, `providers.interfaces` | `providers.local`, `providers.live`, Graph, Azure OpenAI, Ollama, Agent Framework, the file system, a database driver; **and never call `send_draft`, `create_event` or `update_event`** (OQ-2) |
| `orchestrator` | `agents`, `audit`, `domain`, `providers.interfaces` | concrete providers |
| `api` | `Orchestrator` interface, `CrmRepository` interface | concrete providers, agents directly |
| `providers.live`, `providers.local` | `domain`, `providers.interfaces`, their own SDK or file reads | `agents`, `orchestrator` |
| production code (all) | - | `data/synthetic/expected/expected_outcomes.json`, dataset client names, email IDs or dates (R8); only tests read the answer key |

"Now" is injected from configuration into `scheduling` and the agents; they never read the system clock.

## 2. Interface contracts

### 2.1 MailProvider

| Operation | Input | Output | Notes |
|---|---|---|---|
| `list_new_messages(since)` | A point in time | `[Email]` in date order | Local: `.eml` files not yet delivered, replayed in date order; the simulated clock decides which emails have arrived (OQ-5). The clock stays fixed at `SIMULATED_NOW` for a run (OQ-24). Live: subscription notification plus delta safety net (UNVERIFIED) |
| `get_message(id)` | Provider message id | `Email` | Local: parse headers (Message-ID, In-Reply-To, References, Date with offset, From/To/Cc), multipart bodies, attachments |
| `create_reply_draft(thread, body)` | Thread reference, reply text | `DraftRef` | Live: `createReply` (UNVERIFIED). Called by the approval handler, immediately before `send_draft` (OQ-25); no mailbox draft exists before approval |
| `send_draft(draft_ref)` | `DraftRef` | nothing | **Only after approval** (R5). Called **only by the Orchestrator's approval handler** (OQ-2); the interface has no approval parameter, so this restriction is the enforcement |

Normalized `Email` (FR-ING-1): Message-ID; thread identifiers (In-Reply-To, References, conversation ID where the provider has one); direction (received or sent, FR-ING-7); sender; to; cc; sent time as UTC plus the zone information available (the `Date` header offset; the sender's zone is derived by the Scheduler, OQ-7); subject; **new body** with quoted text removed (FR-ING-2); the original body as received; attachment names and metadata (FR-ING-9).

### 2.2 CalendarProvider

| Operation | Input | Output | Notes |
|---|---|---|---|
| `get_availability(users, start, end)` | Internal users, UTC range | Per user: `{working_hours, busy_blocks: [{start, end, showAs}]}` (requirements section 6; OQ-28) | Returns the user's working hours and events as the provider sees them. **Blocking rules are not applied here**; they are applied in `scheduling` (R4). `showAs` is one of `free`, `tentative`, `busy`, `oof`, `workingElsewhere`. **Working hours come from this provider per user** (OQ-6); a user without them gets the default. Outside the mock window (2026-10-19 to 2026-10-31) the availability is unknown and not offerable, reason "no calendar data" (OQ-15) |
| `create_event(event)` | Subject, UTC start/end plus zone, internal and external attendees, online-meeting flag | `EventRef` (event key) | Idempotent on the event key (R6, OQ-9: local key derived from the scheduling request id; live stores the iCalUId from Graph). Local: persists the event so later availability sees it; join link generated and **marked simulated** (R10). Live: Teams online meeting (UNVERIFIED). Called only by the approval handler |
| `update_event(event_key, changes)` | Event key, changes (new time, added attendees) | `EventRef` | Never creates a second event (FR-SCH-9). Local: updates to events that came from the mock JSON go to a writable SQLite overlay keyed by event key and merged over the read-only JSON on read; the dataset files never change (OQ-22). Called only by the approval handler |
| `find_events(users, attendee_addresses, start, end)` | Assigned internal users, the external addresses from the trigger email (and its sender's domain as a fallback), a UTC range | `[Event]`, each with event key, start, end, status and attendee addresses | Added by D11 (requirements section 6, FR-SCH-9). **Local:** reads `attendees` and the event key (`iCalUId`) from the mock JSON, **merges the SQLite overlay** (OQ-22: updated events as updated, events the system created, cancelled status) and returns one `Event` per event key even when several attendees' calendars hold it. Returns only events that include an address from the given list as an attendee (case-insensitive); the domain fallback is applied by the caller with the same operation. Unknown outside the mock window (OQ-15). **Live:** Graph `calendarView` per user (`attendees` and `iCalUId` are properties of the event resource); **UNVERIFIED**, see the `crm-graph-integration` skill snippet `calendar-view-events.md` |
| `find_event(event_key)` | Event key (iCalUId or stable internal key) | `Event` or none | Live lookup by iCalUId is **not documented** (see the `crm-graph-integration` skill and [first_day_with_access.md](first_day_with_access.md)); UNVERIFIED |

Observed mock data shape (`calendars/mock_calendars.json`; `attendees` is a list of address strings, not Graph attendee objects, and there is no `isCancelled` field, so the local provider treats a missing value as not cancelled): per internal user a `workingHours` block (days, start, end, IANA zone) and an `events` list; each event has `id`, `iCalUId`, `subject`, `start` and `end` (`dateTime` plus IANA `timeZone`), `showAs`, `isAllDay`, `isOnlineMeeting`, `organizer`, `attendees`. The same meeting appears in each attendee's calendar with a different `id` and the same `iCalUId`, which matches keying meetings by iCalUId. A user without `workingHours` defaults to 08:00-17:00 Mon-Fri `America/Chicago` (OQ-6).

### 2.3 ChatModelProvider

`complete(messages, output_schema) -> validated structured result`. Contract for every implementation:

1. Ask the model for output in the given schema.
2. Validate the result against the schema; on malformed output retry within a **bounded** budget; after the budget is spent raise a typed error (never return unvalidated text).
3. Report provider and model used so the Orchestrator can record them (FR-AUD-1).
4. Never be used for time zone conversion, availability intersection or slot choice (R4).

Local (Ollama, `llama3.1:8b`, `OLLAMA_MODEL`): small explicit context window, structured output via a JSON schema, a warm-up call at start and at the start of the smoke test because idle models unload (see the `crm-ollama-local-model` skill). Live (UNVERIFIED): Agent Framework `Agent` with `response_format`, using `FoundryChatClient` or an Azure-routed `agent_framework.openai` client, chosen by what IT provisions (see the `crm-agent-framework-azure-openai` skill). Agent Framework is visible only inside these adapters.

### 2.4 CrmRepository

Persistence for the nine entities in section 5, the named queries (section 6) and **audit entries** (separate tables, same database in Phase 1, OQ-1). Writes are **upserts on natural keys** so a repeat is safe (R6): emails by Message-ID, meetings by event key, contacts by customer and email address. The CRM Writer is the only writer of domain outcomes (FR-CRM-1); the `audit` module writes audit entries through the same interface.

### 2.5 Orchestrator (D9)

Proposed operations (names illustrative):

| Operation | Purpose |
|---|---|
| `run(scope)` | Run stage 1 for a set of messages (the workflow trigger, FR-API-1); returns a run ID. Accepted semantics (OQ-14): returns 202, one run at a time (a second request gets 409), all messages or one, sequential in date order, progress read with `GET` |
| `process_message(message)` | Stage 1 for one message through the fixed pipeline |
| `get_run(run_id)` | Progress and failures for a run |
| `approve(request_id, decided_by, slot id, idempotency key)` | Stage 2: the **approval handler** (section 7.2); `decided_by` is the configured local user in Phase 1 (OQ-13); for outcomes that book, the slot id names exactly one proposed slot (OQ-4) |
| `reject(request_id, decided_by, reason)` | Record a rejection (state `rejected`, OQ-26); no external write |
| `edit(request_id, new draft text)` | Change **only the draft reply text**; recorded as an audit entry; the request state does not change (OQ-4; FR-APP-1; requirements section 9) |
| `retry_approval(request_id)` | Resume a `partially_completed` approval from the failed step (FR-APP-5); may be the same call as `approve` (TR-12) |

### 2.6 Agent contracts

| Agent | Input | Output | Providers used |
|---|---|---|---|
| Ingestion | `Email` | Normalized stored email, matched or new customer, new contacts, or a "duplicate" or "ignored" result; **the cleaned new-email text for downstream agents** (OQ-11) | MailProvider (read), CrmRepository (through CRM Writer) |
| Stage Classifier | New email text, current stage, running summary, most recent engagement entries, **bounded to fit the context window** (FR-CLS-1, OQ-19) | Schema-validated: proposed stage, confidence, short reason, extracted facts such as user count, current CRM, decision timeline, loss reason (FR-CLS-2) | ChatModelProvider |
| Summary and Next Action | New text, running summary (kept as append-only `note` engagement entries, the latest being current; OQ-23) | Updated summary; next action (description, optional due date) (FR-SUM-1, FR-SUM-2) | ChatModelProvider |
| Scheduler | Cleaned new-email text with its sent date, the customer, contacts (with stored time zones), policy | A scheduling request in state `pending` with exactly one outcome, reasons and a **prepared draft reply** (FR-SCH-7, FR-SCH-11), or "no scheduling intent". It also decides supersede and cancel when a newer email arrives (section 7.1) | ChatModelProvider (text only), CalendarProvider |
| CRM Writer | Domain results | Persisted records (stage history, engagement entries, meetings, contacts, next actions, scheduling requests) | CrmRepository |

### 2.7 Scheduler internals

The Scheduler agent uses the model for two text tasks only: (a) detect intent and **extract the offered windows** as stated (date phrase, start and end text, zone hint, stated preferences such as "mornings"); (b) draft reply prose around placeholders. Everything else is plain code in `scheduling` (R4):

1. **Resolve** each stated window to a concrete range with an explicit IANA zone and convert to UTC (FR-SCH-2). **Relative dates ("next Thursday") resolve against the email's sent date in the sender's time zone; the simulated clock is used only to discard times already in the past** (OQ-5). **The sender's zone** is taken in this order (FR-SCH-2; OQ-7): the contact's stored zone; an explicit zone in the email text; otherwise candidate zones implied by the `Date` header offset plus hints in the text, **validated in code** against the IANA database; if it is still ambiguous the Scheduler asks the customer to confirm instead of guessing. Times found only in quoted or historical text never trigger scheduling.
2. **Cap** open-ended windows by each attendee's working hours (FR-SCH-6), taken from the `CalendarProvider` per user, default 08:00-17:00 Mon-Fri `America/Chicago` (OQ-6), returned by `get_availability` (OQ-28).
3. **Select attendees** from assignment rules in `config/team.json`: `assignmentRules.byClientDomain` (internal members per customer domain) with a default; add relevant CC'd customer contacts as external attendees: CC'd external addresses at the customer's domain on the trigger email, shown to the approver before approval (FR-SCH-4; OQ-10).
4. **Read availability** through `CalendarProvider` for **assigned internal attendees only**; an unassigned team member never blocks (FR-SCH-10).
   **For a reschedule, locate the existing meeting first with `find_events`** (FR-SCH-9, D11), in plain code: candidates are upcoming (starting at or after the simulated now), non-cancelled events on the assigned attendees' calendars that include an external attendee address from the trigger email (From, To, Cc), falling back to the sender's domain read from that email; one match is the target (`update_existing_meeting`, `target_event_key` set); several are narrowed by the original meeting day the email mentions (the model extracts the phrase as text only; code resolves it with the sent-date rule of FR-SCH-2); anything else is `request_clarification` (a draft asking which meeting is meant), and nothing is created, never a duplicate. No customer names, event keys or dates from the dataset appear in this code (R8).
5. **Apply blocking rules** from `schedulingPolicy`: hard `busy`, `oof`; soft `tentative` (lower-ranked fallback, always shown with a warning, never silently ignored); non-blocking `free`, `workingElsewhere` (FR-SCH-5).
6. **Generate and rank** candidate slots of the meeting duration on the slot granularity, **at most 3** suggestions (FR-SCH-6); duration comes from the default durations by meeting type in policy. A tentative fallback is listed last with its warning (OQ-4).
7. **Choose exactly one outcome**: `recommend_slots`, `counter_propose` (no overlap), `request_clarification` (no concrete times), `update_existing_meeting` (reschedule request) (FR-SCH-7).
8. **Record a human-readable reason** for every accepted and rejected slot (FR-SCH-11).
9. **Prepare** the reply: clarification question (FR-SCH-3), counter-proposal with 2 or 3 mutual slots in the customer's zone within stated preferences (FR-SCH-8), or confirmation text. Code inserts the formatted times; the model does not format or convert times. The draft is stored on the request; **nothing is sent by an agent** (OQ-2).

## 3. Configuration

| Source | Used for |
|---|---|
| `example.env` keys | `PROVIDER_MODE`, `MAIL_PROVIDER`, `CALENDAR_PROVIDER`, `MODEL_PROVIDER` (`ollama`, `foundry`, `azure_openai`; precedence OQ-21); Ollama settings (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_TEMPERATURE`, `OLLAMA_MAX_RETRIES`, `OLLAMA_REQUEST_TIMEOUT_S`, `OLLAMA_WARMUP_ON_START`); live model settings (`FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`); Graph (`GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`); `DATABASE_URL`; `DATA_DIR`; `SIMULATED_NOW`, `SIMULATED_TZ` (**override** `organization.simulationNow` in `team.json`, OQ-5); `LOG_LEVEL`; and the keys added for the accepted decisions: `APPROVER_USER` (the configured approver, OQ-13), `API_PORT` (OQ-30), `DASHBOARD_ORIGIN` (the one origin CORS allows, api.md section 10.1) and `STALE_LEAD_DAYS` (the `stale_leads` threshold, OQ-12, starting value 14). **Deliberately not settings:** the bind address (always 127.0.0.1) and the per-run API token (generated at start, held in memory, never in `.env`, logs or files) |
| `config/team.json` | `organization` (name, domain, time zone, `simulationNow`), `members`, `assignmentRules`, and `schedulingPolicy` (durations by type, slot granularity, hard/soft/non-blocking lists, `respectInternalWorkingHours`, `maxSuggestions`, `requireHumanApproval`). **Policy only**: it holds no working hours (OQ-6) |
| `calendars/mock_calendars.json` | Local calendar data, including per-user `workingHours` |

Precedence of `PROVIDER_MODE` and the per-provider keys: `PROVIDER_MODE` sets the default for all four providers and a non-empty per-provider key overrides it (OQ-21). Policy values are read at runtime and never hardcoded. Live settings are validated before a live client is constructed; local mode needs none. Claude never reads `.env`; the application loads its own settings (R7).

## 4. Time handling (R9)

- Every timestamp is stored as **UTC plus the relevant IANA zone**. Conversion uses the IANA zone database, never a fixed offset.
- Example of why (requirements section 10): the UK leaves summer time on 2026-10-25 and the US on 2026-11-01, so London to Chicago is **6 hours before and 5 hours after**.
- **Reference for relative dates:** the email's sent date in the sender's time zone (FR-SCH-2). The simulated clock decides which emails have arrived and which offered times are already past.
- Zone abbreviations in email text are hints; the sender's IANA zone is derived in the order given in section 2.7 and validated in code (FR-SCH-2, OQ-7). If it is still ambiguous, the customer is asked to confirm; the Scheduler does not guess.
- Customer-facing times are displayed in the customer's zone (FR-SCH-8). Showing the customer's zone and the organization zone side by side in the scheduling panel is a proposal in the `crm-ui-quality` skill; FR-UI-3 does not require it.

## 5. Data model (store-neutral, requirements section 9)

Adapters (SQLite now; Azure SQL or Dataverse later) map these entities. Field names and keys are indicative proposals, except Message-ID and the meeting event key, which R6 names.

| Entity | Fields | Key and uniqueness |
|---|---|---|
| **Customer** | id; company name; email domain; stage (enumeration); account owner; created date; loss reason | id |
| **Contact** | id; customer id; name; email; role/title; time zone (if known) | unique per (customer, email) |
| **EmailMessage** | Message-ID; thread identifiers; direction (received or sent); sender; to; cc; sent time and zone; subject; new body (quoted text removed); attachment names | Message-ID unique (FR-ING-5, R6) |
| **Engagement** | id; customer id; type (email, meeting, note); summary; timestamp; source reference | id |
| **Meeting** | id; customer id; event key (iCalUId); subject; start and end UTC; attendees (internal and external); join link with a simulated flag; status; customer response status | event key unique (R6) |
| **StageHistory** | customer id; previous stage; new stage; timestamp; reason; **source (an email, or an approval)** | one row per stage change (FR-CLS-4) |
| **NextAction** | customer id; description; due date; status | id |
| **SchedulingRequest** | customer id; trigger email; parsed customer slots; attendees considered; evaluated results with reasons; proposed slots; outcome type; **draft reply; state; decision (approve or reject); decided_by; decided_at; approval progress; fresh options; state reason; superseded_by** | id; at most one per trigger email and outcome (proposal, supports replay idempotency, R6) |
| **AgentRun** | agent; input reference; output; provider; model; timestamp; duration; approval decision | id; also carries the workflow run ID. **Each approval step's result is an `AgentRun` linked to the request** (the input reference is the request id; requirements section 9) |

Enumerations: **stage** = Initial Lead, Engagement, Presentation/Follow-up, Converted, Not Converted (section 5). **direction** = received, sent. **engagement type** = email, meeting, note. **showAs** = free, tentative, busy, oof, workingElsewhere. **outcome** = `recommend_slots`, `counter_propose`, `request_clarification`, `update_existing_meeting`. **request state** (FR-SCH-12) = `pending`, `approved`, `rejected`, `superseded`, `cancelled`, `expired`, `needs_review`. **decision** = approve, reject (or none yet). **approval progress** = `not_started`, `in_progress`, `completed`, `partially_completed`. **meeting status** = `scheduled`, `rescheduled`, `cancelled`; **next action status** = `open`, `done`, `dismissed` (OQ-17).

**Approval** (FR-APP-4, FR-APP-5; OQ-20 and OQ-27): the decision, `decided_by` and `decided_at` are recorded at once and the progress becomes `in_progress`. The request `state` becomes `approved` once the availability re-check passes (or `needs_review` on a conflict). The four steps (`recheck_availability`, `create_or_update_event`, `send_confirmation`, `write_crm_updates`) each write an `AgentRun` linked to the request; the step status labels used in the API (`succeeded`, `failed`, `not_applicable`, `conflict`) are derived from those entries. **Edit** changes only the draft reply text, is recorded as an audit entry and does not change the state (FR-APP-1). **After a re-check conflict** the approval progress returns to `not_started` (OQ-31, FR-APP-4); the **fresh options replace the proposed slots** and the earlier ones are kept in an audit entry; state reasons are read from audit entries; `superseded_by` is the id of the newer request (OQ-32; requirements section 9).

### 5.1 Request state transitions (FR-SCH-12, decisions.md OQ-16 and OQ-18)

| From | To | Trigger |
|---|---|---|
| (new) | `pending` | Scheduler stores a request after stage 1 |
| `pending` | `superseded` | A newer email in the same thread offers new times |
| `pending` | `cancelled` | A withdrawal arrives |
| `pending` | `expired` | All offered windows are in the past by the simulated clock |
| `pending` | `rejected` | A person rejects |
| `pending` | `approved` | A person approves and the availability re-check passes (OQ-27); the approval progress then runs on to `completed` or `partially_completed` |
| `pending` | `needs_review` | At approval the availability re-check finds a conflict; fresh options are prepared; nothing is booked or sent (FR-APP-4) |
| `needs_review` | `approved` or `rejected` | The approver approves one of the fresh options (its re-check passes, then `approved`; a new conflict returns to `needs_review`) or rejects (OQ-31, FR-APP-4) |

Old requests are kept for audit. **Edit does not appear here because it changes no state** (section 9). A `partially_completed` approval keeps the state `approved`; a retry resumes at the failed step (FR-APP-5).

## 6. CrmRepository named queries

| Query | Meaning | Used by | Notes |
|---|---|---|---|
| `customers_by_stage` | Customers grouped by stage | Pipeline view (FR-UI-1) | All five stages appear, including empty ones (to confirm with the UI) |
| `stale_leads` | Leads with no recent activity | Dashboard or Teams (not specified) | Takes a threshold in days from configuration, `STALE_LEAD_DAYS`, starting value 14 (OQ-12) |
| `next_actions_due(range)` | Next actions with a due date in the range | "My next actions this week" (FR-UI-5) | Inclusive on both ends; open actions only (OQ-12) |
| `customer_timeline(customer_id)` | Emails and meetings for one customer in time order | Customer detail (FR-UI-2) | Stage history is shown alongside, not required in the timeline |

Plus keyed lookups the pipeline needs: customer by domain or contact email (FR-ING-3), email by Message-ID (FR-ING-5), thread lookups, scheduling requests by state, customer or thread, meeting by event key, audit entries by run, agent or customer, and the most recent engagement entries for the classifier's bounded input (FR-CLS-1).

## 7. Sequences

### 7.1 Stage 1 for one message

```
Orchestrator -> MailProvider: list_new_messages / get_message          -> Email
Orchestrator -> Ingestion:   process(Email)
   Ingestion -> CrmRepository: email by Message-ID?                     (exists: stop, FR-ING-5)
   Ingestion: internal noise? (stop, FR-ING-6)   strip quoted text (FR-ING-2)
   Ingestion -> CrmRepository: match customer or create lead (FR-ING-3, 4); add contacts (FR-ING-8)
   Ingestion -> Orchestrator: cleaned new-email text (OQ-11)
Orchestrator -> Stage Classifier: complete(...) via ChatModelProvider
        input: new text + current stage + running summary + recent engagement entries, bounded (FR-CLS-1)
        output: proposal (FR-CLS-2)
Orchestrator -> CRM Writer: record stage change if any (FR-CLS-4); engagement entry (FR-ING-7)
Orchestrator -> Summary and Next Action: summary, next action          (FR-SUM-1, 2)
Orchestrator -> Scheduler:   scheduling intent?                        (FR-SCH-1)
   Scheduler -> ChatModelProvider: extract windows (text only)         (FR-SCH-2, OQ-11)
   Scheduler (code): derive the sender's zone (contact zone, else explicit zone in text, else Date offset
                     plus hints validated in code; ambiguous -> request_clarification asking to confirm, OQ-7);
                     resolve relative dates against the email's sent date in that zone;
                     discard windows already past by the simulated clock; convert to UTC
   Scheduler -> CalendarProvider: get_availability(assigned users, range) -> per user working_hours + busy_blocks
   Scheduler (code): cap, apply blocking rules, rank, choose outcome, reasons
   Scheduler -> ChatModelProvider: draft prose; code inserts the formatted times
   Scheduler: newer email in the same thread offering new times? -> earlier pending request superseded
              withdrawal? -> earlier pending request cancelled
Orchestrator -> CRM Writer:  persist the request in state pending, with the prepared draft (FR-SCH-11, FR-CRM-1)
Orchestrator -> CrmRepository: AgentRun per agent                      (FR-AUD-1, OQ-1)
```

A failure in any step is recorded in the audit log and the Orchestrator continues with the next message (section 14). Nothing in stage 1 creates or changes a calendar event or sends mail. Requests whose offered windows are all past are set to `expired`.

### 7.2 Stage 2: the approval handler (FR-APP-2 to FR-APP-5)

Called only after an explicit human decision through the CRM API (the API has already passed its safety checks, api.md section 10.1, TR-13). Common to all outcomes:

```
API -> Orchestrator: approve(request_id, decided_by, slot id, idempotency key)
Handler: already completed for this request?  -> return the recorded result (R6)
Handler -> CrmRepository: record intent: decision=approve, decided_by, decided_at; approval progress = in_progress
Step 1  recheck_availability for the chosen slot             (FR-APP-4; not applicable if no chosen slot, OQ-29)
          conflict -> do NOT book or send; request -> needs_review with fresh options; stop   (TR-11)
          passed   -> request state = approved (OQ-27)
Step 2  create_or_update_event: CalendarProvider.create_event / update_event   (outcomes that book; else n/a)
Step 3  send_confirmation: MailProvider.create_reply_draft, then send_draft     (OQ-25)
Step 4  write_crm_updates: CRM Writer: meeting record (FR-CRM-2), stage change with source = this approval,
          engagement entries
Each step: idempotent, its result recorded as an AgentRun linked to the request (FR-APP-5, section 9).
All steps done -> approval progress = completed.
A step fails -> approval progress = partially_completed, failed step visible; a retry resumes from the
failed step without duplicates (TR-12); no automatic rollback in Phase 1.
Orchestrator -> CrmRepository: AgentRun for the approval, including the approval decision (FR-AUD-1)
```

After a conflict at step 1 the approval progress returns to `not_started`, the fresh options replace the proposed slots (the earlier ones go to an audit entry), and the approver approves one fresh option or rejects (OQ-31, OQ-32, FR-APP-4).

Sent mail also updates engagement history (FR-ING-7); when the same message later arrives from Sent Items it is deduplicated by Message-ID (FR-ING-5).

### 7.3 SCH-ADV: Adventure Works Cycles (60 min, trigger email A05, client in London; team Emily and Raj)

**Stage 1: replay, no approval**

1. Ingestion matches the customer by domain and contacts and adds Sophie Turner as a contact (section 10; FR-ING-3, FR-ING-8). Oliver Bennett is the customer contact in London. The classifier keeps the customer in **Engagement** and captures 60 users, Dynamics 365 and a decision by end of Q4 (FR-CLS-2).
2. The Scheduler detects intent in the cleaned new text only (FR-SCH-1) and extracts three windows (model, text only): Tue Oct 20 15:00-17:00 BST; Wed Oct 21 14:00-15:30 BST; Tue Oct 27 14:00-16:00 GMT. The sender's zone is derived as `Europe/London` (OQ-7: contact zone if stored, else the explicit BST and GMT in the text, else the `Date` offset plus hints, validated in code). The windows are explicit dates; any relative phrase would resolve against the email's sent date.
3. Code converts with the IANA database to CT: 09:00-11:00 on Oct 20; 08:00-09:30 on Oct 21; 09:00-11:00 on Oct 27. The offset is 6 hours before Oct 25 and 5 hours after (the DST trap; a fixed 6-hour offset would give 08:00-09:00 CT on Oct 27, outside the window, R9). All three windows are in the future by the simulated clock, so none is discarded.
4. Attendees: Emily and Raj (assignment rule for the domain) plus external Oliver Bennett and Sophie Turner. Availability and working hours are read for Emily and Raj only (FR-SCH-10).
5. Evaluation, with reasons stored (FR-SCH-11):
   - Oct 20 09:00-11:00 CT: **rejected**, Emily busy until 10:30.
   - Oct 21 08:00-09:30 CT: **fallback only, with a warning**, Raj tentative 08:30-09:00 (soft block).
   - Oct 27 09:00-11:00 CT: **selected 10:00-11:00 CT** (15:00-16:00 GMT); Raj is busy 09:00-10:00 (the Fabrikam kickoff).
6. Outcome `recommend_slots`; the proposals are the selected slot first and the Oct 21 tentative fallback **listed last with its warning** (OQ-4; the answer key records it as `fallback_with_warning`); the draft reply is prepared and stored; the request is `pending`. No meeting exists; nothing is sent.

**Stage 2: approval handler** (explicit call to the approval endpoint)

1. Record intent: decision `approve`, `decided_by` (the configured local user), `decided_at`; approval progress `in_progress`. The approval names the one proposed slot (10:00-11:00 CT on Oct 27) by id.
2. Re-check availability for 10:00-11:00 CT on Oct 27 (FR-APP-4). If a conflict has appeared, nothing is booked or sent and the request becomes `needs_review` with fresh options (TR-11); otherwise the state becomes `approved`.
3. `CalendarProvider.create_event`: 10:00-11:00 CT (stored as 15:00-16:00 UTC), attendees Emily, Raj, Oliver Bennett, Sophie Turner, online meeting. Local mode generates a join link and **marks it simulated** (R10); live would create a Teams meeting (UNVERIFIED). The event key is derived from the scheduling request id locally (OQ-9), so a repeat creates no duplicate (R6).
4. `MailProvider.create_reply_draft` then `send_draft`: the confirmation reply (OQ-25).
5. CRM Writer: the `Meeting` (FR-CRM-2; customer response status `null`, shown as "not available (simulated)", OQ-8), the move to **Presentation/Follow-up** with a stage-history entry whose source is this approval; the decision, `decided_by` and `decided_at` were recorded at step 1 (FR-APP-3). Progress becomes `completed`.
6. The local `CalendarProvider` keeps the created meeting so later availability sees it. A failure in step 3, 4 or 5 leaves the approval `partially_completed`; a retry resumes there without a second meeting (TR-12).

### 7.4 SCH-TAIL: Tailspin Toys (30 min, trigger email T03, client in Denver; team Sarah and David)

**Stage 1: replay, no approval**

1. The first email is vague (no concrete times): the Scheduler chooses `request_clarification`, prepares a clarification and **guesses nothing** (FR-SCH-3, TR-1). The request is `pending`; because R5 covers every send, it needs an approval before anything is sent (OQ-16). The dataset README describes this customer as a new lead; the stage at the end of replay is Engagement (section 10).
2. Trigger email T03 offers two windows (customer zone `America/Denver`, OQ-7): Mon Oct 19 09:00-10:00 MDT and Thu Oct 22 08:00-09:00 MDT. If T03 is in the same thread as the earlier vague email, the earlier clarification request becomes `superseded` (kept for audit) and only the SCH-TAIL request is `pending` (OQ-16; section 10 says replay ends with a pending scheduling request).
3. Code converts to CT: 10:00-11:00 on Oct 19; 09:00-10:00 on Oct 22.
4. Availability and working hours for Sarah and David only. Evaluation with reasons:
   - Oct 19: **rejected**, Sarah out of office all day (`oof`, hard block).
   - Oct 22: **rejected**, David busy 08:30-10:00.
5. No overlap: outcome **`counter_propose`**. The Scheduler finds 2 or 3 mutual 30-minute slots within the customer's stated preference (mornings: 08:00-12:00 MDT, 09:00-13:00 CT), none on Oct 19. Valid examples from section 10: Oct 20 10:00 CT, Oct 21 09:00 CT, Oct 22 10:00 CT. The draft reply shows them **in Mountain time** (code formats the times, FR-SCH-8).
6. The request is `pending` with the prepared draft. **No meeting is created.**

**Stage 2: approval handler**

1. Record intent (decision `approve`, `decided_by`, `decided_at`; progress `in_progress`).
2. Re-check and calendar steps: there is no chosen slot and no event, so they are recorded as not applicable (OQ-29).
3. `MailProvider.create_reply_draft` then `send_draft`: the counter-proposal.
4. CRM Writer: request state, an engagement entry for the sent email. The stage stays **Engagement**; no meeting.

### 7.5 SCH-WING: Wingtip Toys (60 min, trigger email W06, client in New York; team Emily and David)

**Stage 1: replay, no approval**

1. Customer matched; James Carter is the customer contact in New York and Lisa Park is added as a contact (section 10; FR-ING-8). The customer is in **Presentation/Follow-up**; an existing walkthrough exists, event key `wingtip-walkthrough-20261022`, currently Oct 22 13:00-14:00 CT, with `james.carter@wingtiptoys.com` as its external attendee on Emily's and David's calendars (one event key).
2. The Scheduler detects a **reschedule** request and extracts two windows: Wed Oct 21 after 15:00 EDT (open-ended) and Fri Oct 23 11:00-13:00 EDT.
3. Code converts and caps with each attendee's working hours: Oct 21 becomes 14:00-17:00 CT (capped at 17:00); Oct 23 becomes 10:00-12:00 CT.
4. Availability for Emily and David only. Evaluation:
   - Oct 21: **rejected**; Emily busy 14:00-15:30 and David busy 15:30-16:30 leave only 30 minutes, 60 are needed.
   - Oct 23: **selected 10:00-11:00 CT** (11:00-12:00 EDT). Traps: David's "Lunch" 11:30-12:30 is `showAs: free` and does not block; Raj is out of office that day but is not on this meeting and does not block (FR-SCH-10).
5. `find_events` for Emily and David with the addresses on W06 (From James Carter, To Emily, Cc David and Lisa Park) returns **exactly one** upcoming event, the Oct 22 walkthrough (the same event key on both calendars counts once); it is the target. Outcome **`update_existing_meeting`**; the request names the target event key, the new time and the attendee to add, `lisa.park@wingtiptoys.com`. `pending`; the event is unchanged; nothing is sent.

**Stage 2: approval handler**

1. Record intent (decision `approve`, `decided_by`, `decided_at`; progress `in_progress`).
2. Re-check availability for 10:00-11:00 CT on Oct 23; on a conflict, nothing changes and the request becomes `needs_review` (TR-11).
3. `CalendarProvider.find_event(key)` re-reads the target event found at proposal time; `update_event(key, changes)` moves it to Oct 23 10:00-11:00 CT and adds Lisa Park. No second event is created (FR-SCH-9). Locally the update goes to the SQLite overlay and never modifies the dataset files (OQ-22).
4. `MailProvider.create_reply_draft` then `send_draft`: the confirmation reply.
5. CRM Writer: the updated `Meeting` (FR-CRM-2). The stage stays **Presentation/Follow-up**.

### 7.6 Other replay paths

- **Duplicate**: the second email with an existing Message-ID (F08b vs F08) creates no record (FR-ING-5, TR-1).
- **Noise**: the internal HR all-staff email creates no CRM record (FR-ING-6).
- **Unanswered nudge** (Northwind): no stage change (FR-CLS-3); loss reason captured; next action re-engage in April 2027 (FR-SUM-2).
- **New subject, same customer** (for example F05, N04, W03): linked by domain and contacts (FR-ING-3).
- **Sent items**: outbound emails also update engagement history (FR-ING-7).

## 8. Idempotency matrix (R6, TR-6)

R6 requires every write to be safe to repeat and names Message-ID and iCalUId or a stable internal key. The other keys below are proposals.

| Operation | Key | Behavior on repeat |
|---|---|---|
| Ingest email | Message-ID | No second record |
| Add contact | (customer, email) | No duplicate |
| Record stage change | (customer, new stage, source) | No duplicate history row |
| Store scheduling request | Trigger email and outcome | Same request returned |
| **Approve (whole)** | Request id (plus the API's `Idempotency-Key`, see api.md) | Same recorded result returned; no new side effects (TR-6) |
| **Approval step** | Request id and step name | A completed step is not run again; a failed step is retried |
| Create event | Event key (OQ-9: derived from the request id locally) | Same event returned |
| Update event | Event key plus requested change | No second event; same final state |
| Send reply | Draft reference plus request id | Not sent twice; a retry after a failed send reuses the draft reference |

## 9. Error handling, retries and audit

- Model calls: bounded schema-validation retries (the contract in section 2.3) and a request timeout; failure raises a typed error that the Orchestrator records. Provider calls: retries with limits.
- A failed message never stops a run (section 14); the failure appears in the audit log and the run result. A failed approval step leaves the approval progress `partially_completed` with the failed step visible and is retryable (FR-APP-5, TR-12); no automatic rollback in Phase 1.
- Each agent run is an `AgentRun` with agent, input reference, output, provider, model, timestamp, duration, approval decision (FR-AUD-1), tied together by a run ID in structured logs; the approval handler is recorded the same way. All audit entries go through `CrmRepository`. Mail bodies and secrets stay out of logs (R7).
- Local mode records the active provider labels; live providers carry `implemented, unverified` (R3).

## 10. Live adapters (UNVERIFIED)

Written from documentation only; none has run. Details and reference excerpts: the `crm-graph-integration` and `crm-agent-framework-azure-openai` skills and `.claude/skills/*/snippets/`.

| Interface | Live adapter | Documented calls |
|---|---|---|
| MailProvider | Graph mail | Inbox subscription plus delta; get message; `createReply` then send. Sent Items ingestion (FR-ING-7) is not yet researched |
| CalendarProvider | Graph calendar | `getSchedule` (its response includes per-user working hours); create event as Teams meeting; update event |
| ChatModelProvider | Foundry or Azure OpenAI via Agent Framework | `Agent` with `response_format` |
| CrmRepository | Azure SQL or Dataverse | Undecided (D3) |

Permissions and the approver are to be confirmed with IT (D7); no permission set is scoped in code. Contract tests (TR-7) use sample responses shaped like real output and are labeled contract tests. Real authentication for the CRM API (Entra ID) is designed in [api.md](api.md) section 10 and is UNVERIFIED.

## 11. Where the tests attach

| Test | Targets |
|---|---|
| TR-1 | Ingestion, Stage Classifier, Scheduler clarification path, against `expected_outcomes.json` |
| TR-2 | `scheduling` module and Scheduler outcomes for sections 7.3 to 7.5, including the DST trap and the non-blocking `free` event; **the reschedule lookup (FR-SCH-9, D11)**: the W06 case (exactly one match), several matches narrowed by the original meeting day, several matches not resolved, and no match, the last two giving a clarification request and never a second meeting |
| TR-3 | Summaries and drafted replies, rubric-scored |
| TR-4 | Every endpoint in [api.md](api.md) |
| TR-5 | Dashboard pipeline, timeline, scheduling panel, approve/edit/reject |
| TR-6 | Replay twice, identical CRM state; approve twice, no duplicates |
| TR-7 | Live providers, contract tests |
| TR-8 | Stage accuracy per run |
| TR-9 | Smoke: warm-up; (a) replay with no approval (final stages, a pending request for Adventure Works, Tailspin and Wingtip); (b) approval through the real endpoint; no duplicates |
| TR-10 | Request state transitions (section 5.1): pending, superseded by a newer email, cancelled by a withdrawal, expired when all windows are past (an injected clock, OQ-24); FR-SCH-12 |
| TR-11 | Approval re-check: a calendar conflict introduced after proposal gives `needs_review` with fresh options and books nothing (section 7.2 step 1); FR-APP-4 |
| TR-12 | Approval failure: a forced failure in one step leaves `partially_completed` with the failed step visible; a retry completes without duplicates (section 8); FR-APP-5, R6 |
| TR-13 | API safety: the approve endpoint rejects a foreign Origin, a missing `X-CRM-Token` header and a wrong content type (api.md section 10.1); R5 |

## 12. Design questions

All design questions OQ-1 to OQ-33 are resolved; the decisions are in hld.md section 12.1 (and `inputs/decisions.md`). What is still open, by the slice that needs it, is in hld.md section 12.2; none blocks Slice 1 or Slice 2 (the TR-3 scorer is decided in `decisions.md`).
