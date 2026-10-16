# Project decisions

REQUIREMENTS.md is authoritative. This file records owner decisions and resolutions where REQUIREMENTS.md is silent. A decision that changes a rule must also be written into REQUIREMENTS.md by the owner. If the two still differ, REQUIREMENTS.md prevails and the difference is reported.

## Build decisions

- D1 Backend language: Python
- D2 Frontend: React (Vite + TypeScript)
- D3 CRM store: SQLite local for Phase 1. A live store (Azure SQL, Dataverse or other) is deferred behind CrmRepository.
- D4 Coding agent: Claude Code
- D5 Ollama model: llama3.1:8b. Confirmed for a MacBook Air M4 with 16 GB RAM. Compare qwen3:8b against it using TR-8 later. Keep the model name in OLLAMA_MODEL config. Keep prompts short and use a small context window. The smoke test must include a warm-up call, because Ollama unloads idle models.
- D6 Teams agent: after the web dashboard.
- D7 Graph permissions: deferred. The permission set and approver are decided with IT when live access is requested. In Phase 1, write the permission needs into docs/first_day_with_access.md as "to be confirmed". Do not scope permissions in code.
- D8 Hosting: deferred. Out of scope for Phase 1.
- D9 Orchestration: plain Python orchestrator behind an Orchestrator interface for Phase 1. Revisit Agent Framework Workflows once live access exists and record the outcome. Reason: fixed pipeline with a human approval gate, easier to test, and the framework's workflow and Ollama packages are beta.
- D10 Python version: 3.13. The project venv is created on Python 3.13 (the owner recreated it; 3.13.15 observed on 2026-10-16). Python 3.14 is not used.
- D11 Wingtip event lookup (plan item 3c): add CalendarProvider.find_events(users, attendee_addresses, start, end) to REQUIREMENTS section 6. Lookup rule as in FR-SCH-9. No customer names, event keys or dates from the dataset in production code (R8). In live mode the Graph call that provides attendees and iCalUId is UNVERIFIED; check the Graph docs when writing the live provider.

## Authority and references

- AUTHORITY: REQUIREMENTS.md is the source of truth. inputs/crm_scheduling_agents_project_description.txt is background only. If they differ, follow REQUIREMENTS.md.
- ARCHITECTURE: docs/architecture/eraser-code.txt is the authoritative source. No rendered image is kept in the repository.

## Design decisions (OQ numbers refer to docs/hld.md section 12)

- OQ-1 Audit: audit entries are written through CrmRepository (separate tables, same database in Phase 1). There are still exactly four provider interfaces. The architecture diagram is updated to match.
- OQ-2 Sending: after approval, the Orchestrator's approval handler calls CalendarProvider (create or update event) and MailProvider.send_draft. Agents only prepare drafts.
- OQ-3 Data model additions (REQUIREMENTS section 9 has the full field list): SchedulingRequest gets draft reply, state, decision (approve or reject), decided_by, decided_at, approval progress, fresh options, state reason and superseded_by. StageHistory source can be an email or an approval.
- OQ-4 Edit changes only the draft reply text and is recorded as an audit entry. The request state does not change (REQUIREMENTS section 9: decision is approve or reject only). For outcomes that book (recommend_slots, update_existing_meeting), approval names exactly one proposed slot by id. A tentative fallback is listed last with its warning.
- OQ-5 Simulated clock: SIMULATED_NOW and SIMULATED_TZ in the environment override organization.simulationNow in team.json. The clock decides which emails have arrived and which offered times are already in the past. Relative dates in an email ("next Thursday") resolve against that email's sent date in the sender's time zone, not against the simulated clock.
- OQ-6 Working hours come from the CalendarProvider per user (local mode: workingHours in mock_calendars.json; live mode: returned by Graph). config/team.json holds policy only (durations, granularity, blocking rules, max suggestions). If a user has no working hours, default to 08:00-17:00 Mon-Fri America/Chicago.
- OQ-7 Customer's time zone: the contact's stored zone; else an explicit zone in the email text; else candidates from the Date header offset plus hints in the text, validated in code. If still ambiguous, ask the customer to confirm (same as FR-SCH-2).
- OQ-8 Customer response status in local mode is stored as null and shown as "not available (simulated)". Live mode reads the attendee response status (UNVERIFIED).
- OQ-9 Local event key is derived deterministically from the scheduling request id. Live mode stores the iCalUId returned by Graph and keeps the internal key as the idempotency key.
- OQ-10 Relevant customer attendees are CC'd external addresses at the customer's domain on the trigger email, shown to the approver before approval.
- OQ-11 Slot extraction belongs to the Scheduler Agent (FR-SCH-2). The Ingestion Agent only passes on the cleaned new-email text.
- OQ-12 stale_leads takes a threshold in days from configuration (STALE_LEAD_DAYS=14 confirmed as the starting value). next_actions_due(range) is inclusive on both ends and returns open actions only.
- OQ-13 Phase 1 API: listens on localhost only. The approver is a configured local user name (APPROVER_USER, no login screen), recorded on every approval. Real authentication (Entra ID) is designed in the docs, marked UNVERIFIED, and built after live access exists.
- OQ-14 The workflow trigger returns 202. One run at a time (a second request gets 409). Scope is all messages or one message. Messages are processed sequentially in date order. Progress is read with GET.
- OQ-15 Availability outside the mock calendar window is treated as unknown and not offerable, with the reason "no calendar data".
- OQ-16 Scheduling request states (seven, per FR-SCH-12): pending, approved, rejected, superseded, cancelled, expired, needs_review. A newer email in the same thread offering new times supersedes the pending request. A withdrawal cancels it. It expires when all offered windows are past. Old requests are kept for audit.
- OQ-17 Meeting status: scheduled, rescheduled, cancelled. Next action status: open, done, dismissed.
- OQ-18 At approval, re-check availability for the chosen slot. If a conflict has appeared, do not book. Mark the request needs_review with fresh options (see OQ-31 and OQ-32).
- OQ-19 Classifier input: new email text plus current stage, running summary, and the most recent engagement entries, bounded to fit the context window.
- OQ-20 Approval runs these steps in order: re-check availability, create or update the event, send the confirmation, write CRM updates. Each step is idempotent and its result is recorded. On failure the approval stays partially_completed and can be retried. No automatic rollback in Phase 1. The UI shows the failed step. Progress values are defined in OQ-27.
- OQ-21 PROVIDER_MODE sets the default for all four providers. A non-empty per-provider key overrides it.
- OQ-22 Local updates to events that came from the mock JSON are stored in a writable SQLite overlay keyed by event key and merged over the read-only JSON on read. The dataset files never change.
- OQ-23 The running summary is kept as append-only Engagement entries of type note marked as the running summary. The latest one is current.
- OQ-24 The simulated clock is fixed at SIMULATED_NOW for the whole run. Relative dates use each email's sent date anyway.
- OQ-25 The approval handler calls create_reply_draft and then send_draft in the "send confirmation" step. Before approval only the draft text exists on the request.
- OQ-26 After a rejection the state is rejected and nothing happens automatically. An optional reason is recorded. A new request is made only when a new email arrives.
- OQ-27 The decision, decided_by and decided_at are recorded at once. State becomes approved after the availability re-check passes (or needs_review on a conflict). Approval progress is the section 9 field (not_started, in_progress, completed, partially_completed), and each step's result is an AgentRun audit entry linked to the request.
- OQ-28 get_availability returns per user working_hours next to busy_blocks (now in REQUIREMENTS section 6). No new interface.
- OQ-29 For counter_propose and request_clarification there is no chosen slot, so the re-check step is recorded as not applicable. It runs for recommend_slots and update_existing_meeting.
- OQ-30 The API port comes from configuration (API_PORT). No version prefix in Phase 1.
- OQ-31 After a re-check conflict, approval progress returns to not_started. The approver approves a fresh option or rejects.
- OQ-32 Fresh options replace the proposed slots. The earlier ones are kept in an audit entry. State reasons are read from audit entries. superseded_by links to the newer request.
- OQ-33 The token header is X-CRM-Token, fetched from GET /session.
- OQ-34 Clarification requests are scheduling requests with outcome request_clarification. A newer email in the same thread that offers concrete times supersedes it (OQ-16). After 3c, T01's request is still pending; the scenario trigger requests (A05, T03, W06) are asserted by trigger email, and 3d.4 supersedes T01's request. An ambiguous sender time zone also produces request_clarification (FR-SCH-3).
- OQ-35 Test reports (TR-8 accuracy, TR-3 scores) go to reports/ (git-ignored). Baselines are copied to tests/baselines/ only when the owner decides. Review and resume prompts may run pytest and write only to reports/ and temp directories.
- OQ-36 Approve may carry an optional edited draft reply body. Orchestrator.approve accepts it, records the edit as an audit entry (OQ-4) and sends the approved text. Tested in 3e and 4d.
- OQ-37 The mock calendar window is end exclusive. Availability at or after 2026-10-31T00:00 is unknown (OQ-15).
- OQ-38 Orchestrator.approve exists from 3e and is unit-tested there. The smoke-test approval assertions become real at 3f.5.
- ENV LOADER is now amended into REQUIREMENTS R7. The application's own loader may read .env while it holds no real secrets.

## Additional rules

- API safety (api.md section 10.1): bind 127.0.0.1 only; Origin and Host checks; CORS limited to the dashboard origin (DASHBOARD_ORIGIN); JSON content type plus the X-CRM-Token header on approve; a random per-run token that is not stored in .env. Test: TR-13.
- Approval idempotency (R6): approving the same request twice creates no duplicates.
- Smoke test (staged): from Slice 1 on there is one smoke test, tests/smoke/test_smoke.py, covering everything built so far. Assertions that cannot exist yet appear as explicit "not yet implemented" skips in the output, never silent passes. It is complete, with no skips, at Slice 4d.
- Test runner: pytest is approved. Its exact version is proposed from PyPI with its release date, spot-checked by the owner, and only then pinned in inputs/references.md. Approved in principle, each to be pinned at the start of the slice that needs it with the same propose-then-check step: pydantic (Slice 2), FastAPI and uvicorn (Slice 4), React, Vite, TypeScript and Playwright (Slice 4). Any other dependency needs a question first.
- Commits: the owner makes all commits (the docs-only commit is tagged docs-baseline). At each commit point Claude shows git status, proposes a message and waits.
- Dataset check (Slice 0): generate.py is run on a copy. calendars/mock_calendars.json, config/team.json and expected/expected_outcomes.json are compared byte for byte. The .eml files are compared by parsed headers, bodies and attachments, because Python's email library picks random multipart boundaries. The dataset is never changed.
- SLICE 0 ONLY: the owner runs the .env key-name check and pastes the output, so Claude executes nothing that reads .env during Slice 0. From Slice 1 on, the amended R7 applies: the application's own settings loader may read .env while it holds no real secrets.
- Any question not listed here is resolved when the slice that needs it starts, and then recorded in this file.

TR-3 scorer (Phase 1): two layers. Gating: deterministic checks that every date, name, number and company in a generated summary or draft appears in the source emails or CRM record, and that required facts are present. Must pass. Advisory: rubric score (accuracy, completeness, tone, actionability, 1-5) from the local model; record a baseline on the first run and report regressions; never gates a slice. The owner reads a sample of drafts before demos. Revisit with a stronger judge model once live access exists.

ENV LOADER (Phase 1): tests and smoke runs that Claude executes may use the application's settings loader on .env, because .env contains no secrets in Phase 1. Claude still never opens, prints or searches .env itself. The loader and all logging must never print configuration values, only key names and set/blank status. Settings objects must redact values in their string form. Revisit before any real secret (keys, tokens, passwords) is placed anywhere in this project; at that point use managed identity or inline environment variables instead.
