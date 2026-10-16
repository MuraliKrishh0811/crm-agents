# CRM API

Status: **proposed contract**, draft for review, updated 2026-10-16 after every design question (OQ-1 to OQ-38) was resolved in `decisions.md` and the requirements were edited to match. Nothing is implemented. `REQUIREMENTS.md` requires one CRM API that serves both UI surfaces and exposes customers, timelines, next actions, scheduling requests, approvals and a trigger for the agent workflow (FR-API-1), but it defines no endpoints, paths or payloads. Everything below is a proposal for the Slice 4 plan; it becomes a decision only when you approve it.

Conventions of this document:

- `REQUIREMENTS.md` is authoritative. `OQ-n` points to the design questions in [hld.md](hld.md) section 12.1 (numbers match `decisions.md`); all are resolved. Endpoint paths, payload shapes and error codes are not in the requirements, so they are still a proposal for the Slice 4 plan.
- Example values are **illustrative**, built from the scenarios in requirements section 10. Identifiers and email addresses are made up, except the event key `wingtip-walkthrough-20261022` and `lisa.park@wingtiptoys.com`, which section 10 gives.
- Live-mode behavior behind any field (Graph, Entra ID, Azure OpenAI, Foundry) is **UNVERIFIED**. The API shapes are mode-agnostic.
- Every endpoint here needs a curl command and a scripted equivalent (TR-4); the scripts will live in `tests/backend/`.

## 1. Conventions

| Topic | Proposal |
|---|---|
| Base URL | **Phase 1: the server binds 127.0.0.1 only** (OQ-13; API safety in `decisions.md`). The port comes from `API_PORT` (OQ-30); there is no version prefix. Examples use `export BASE_URL="http://127.0.0.1:$API_PORT"` |
| Format | JSON request and response bodies, UTF-8. `Content-Type: application/json` is required on every `POST` and `PATCH` (`415` otherwise, section 10.1) |
| Authentication and identity | **Phase 1:** no login. The approver is a **configured local user name** (`APPROVER_USER`) recorded as `decided_by` on every approval; request bodies carry no identity. Every write (`POST`, `PATCH`) must also pass the safety checks of section 10.1: allowed `Host` and `Origin`, `Content-Type: application/json` and the per-run token in `X-CRM-Token`. **Live:** Entra ID, designed in section 10.2, UNVERIFIED |
| Time | Every timestamp is a `TimeInZone` object: UTC plus the relevant IANA zone (R9), for example `{"utc": "2026-10-27T15:00:00Z", "zone": "America/Chicago"}`. No bare offsets |
| Simulation | Anything local mode cannot truly produce carries `"simulated": true` (R10), for example a Teams join link |
| Identifiers | Opaque strings. Emails are keyed by Message-ID (R6); meetings by event key (iCalUId or a stable internal key, OQ-9) |
| Idempotency | Repeating a write is safe (R6). Approval takes a required `Idempotency-Key` header (section 7.5) |
| Errors | `{"error": {"code": "...", "message": "...", "details": {}}}`, sometimes with the current `scheduling_request` beside it |
| Pagination | Not needed for the Phase 1 dataset; list endpoints return `{"items": [...], "count": n}` |

Proposed status codes: `200` OK, `202` accepted (workflow started), `400` malformed request or missing required header, `401` token missing, `403` foreign `Host` or `Origin` or a wrong token (section 10.1), `404` not found, `409` the request is in a state that does not allow this (including `availability_changed` at approval, and a second workflow run while one is active, OQ-14), `415` wrong content type, `422` valid JSON but invalid content, `502` a provider call failed during approval (details name the failed step), `503` a required provider is unavailable (for example the model server is down).

### 1.1 Enumerations

| Name | Values | Source |
|---|---|---|
| Stage | `Initial Lead`, `Engagement`, `Presentation/Follow-up`, `Converted`, `Not Converted` | Section 5 |
| Outcome | `recommend_slots`, `counter_propose`, `request_clarification`, `update_existing_meeting` | FR-SCH-7 |
| Request `state` | `pending`, `approved`, `rejected`, `superseded`, `cancelled`, `expired`, `needs_review` | FR-SCH-12 |
| `decision` | `approve`, `reject` (or `null` until decided). **There is no `edit` decision**: an edit is an audit entry and changes no state (OQ-4) | Section 9 |
| `approval_progress` | `not_started`, `in_progress`, `completed`, `partially_completed` | Section 9, FR-APP-5 |
| Approval step `name` | `recheck_availability`, `create_or_update_event`, `send_confirmation`, `write_crm_updates` (this order) | `decisions.md` OQ-20 |
| Approval step `status` | `pending`, `succeeded`, `failed`, `not_applicable`, `conflict` (**proposed**; each is derived from the step's `AgentRun` audit entry, section 9) | OQ-27, OQ-29 |
| `showAs` | `free`, `tentative`, `busy`, `oof`, `workingElsewhere` | Section 11 |

| Meeting `status` | `scheduled`, `rescheduled`, `cancelled` | OQ-17 |
| Next action `status` | `open`, `done`, `dismissed` | OQ-17 |

## 2. Endpoint overview

| # | Method and path | Purpose | Requirement |
|---|---|---|---|
| 0 | `GET /session` | Hands the dashboard or a script the per-run token needed for writes | R5, TR-13, OQ-33 |
| 1 | `GET /health` | Liveness, mode, configured approver, model warm-up state, simulated clock | R3, D5 (warm-up), OQ-13 |
| 2 | `GET /providers` | Active providers per interface with their status labels | FR-CFG-1, R3, R10, FR-UI-4 |
| 3 | `POST /workflow/runs` | Trigger the agent workflow (stage 1) | FR-API-1 |
| 4 | `GET /workflow/runs/{run_id}` | Progress, counts and failures of a run | FR-API-1, section 14 |
| 5 | `GET /pipeline` | Customers grouped by stage | FR-UI-1 |
| 6 | `GET /customers` | Customers, filterable | FR-API-1, FR-UI-5 |
| 7 | `GET /customers/{customer_id}` | Customer detail | FR-UI-2 |
| 8 | `GET /customers/{customer_id}/timeline` | Engagement timeline (emails and meetings) | FR-UI-2 |
| 9 | `GET /next-actions` | Next actions, filterable by due range and owner | FR-API-1, FR-UI-5 |
| 10 | `GET /scheduling-requests` | Scheduling requests, filterable by `state` | FR-API-1, FR-UI-3, FR-SCH-12 |
| 11 | `GET /scheduling-requests/{id}` | One request with reasons, draft, decision and approval progress | FR-UI-3 |
| 12 | `PATCH /scheduling-requests/{id}/draft` | Edit the prepared draft reply text only (an audit entry; the state does not change) | FR-APP-1, OQ-4 |
| 13 | `POST /scheduling-requests/{id}/approve` | Approve: run the approval steps | FR-APP-2 to FR-APP-5, R5 |
| 14 | `POST /scheduling-requests/{id}/reject` | Reject: record and do nothing else | FR-APP-1, FR-APP-3 |
| 15 | `GET /audit/runs` | Agent runs, filterable | FR-AUD-1, FR-UI-4 |
| 16 | `GET /audit/runs/{id}` | One agent run | FR-AUD-1, FR-UI-4 |

Endpoints 0, 1, 2, 15 and 16 are not named in FR-API-1; they follow from R3, R5, R10, FR-AUD-1 and FR-UI-4.

## 3. System

### 3.0 `GET /session` (OQ-33)

Every write needs the per-run token in the `X-CRM-Token` header (section 10.1). The token is generated when the API starts, kept in memory only and never written to `.env`, a file or a log. A client gets it here; examples below assume:

```bash
export BASE_URL="http://127.0.0.1:$API_PORT"
export TOKEN="$(curl -s "$BASE_URL/session" | python3 -I -c 'import sys, json; print(json.load(sys.stdin)["token"])')"
```

```json
{"token": "<random value, new on every start of the API>", "header": "X-CRM-Token", "approver": "Emily Chen"}
```

The request must come from an allowed `Host`, and if it carries an `Origin` header that must be the dashboard origin; the response carries CORS headers only for the dashboard origin, so a page from any other origin cannot read the token. A restart invalidates the old token (a write with it returns `403` `token_invalid`; fetch a new one).

### 3.1 `GET /health`

```bash
curl -s "$BASE_URL/health"
```

```json
{
  "status": "ok",
  "mode": "local",
  "simulated_now": {"utc": "2026-10-16T15:00:00Z", "zone": "America/Chicago"},
  "model": {"provider": "ollama", "name": "llama3.1:8b", "warm": true},
  "api": {"listen": "127.0.0.1 only", "approver": "Emily Chen"}
}
```

`model.warm` reports whether the warm-up call has completed, because Ollama unloads idle models (D5); the smoke test calls this first (TR-9). `api.approver` is the configured local approver (`APPROVER_USER`) that every approval is recorded under as `decided_by` (OQ-13). If the model server is down, `status` is `degraded` and `model.warm` is `false`.

### 3.2 `GET /providers`

```bash
curl -s "$BASE_URL/providers"
```

```json
{
  "mode": "local",
  "active": {
    "mail": {"implementation": "local-eml", "status": "working"},
    "calendar": {"implementation": "local-mock-calendar", "status": "working"},
    "model": {"implementation": "ollama", "model": "llama3.1:8b", "status": "working"},
    "repository": {"implementation": "sqlite", "status": "working"}
  },
  "live": [
    {"implementation": "graph-mail", "status": "implemented, unverified", "enabled": false},
    {"implementation": "graph-calendar", "status": "implemented, unverified", "enabled": false},
    {"implementation": "foundry-or-azure-openai", "status": "implemented, unverified", "enabled": false}
  ]
}
```

The UI uses this to label simulated and unverified parts (R10, R3).

## 4. Workflow

### 4.1 `POST /workflow/runs`

Triggers stage 1 (ingestion and analysis). It never books, updates or sends anything (R5). Semantics (OQ-14): it returns `202` immediately and progress is read with `GET`; only one run is active at a time (a second request gets `409` `run_in_progress`); the scope is all messages or one; messages are processed sequentially in date order.

```bash
curl -s -X POST "$BASE_URL/workflow/runs" \
  -H "Content-Type: application/json" -H "X-CRM-Token: $TOKEN" \
  -d '{"scope": "all"}'
```

Request: `scope` is `"all"` (replay everything not yet processed) or `{"message_id": "<id>"}` for one message. The simulated clock, fixed at `SIMULATED_NOW` for the run (OQ-24), decides which emails have arrived (OQ-5). Replaying the same set twice yields identical CRM state (R6, TR-6).

Response `202`:

```json
{
  "run_id": "run-example-1",
  "status": "running",
  "scope": "all",
  "started_at": {"utc": "2026-10-16T15:00:02Z", "zone": "America/Chicago"}
}
```

### 4.2 `GET /workflow/runs/{run_id}`

```bash
curl -s "$BASE_URL/workflow/runs/run-example-1"
```

```json
{
  "run_id": "run-example-1",
  "status": "completed_with_failures",
  "counts": {
    "processed": 29,
    "duplicates_ignored": 1,
    "noise_ignored": 1,
    "failed": 1
  },
  "scheduling_requests": {"pending": 3, "superseded": 1, "cancelled": 0, "expired": 0},
  "failures": [
    {"message_id": "<illustrative-id>", "agent": "stage_classifier", "error": "model output failed schema validation after the retry budget"}
  ],
  "started_at": {"utc": "2026-10-16T15:00:02Z", "zone": "America/Chicago"},
  "finished_at": {"utc": "2026-10-16T15:12:40Z", "zone": "America/Chicago"}
}
```

`status` is `running`, `completed` or `completed_with_failures`. A failed message does not stop the run; the failure is also in the audit log (section 14). The counts are illustrative (the message counts add up to the dataset's 32 emails) and are not expected results; `superseded` shows that old requests are kept (FR-SCH-12).

## 5. Customers

### 5.1 `GET /pipeline`

```bash
curl -s "$BASE_URL/pipeline"
```

```json
{
  "stages": [
    {"stage": "Initial Lead", "customers": []},
    {"stage": "Engagement", "customers": [
      {"id": "cust-example-adv", "company_name": "Adventure Works Cycles", "email_domain": "adventure-works.com",
       "account_owner": "emily.chen@contoso.com",
       "next_action": {"description": "Confirm the proposed meeting", "due_date": null},
       "pending_scheduling_requests": 1}
    ]},
    {"stage": "Presentation/Follow-up", "customers": []},
    {"stage": "Converted", "customers": []},
    {"stage": "Not Converted", "customers": []}
  ]
}
```

Backed by `customers_by_stage` (FR-UI-1). `pending_scheduling_requests` counts requests in state `pending`.

### 5.2 `GET /customers`

Query parameters: `stage`, `q` (case-insensitive match on company name), `owner` (account owner email).

```bash
curl -s "$BASE_URL/customers?q=Fabrikam"
curl -s "$BASE_URL/customers?stage=Engagement&owner=emily.chen@contoso.com"
```

```json
{"items": [{"id": "cust-example-fab", "company_name": "Fabrikam", "email_domain": "fabrikam.com", "stage": "Converted", "account_owner": "sarah.mitchell@contoso.com"}], "count": 1}
```

The Teams agent answers "where does Fabrikam stand?" with `GET /customers?q=Fabrikam` followed by `GET /customers/{id}` (FR-UI-5).

### 5.3 `GET /customers/{customer_id}`

```bash
curl -s "$BASE_URL/customers/cust-example-adv"
```

```json
{
  "id": "cust-example-adv",
  "company_name": "Adventure Works Cycles",
  "email_domain": "adventure-works.com",
  "stage": "Engagement",
  "account_owner": "emily.chen@contoso.com",
  "created_date": {"utc": "2026-08-12T14:00:00Z", "zone": "America/Chicago"},
  "loss_reason": null,
  "contacts": [
    {"id": "contact-example-1", "name": "Oliver Bennett", "email": "oliver.bennett@adventure-works.com", "role_title": null, "time_zone": "Europe/London"},
    {"id": "contact-example-2", "name": "Sophie Turner", "email": "sophie.turner@adventure-works.com", "role_title": null, "time_zone": null}
  ],
  "stage_history": [
    {"previous_stage": "Initial Lead", "new_stage": "Engagement", "timestamp": {"utc": "2026-08-20T15:00:00Z", "zone": "America/Chicago"}, "reason": "Two-way discovery conversation", "source": {"type": "email", "ref": "<illustrative-id>"}}
  ],
  "engagement_summary": "Customer needs ... (the latest running-summary note, OQ-23)",
  "next_action": {"description": "Confirm the proposed meeting", "due_date": null},
  "pending_scheduling_request_ids": ["sr-example-adv"]
}
```

Stage, contacts, timeline and next action are what FR-UI-2 asks for. A stage-history `source` is an email or an approval (section 9; OQ-3, resolved): `{"type": "email", "ref": "<message id>"}` or `{"type": "approval", "ref": "<scheduling request id>"}`.

### 5.4 `GET /customers/{customer_id}/timeline`

```bash
curl -s "$BASE_URL/customers/cust-example-adv/timeline"
```

```json
{
  "items": [
    {"id": "eng-example-1", "type": "email", "timestamp": {"utc": "2026-10-14T16:30:00Z", "zone": "Europe/London"},
     "summary": "Customer offers three windows for a 60 minute meeting",
     "source_ref": "<illustrative-id>",
     "detail": {"direction": "received", "subject": "...", "attachments": []}},
    {"id": "eng-example-2", "type": "meeting", "timestamp": {"utc": "2026-10-27T15:00:00Z", "zone": "America/Chicago"},
     "summary": "Meeting created after approval",
     "source_ref": "<event key>",
     "detail": {"join_link": {"url": "<simulated-link>", "simulated": true}, "status": "scheduled"}}
  ],
  "count": 2
}
```

Backed by `customer_timeline(customer_id)`: engagement entries of type email, meeting or note in time order (FR-UI-2). The second item exists only after approval.

## 6. Next actions

`GET /next-actions` query parameters: `due_from`, `due_to` (dates, inclusive), `owner` (account owner email), `customer_id`, `status`.

```bash
curl -s "$BASE_URL/next-actions?due_from=2026-10-19&due_to=2026-10-23&owner=emily.chen@contoso.com"
```

```json
{
  "items": [
    {"id": "na-example-1", "customer_id": "cust-example-adv", "company_name": "Adventure Works Cycles",
     "description": "Confirm the proposed meeting", "due_date": "2026-10-20", "status": "open"}
  ],
  "count": 1
}
```

Backed by `next_actions_due(range)`: inclusive on both ends, open actions only (OQ-12; the `status` parameter lets a client ask for others). Status values are `open`, `done`, `dismissed` (OQ-17). The `stale_leads` threshold is `STALE_LEAD_DAYS` (starting value 14). The Teams question "what are my next actions this week?" maps to this endpoint with the week's dates; how a Teams user maps to `owner` is not specified.

## 7. Scheduling requests and approval

### 7.1 Shape of a scheduling request

Fields follow the `SchedulingRequest` entity (requirements section 9): customer, trigger email, parsed customer slots, attendees considered, evaluated results with reasons, proposed slots, outcome, draft reply, `state`, `decision` (`approve` or `reject`), `decided_by`, `decided_at` and `approval_progress`. Each approval step's result is an `AgentRun` audit entry linked to the request, and `approval_steps` below is derived from those entries. Example for the SCH-ADV scenario, **after replay and before approval**:

```json
{
  "id": "sr-example-adv",
  "customer_id": "cust-example-adv",
  "trigger_email": "<illustrative-id>",
  "outcome": "recommend_slots",
  "state": "pending",
  "state_reason": null,
  "superseded_by": null,
  "parsed_customer_slots": [
    {"start": {"utc": "2026-10-20T14:00:00Z", "zone": "Europe/London"}, "end": {"utc": "2026-10-20T16:00:00Z", "zone": "Europe/London"}, "stated_zone_text": "BST"},
    {"start": {"utc": "2026-10-21T13:00:00Z", "zone": "Europe/London"}, "end": {"utc": "2026-10-21T14:30:00Z", "zone": "Europe/London"}, "stated_zone_text": "BST"},
    {"start": {"utc": "2026-10-27T14:00:00Z", "zone": "Europe/London"}, "end": {"utc": "2026-10-27T16:00:00Z", "zone": "Europe/London"}, "stated_zone_text": "GMT"}
  ],
  "attendees_considered": [
    {"email": "emily.chen@contoso.com", "kind": "internal", "blocks_meeting": true},
    {"email": "raj.patel@contoso.com", "kind": "internal", "blocks_meeting": true},
    {"email": "oliver.bennett@adventure-works.com", "kind": "external", "blocks_meeting": false},
    {"email": "sophie.turner@adventure-works.com", "kind": "external", "blocks_meeting": false}
  ],
  "evaluated_results": [
    {"candidate": {"start": {"utc": "2026-10-20T14:00:00Z", "zone": "America/Chicago"}, "end": {"utc": "2026-10-20T16:00:00Z", "zone": "America/Chicago"}},
     "verdict": "rejected", "reason": "Emily busy until 10:30", "warnings": []},
    {"candidate": {"start": {"utc": "2026-10-21T13:00:00Z", "zone": "America/Chicago"}, "end": {"utc": "2026-10-21T14:30:00Z", "zone": "America/Chicago"}},
     "verdict": "fallback", "reason": "Only a fallback: Raj tentative 08:30-09:00", "warnings": ["Raj is tentative 08:30-09:00"]},
    {"candidate": {"start": {"utc": "2026-10-27T15:00:00Z", "zone": "America/Chicago"}, "end": {"utc": "2026-10-27T16:00:00Z", "zone": "America/Chicago"}},
     "verdict": "accepted", "reason": "Both attendees free; Raj busy 09:00-10:00 (kickoff) so the slot starts at 10:00", "warnings": []}
  ],
  "proposed_slots": [
    {"id": "slot-1", "rank": 1, "fallback": false,
     "start": {"utc": "2026-10-27T15:00:00Z", "zone": "America/Chicago"},
     "end": {"utc": "2026-10-27T16:00:00Z", "zone": "America/Chicago"},
     "customer_local": {"zone": "Europe/London", "start": "2026-10-27T15:00:00", "end": "2026-10-27T16:00:00"},
     "warnings": []},
    {"id": "slot-2", "rank": 2, "fallback": true,
     "start": {"utc": "2026-10-21T13:00:00Z", "zone": "America/Chicago"},
     "end": {"utc": "2026-10-21T14:00:00Z", "zone": "America/Chicago"},
     "customer_local": {"zone": "Europe/London", "start": "2026-10-21T14:00:00", "end": "2026-10-21T15:00:00"},
     "warnings": ["Raj is tentative 08:30-09:00"]}
  ],
  "fresh_options": [],
  "target_event_key": null,
  "draft_reply": {"to": ["oliver.bennett@adventure-works.com"], "subject": "...", "body": "...proposed time shown in the customer's zone..."},
  "decision": null,
  "decided_by": null,
  "decided_at": null,
  "approval_progress": "not_started",
  "approval_steps": []
}
```

Notes:

- Reasons are generated by code and are human-readable (FR-SCH-11); the wording is illustrative. Whether `evaluated_results` entries are per window or per slot is for the Slice 3 plan.
- `proposed_slots` holds at most 3 entries (FR-SCH-6). A tentative fallback is **listed last with its warning** (OQ-4; the answer key records the Oct 21 window as `fallback_with_warning`). The two slots in the example are illustrative: slot 2 is 14:00-15:00 BST on Oct 21 (08:00-09:00 CT).
- `state` is one of the seven values in section 1.1; `approval_progress` is one of four. `state_reason`, `superseded_by` (the id of the newer request) and `fresh_options` are fields of the request (requirements section 9; OQ-3, OQ-32) for requests that are superseded, cancelled, expired or in `needs_review`, kept for audit (OQ-16). Fresh options replace `proposed_slots`, the earlier slots are kept in an audit entry, and state reasons are read from audit entries (OQ-32).
- `draft_reply` is **prepared by the Scheduler and never sent by an agent** (OQ-2). The draft, `decision`, `decided_by` and `decided_at` are fields of the request (OQ-3, resolved). The mailbox draft is created by the approval handler at the send step (OQ-25).
- For `counter_propose` the slots are shown in the customer's zone; for `update_existing_meeting` `target_event_key` names the event located with `find_events` (FR-SCH-9, D11; for SCH-WING `wingtip-walkthrough-20261022`); when no event or several unresolved events match, the outcome is `request_clarification`, not a new meeting. Offsets follow requirements section 10 (London is 6 hours ahead of Chicago before Oct 25 and 5 hours after).

### 7.2 `GET /scheduling-requests`

Query parameters: `state` (one of the seven), `customer_id`, `outcome`.

```bash
curl -s "$BASE_URL/scheduling-requests?state=pending"
curl -s "$BASE_URL/scheduling-requests?state=superseded&customer_id=cust-example-tail"
```

```json
{"items": [{"id": "sr-example-adv", "customer_id": "cust-example-adv", "outcome": "recommend_slots", "state": "pending"}], "count": 1}
```

### 7.3 `GET /scheduling-requests/{id}`

```bash
curl -s "$BASE_URL/scheduling-requests/sr-example-adv"
```

Returns the full object from section 7.1. This is the data behind the scheduling panel (FR-UI-3): parsed windows, availability results with reasons, proposed slots, draft reply, request state, approval progress with the failed step if any, and the controls to approve, edit or reject.

### 7.4 `PATCH /scheduling-requests/{id}/draft` (edit)

Changes **only the draft reply text** and approves nothing (OQ-4; FR-APP-1; requirements section 9). The change is recorded as an **audit entry** (an `AgentRun` with the configured approver and the time); `decision`, `state` and `approval_progress` do not change. Requires the headers of section 10.1.

```bash
curl -s -X PATCH "$BASE_URL/scheduling-requests/sr-example-adv/draft" \
  -H "Content-Type: application/json" -H "X-CRM-Token: $TOKEN" \
  -d '{"body": "Hi Oliver, ... (edited text)"}'
```

Response `200`: the updated request plus `edit_audit_run_id`. `409` (`invalid_state`) if the request is not `pending`. Slots and attendees cannot be edited, because the evaluation is done in code (R4).

### 7.5 `POST /scheduling-requests/{id}/approve`

The only way a calendar event is created or updated, or a reply sent (R5, FR-APP-2). The approver is **not** in the body: it is the configured local user (OQ-13), recorded as `decided_by` with `decided_at`.

**Request**

| Part | Required | Meaning |
|---|---|---|
| Header `Content-Type: application/json` | **yes** | Anything else is rejected with `415` (section 10.1) |
| Header `X-CRM-Token` | **yes** | The per-run token from `GET /session`; missing: `401`, wrong: `403` (section 10.1) |
| Header `Idempotency-Key` | **yes** | Opaque string chosen by the caller (1 to 128 characters; a fresh UUID per user action is typical). See "Idempotency key" below |
| `selected_slot_id` | for `recommend_slots` and `update_existing_meeting` | **Exactly one** proposed (or fresh) slot id (OQ-4). A fallback slot may be chosen; its warning is shown to the approver. Not used for `counter_propose` and `request_clarification`, where there is no chosen slot (OQ-29) |
| `draft_reply_body` | no | Final reply text, if edited in the same call (OQ-36): `Orchestrator.approve` records it as an edit audit entry like section 7.4 (the edit changes only the draft text) and the approved text is what is sent. Without it the stored draft is sent. A repeat of the same call sends once (R6) |

```bash
curl -s -X POST "$BASE_URL/scheduling-requests/sr-example-adv/approve" \
  -H "Content-Type: application/json" \
  -H "X-CRM-Token: $TOKEN" \
  -H "Idempotency-Key: 6f1c9a52-example-0001" \
  -d '{"selected_slot_id": "slot-1"}'
```

**What approval does** (requirements section 10, FR-APP-2 to FR-APP-5): the handler records the intent first (decision `approve`, `decided_by`, `decided_at`, `approval_progress: in_progress`), then runs these steps in order. **Each step's result is recorded as an `AgentRun` audit entry linked to the request** (section 9). The request `state` becomes `approved` once the re-check passes (OQ-27).

| Step | `recommend_slots` (SCH-ADV) | `counter_propose` (SCH-TAIL) | `update_existing_meeting` (SCH-WING) | `request_clarification` |
|---|---|---|---|---|
| `recheck_availability` | Re-check the chosen slot | `not_applicable` (OQ-29) | Re-check the chosen slot | `not_applicable` (OQ-29) |
| `create_or_update_event` | Create the event once; online meeting; join link simulated locally | `not_applicable` (no meeting is created) | Re-read the target event found at proposal time with `find_events` (`find_event` by its key), update it, add the new attendee; no second event | `not_applicable` |
| `send_confirmation` | Create the reply draft, then send confirmation (OQ-25) | Send the counter-proposal | Send confirmation | Send the clarification |
| `write_crm_updates` | Meeting record, stage to Presentation/Follow-up (source: this approval), engagement entries | Stage stays Engagement | Meeting record updated; stage stays Presentation/Follow-up | Engagement entry for the sent email |

When every step is done, `approval_progress` is `completed`. No automatic rollback in Phase 1. Each step is idempotent: a completed step is not run again, a failed step is retried.

**Idempotency key (proposal).** The key makes a repeated HTTP call safe, in addition to the step-level idempotency inside the handler (R6, TR-6):

| Situation | Result |
|---|---|
| Header missing | `400` `idempotency_key_required` |
| Same key, same request id, same body | The stored response is returned (`200` or the original status), with `"idempotent_replay": true`; no new side effects |
| Same key, a different request id or body | `422` `idempotency_key_reused` |
| New key, request already `approved` with `approval_progress: completed` | `200` with the recorded result and `"idempotent_replay": true`; approving the same request twice creates no duplicates regardless of the key |
| New key, `approval_progress: partially_completed` | **Retry**: resumes from the failed step (FR-APP-5, TR-12) |
| New key, `approval_progress: in_progress` (another call is running) | `409` `approval_in_progress` |
| New key, request `needs_review` | Allowed when it names one of the `fresh_options`, then the same flow as a first approval; a new conflict returns the request to `needs_review` (FR-APP-4, OQ-31) |
| Request in `rejected`, `superseded`, `cancelled` or `expired` | `409` `invalid_state` |

Keys are kept for the life of the request, which is kept for audit.

**Response `200`, completed** (SCH-ADV, illustrative):

```json
{
  "scheduling_request": {
    "id": "sr-example-adv",
    "state": "approved",
    "decision": "approve",
    "decided_by": "Emily Chen",
    "decided_at": {"utc": "2026-10-16T16:00:00Z", "zone": "America/Chicago"},
    "approval_progress": "completed",
    "approval_steps": [
      {"name": "recheck_availability", "status": "succeeded", "result": "slot-1 still free for Emily and Raj", "audit_run_id": "agentrun-example-11"},
      {"name": "create_or_update_event", "status": "succeeded", "result": "created", "audit_run_id": "agentrun-example-12"},
      {"name": "send_confirmation", "status": "succeeded", "result": "sent", "audit_run_id": "agentrun-example-13"},
      {"name": "write_crm_updates", "status": "succeeded", "result": "meeting recorded; stage changed", "audit_run_id": "agentrun-example-14"}
    ]
  },
  "effects": {
    "calendar_action": "created",
    "meeting": {
      "id": "meeting-example-1",
      "event_key": "<key derived from the request id>",
      "subject": "...",
      "start": {"utc": "2026-10-27T15:00:00Z", "zone": "America/Chicago"},
      "end": {"utc": "2026-10-27T16:00:00Z", "zone": "America/Chicago"},
      "attendees": [
        {"email": "emily.chen@contoso.com", "kind": "internal"},
        {"email": "raj.patel@contoso.com", "kind": "internal"},
        {"email": "oliver.bennett@adventure-works.com", "kind": "external"},
        {"email": "sophie.turner@adventure-works.com", "kind": "external"}
      ],
      "join_link": {"url": "<simulated-link>", "simulated": true},
      "status": "scheduled",
      "customer_response_status": null,
      "customer_response_label": "not available (simulated)"
    },
    "message_sent": {"draft_ref": "<draft-ref>", "sent": true},
    "stage_change": {"previous_stage": "Engagement", "new_stage": "Presentation/Follow-up", "reason": "Presentation meeting confirmed", "source": {"type": "approval", "ref": "sr-example-adv"}}
  },
  "idempotent_replay": false,
  "providers": {"calendar": "local-mock-calendar", "mail": "local-eml"}
}
```

For SCH-WING: `calendar_action` is `"updated"`, `meeting.event_key` is `wingtip-walkthrough-20261022`, `meeting.status` is `rescheduled` (OQ-17), the times are `2026-10-23T15:00:00Z` to `2026-10-23T16:00:00Z` (10:00-11:00 CT), the attendee list includes `lisa.park@wingtiptoys.com`, and `stage_change` is `null`. For SCH-TAIL: `calendar_action` is `"none"`, `meeting` is `null`, `message_sent.sent` is `true`, `stage_change` is `null`, and the first two steps are `not_applicable`. `customer_response_status` is `null` in local mode and shown as "not available (simulated)" (OQ-8).

**Response when availability changed (FR-APP-4, TR-11)**: at step 1 a conflict has appeared since replay. **Nothing is booked and nothing is sent.** The request becomes `needs_review` with fresh options. Proposed as `409` with code `availability_changed`, and the current request beside the error so the UI can show the new options:

```json
{
  "error": {
    "code": "availability_changed",
    "message": "Raj Patel is now busy 10:00-10:30 on 2026-10-27 (America/Chicago). Nothing was booked.",
    "details": {"step": "recheck_availability", "conflicts": [{"attendee": "raj.patel@contoso.com", "showAs": "busy", "start": {"utc": "2026-10-27T15:00:00Z", "zone": "America/Chicago"}, "end": {"utc": "2026-10-27T15:30:00Z", "zone": "America/Chicago"}}]}
  },
  "scheduling_request": {
    "id": "sr-example-adv",
    "state": "needs_review",
    "state_reason": "Availability changed at approval",
    "decision": "approve",
    "decided_by": "Emily Chen",
    "decided_at": {"utc": "2026-10-16T16:00:00Z", "zone": "America/Chicago"},
    "approval_progress": "not_started",
    "approval_steps": [
      {"name": "recheck_availability", "status": "conflict", "result": "Raj Patel busy 10:00-10:30", "audit_run_id": "agentrun-example-21"},
      {"name": "create_or_update_event", "status": "pending"},
      {"name": "send_confirmation", "status": "pending"},
      {"name": "write_crm_updates", "status": "pending"}
    ],
    "fresh_options": [
      {"id": "fresh-1", "rank": 1, "fallback": true,
       "start": {"utc": "2026-10-21T13:00:00Z", "zone": "America/Chicago"},
       "end": {"utc": "2026-10-21T14:00:00Z", "zone": "America/Chicago"},
       "customer_local": {"zone": "Europe/London", "start": "2026-10-21T14:00:00", "end": "2026-10-21T15:00:00"},
       "warnings": ["Raj is tentative 08:30-09:00"]}
    ]
  }
}
```

The fresh option is illustrative: with the Oct 27 slot gone, the only slot left inside the customer's offered windows is the earlier tentative fallback (Oct 21, 14:00-15:00 BST), shown with its warning. If no slot remains, `fresh_options` is empty and the person is told that nothing could be offered. After a conflict the approval progress returns to `not_started`; the approver approves one of the fresh options with a new `Idempotency-Key`, or rejects (FR-APP-4, OQ-31). The fresh options replace the proposed slots and the earlier ones are kept in an audit entry (OQ-32).

**Response when a step fails (FR-APP-5, TR-12)**: proposed as `502` with code `approval_step_failed`. The earlier steps stay done (no rollback in Phase 1), the failed step is visible, and the approval progress is `partially_completed`:

```json
{
  "error": {"code": "approval_step_failed", "message": "The confirmation could not be sent. The meeting was already created and will not be created again on retry.",
            "details": {"step": "send_confirmation", "provider": "mail"}},
  "scheduling_request": {
    "id": "sr-example-adv", "state": "approved", "decision": "approve", "decided_by": "Emily Chen",
    "approval_progress": "partially_completed",
    "approval_steps": [
      {"name": "recheck_availability", "status": "succeeded"},
      {"name": "create_or_update_event", "status": "succeeded", "result": "created"},
      {"name": "send_confirmation", "status": "failed", "result": "mail provider error"},
      {"name": "write_crm_updates", "status": "pending"}
    ]
  }
}
```

To retry, call the same endpoint again (same or new key): the handler resumes at `send_confirmation` and completes without a second meeting. The `state` stays `approved` because the re-check had passed (OQ-27).

Other errors: `404` unknown id; `409` `invalid_state`; `422` `slot_required` (a booking outcome with no `selected_slot_id`), `slot_not_found` or `idempotency_key_reused`; `503` a required provider is down; the safety errors of section 10.1.

### 7.6 `POST /scheduling-requests/{id}/reject`

The approver is the configured local user; no identity in the body. Requires the headers of section 10.1; `Idempotency-Key` is optional here because rejecting twice is naturally harmless.

```bash
curl -s -X POST "$BASE_URL/scheduling-requests/sr-example-adv/reject" \
  -H "Content-Type: application/json" -H "X-CRM-Token: $TOKEN" \
  -d '{"reason": "Customer asked to wait until next month"}'
```

Creates, updates and sends nothing. Response `200`: the request with `state: "rejected"`, `decision: "reject"`, `decided_by`, `decided_at`, and the optional reason in `state_reason`. After a rejection nothing happens automatically; a new request is created only when a new email arrives (OQ-26). Rejecting an already rejected request returns the same result with `"idempotent_replay": true`; a request in any other non-`pending` state returns `409` `invalid_state`.

## 8. Audit

### 8.1 `GET /audit/runs`

Query parameters: `agent`, `customer_id`, `run_id`, `since`.

```bash
curl -s "$BASE_URL/audit/runs?run_id=run-example-1&agent=scheduler"
```

```json
{
  "items": [
    {"id": "agentrun-example-1", "run_id": "run-example-1", "agent": "scheduler",
     "input_ref": "<trigger email message id>",
     "output": {"outcome": "recommend_slots", "scheduling_request_id": "sr-example-adv"},
     "providers": [
       {"interface": "chat_model", "implementation": "ollama", "model": "llama3.1:8b"},
       {"interface": "calendar", "implementation": "local-mock-calendar"}
     ],
     "timestamp": {"utc": "2026-10-16T15:03:11Z", "zone": "America/Chicago"},
     "duration_ms": 8420,
     "approval_decision": null}
  ],
  "count": 1
}
```

Fields follow `AgentRun` (FR-AUD-1). The approval handler is recorded the same way, with its `approval_decision`, and **each approval step is its own entry linked to the scheduling request** (the `input_ref` is the request id; requirements section 9); so is each draft edit. Audit entries are written through `CrmRepository` into separate tables of the same database in Phase 1 (OQ-1, resolved). The audit view shows provider and model per run (FR-UI-4).

### 8.2 `GET /audit/runs/{id}`

```bash
curl -s "$BASE_URL/audit/runs/agentrun-example-1"
```

Returns one item in the shape above. Mail bodies and secrets are not written to audit output (R7).

## 9. A complete approval walk-through (curl)

For a pending SCH-ADV request; this is the call sequence of smoke-test part (b) (TR-9):

```bash
# 0. get the per-run token (section 3.0)
export TOKEN="$(curl -s "$BASE_URL/session" | python3 -I -c 'import sys, json; print(json.load(sys.stdin)["token"])')"
# 1. find what is waiting
curl -s "$BASE_URL/scheduling-requests?state=pending"
# 2. inspect one
curl -s "$BASE_URL/scheduling-requests/sr-example-adv"
# 3. approve (explicit human action; R5). The approver is the configured local user.
curl -s -X POST "$BASE_URL/scheduling-requests/sr-example-adv/approve" \
  -H "Content-Type: application/json" -H "X-CRM-Token: $TOKEN" -H "Idempotency-Key: 6f1c9a52-example-0001" \
  -d '{"selected_slot_id": "slot-1"}'
# 4. repeat with the same key: same stored result, no duplicate meeting (R6, TR-6)
curl -s -X POST "$BASE_URL/scheduling-requests/sr-example-adv/approve" \
  -H "Content-Type: application/json" -H "X-CRM-Token: $TOKEN" -H "Idempotency-Key: 6f1c9a52-example-0001" \
  -d '{"selected_slot_id": "slot-1"}'
# 5. repeat with a NEW key: still no duplicate, the recorded result comes back
curl -s -X POST "$BASE_URL/scheduling-requests/sr-example-adv/approve" \
  -H "Content-Type: application/json" -H "X-CRM-Token: $TOKEN" -H "Idempotency-Key: 6f1c9a52-example-0002" \
  -d '{"selected_slot_id": "slot-1"}'
# 6. confirm the effect
curl -s "$BASE_URL/customers/cust-example-adv"
curl -s "$BASE_URL/customers/cust-example-adv/timeline"
curl -s "$BASE_URL/audit/runs?customer_id=cust-example-adv"
```

## 10. Authentication, safety and approver identity

### 10.1 Phase 1: localhost API safety

The Phase 1 API has **no login** and the approver is a configured local user name (OQ-13). That identity is **not authenticated**, so something else must stop a web page open in the same browser from sending an approval to the local API, which would break R5. The measures below are in `decisions.md` ("Additional rules") and are tested by **TR-13**. Which check applies to which request, and the exact error codes, are not in the requirements; they are part of this proposed contract.

| # | Measure | What the API does | Rejection |
|---|---|---|---|
| 1 | **Bind 127.0.0.1 only** | The server listens on the loopback address `127.0.0.1` and on nothing else. The bind address is **not a setting**, so it cannot be misconfigured. The API never listens beyond the local machine in Phase 1 | A connection from another machine cannot be made |
| 2 | **`Host` check** (all requests) | `Host` must be `127.0.0.1:<API_PORT>` or `localhost:<API_PORT>`. This defends against a web page whose domain name has been pointed at 127.0.0.1 | `403` `host_not_allowed` |
| 3 | **`Origin` check** (all requests) | If an `Origin` header is present it must equal `DASHBOARD_ORIGIN` (including for the opaque origin `null`, which is rejected). A request with no `Origin` header (curl, the test scripts) is not rejected on this ground; it still needs the token on writes. With `DASHBOARD_ORIGIN=http://localhost:5173` (the value in `example.env`) the dashboard must be opened at exactly that origin: a page at `http://127.0.0.1:5173` is a different origin and is refused | `403` `origin_not_allowed` |
| 4 | **CORS limited to the dashboard origin** | `Access-Control-Allow-Origin` is the single value `DASHBOARD_ORIGIN`, never `*`, with `Vary: Origin`. Allowed methods `GET, POST, PATCH`; allowed headers `Content-Type, X-CRM-Token, Idempotency-Key`; no credentials (there are no cookies). A preflight (`OPTIONS`) from any other origin gets no allow headers. If `DASHBOARD_ORIGIN` is empty, no cross-origin request is allowed (fail closed) | The browser blocks the page from reading the response or sending the write |
| 5 | **JSON content type** (every `POST` and `PATCH`) | `Content-Type: application/json` is required, even for an empty `{}` body | `415` `unsupported_media_type` |
| 6 | **Custom header on writes: the per-run token** | `X-CRM-Token` must carry the token that `GET /session` handed out. The token is random, generated when the API starts, **held in memory only and never stored in `.env`**, a file, a log, an audit entry or a test fixture (R7), and it is compared in constant time. A restart invalidates it. Approve is the call TR-13 names; the proposal applies the same rule to every `POST` and `PATCH` | missing: `401` `token_required`; wrong: `403` `token_invalid` |

Checks run in the order `Host`, `Origin`, content type, token, `Idempotency-Key` (approve only) and only then reach the handler; a rejected request creates, updates and sends nothing.

**What the browser does for us.** Checked on 2026-10-16 against MDN (`Web/HTTP/Guides/CORS`, `Glossary/CORS-safelisted_request_header`, `Web/HTTP/Reference/Headers/Origin`, `Glossary/Preflight_request`): a cross-origin request needs a preflight unless its headers are only the CORS-safelisted ones (`Accept`, `Accept-Language`, `Content-Language`, `Content-Type`, `Range`), and `Content-Type` is safelisted only for `application/x-www-form-urlencoded`, `multipart/form-data` and `text/plain`. So a browser asks the API's permission before it sends `application/json` or an `X-CRM-Token` header from another origin, and measure 4 refuses it. The `Origin` header is added to cross-origin requests and to same-origin `POST`, `PATCH` and other non-GET requests, and it can be `null` for privacy-sensitive or opaque origins. `Access-Control-Allow-Origin` may name a single origin instead of `*`. **Not verified:** the `Host`-check reasoning (DNS rebinding) is my own and was not checked against browser or framework documentation, and nothing here has run. The token is also a second line of defense: a foreign page cannot read `GET /session` because of measure 4.

**What this does not protect against.** Other programs running on the same machine can call the API directly, fetch the token and approve. That follows from the decision to have no login in Phase 1 (OQ-13) and is why real authentication comes with live access (section 10.2).

**Tests (TR-13).** TR-13 requires that the approve endpoint rejects a foreign Origin, a missing `X-CRM-Token` header and a wrong content type. In each case the test also checks that the request is still `pending` and that nothing was created or sent. The first three below are TR-13; the rest are proposed extras:

```bash
# a. foreign Origin, otherwise valid  -> 403 origin_not_allowed
curl -s -i -X POST "$BASE_URL/scheduling-requests/sr-example-adv/approve" \
  -H "Origin: http://example.invalid" \
  -H "Content-Type: application/json" -H "X-CRM-Token: $TOKEN" -H "Idempotency-Key: tr13-a" \
  -d '{"selected_slot_id": "slot-1"}'
# b. missing X-CRM-Token header  -> 401 token_required
curl -s -i -X POST "$BASE_URL/scheduling-requests/sr-example-adv/approve" \
  -H "Content-Type: application/json" -H "Idempotency-Key: tr13-b" \
  -d '{"selected_slot_id": "slot-1"}'
# c. wrong content type  -> 415 unsupported_media_type
curl -s -i -X POST "$BASE_URL/scheduling-requests/sr-example-adv/approve" \
  -H "Content-Type: text/plain" -H "X-CRM-Token: $TOKEN" -H "Idempotency-Key: tr13-c" \
  -d '{"selected_slot_id": "slot-1"}'
# extras: wrong token -> 403 token_invalid; "Origin: null" -> 403; a wrong Host header -> 403 host_not_allowed;
#         a foreign-origin preflight (OPTIONS) gets no Access-Control-Allow-* headers;
#         a connection to the machine's non-loopback address is refused (measure 1)
```

The custom header in TR-13 is `X-CRM-Token` (OQ-33). `Idempotency-Key` is a second required header on approve and is tested under TR-4 and TR-6.

### 10.2 Live: Entra ID (designed here, **UNVERIFIED**, built after live access exists)

This is a design sketch only. It has not been checked against Microsoft's Entra ID documentation, and nothing is built.

- Callers send an Entra ID access token for the CRM API; the API validates signature, issuer, audience and expiry before any work. The dashboard (and later the Teams agent, D6, which would call the API on behalf of the signed-in user through the Microsoft 365 Agents Toolkit) obtains the token.
- `decided_by` is taken from the validated token's identity and matched to a member in `config/team.json`, replacing the configured local user. Who may approve a given request (the assigned team members, the account owner, or others) is not decided and belongs with the permission and approver decision for IT (D7).
- The localhost measures of section 10.1 stay useful in any deployment that has a browser dashboard; whether the per-run token is still needed once tokens are validated is not decided.
- Live Graph access uses its own app and delegated permissions, to be confirmed with IT (D7); do not confuse them with the API's own token.
- First-day checks are in [first_day_with_access.md](first_day_with_access.md).

## 11. Live-mode notes (UNVERIFIED)

The endpoints and shapes do not change between local and live. Behind them, live providers are written from documentation and have never run (R3): Graph for mail and calendar, Foundry or Azure OpenAI for the model. `GET /providers` shows them as `implemented, unverified` and disabled. Fields that would differ in live mode: `join_link` (a real Teams link instead of a simulated one), `customer_response_status` (from attendee response or meeting-response mail, not yet researched), `event_key` (iCalUId; lookup by iCalUId is not documented, see [first_day_with_access.md](first_day_with_access.md)), per-user working hours (from `getSchedule`, UNVERIFIED), and `decided_by` (from Entra ID, section 10.2).

## 12. Decisions reflected

All design questions OQ-1 to OQ-38 are resolved (hld.md section 12.1; `inputs/decisions.md`) and reflected here: audit through `CrmRepository` (OQ-1); the approval handler sends and books and agents only prepare drafts (OQ-2); request fields including `decided_by`, `decided_at`, fresh options, state reason and `superseded_by` (OQ-3, OQ-32); edit changes only the draft text and is an audit entry, one slot named by id for outcomes that book, fallback listed last (OQ-4); simulated clock and sent-date rule (OQ-5, OQ-24); working hours from the calendar provider (OQ-6, OQ-28); sender's zone (OQ-7); customer response status `null` (OQ-8); event key (OQ-9); CC'd attendees (OQ-10); `stale_leads` and `next_actions_due` (OQ-12); configured approver and localhost only (OQ-13); workflow trigger (OQ-14); no calendar data outside the mock window (OQ-15); seven request states (OQ-16); meeting and next action status values (OQ-17); re-check and `needs_review` (OQ-18, OQ-31); recorded steps and progress values (OQ-20, OQ-27); `create_reply_draft` then `send_draft` (OQ-25); after a rejection (OQ-26); no chosen slot for two outcomes (OQ-29); `API_PORT` (OQ-30); the `X-CRM-Token` header from `GET /session` (OQ-33); the API safety measures (section 10.1) and the repeat-approval check (TR-6).

**What is still a proposal in this document** (the requirements do not define it): the endpoint paths and payload shapes, the `Idempotency-Key` header and its replay table, the `409 availability_changed` and `502 approval_step_failed` responses, the step status labels, and the error codes of section 10.1. These are for the Slice 4 plan; hld.md section 12.2 lists what else is open and which slice needs it.
