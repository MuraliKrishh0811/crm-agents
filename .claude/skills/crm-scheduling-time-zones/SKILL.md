---
name: crm-scheduling-time-zones
description: Deterministic scheduling and time zone rules for CRM Agents - IANA zones and DST, window parsing to UTC, working-hours cap, blocking rules, ranking, the four outcomes, approval and idempotency, and the three dataset scenarios as test oracles (never special-cased). Use when writing or reviewing the Scheduler agent, anything touching dates or time zones, or its tests.
---

# Scheduling logic and time zones

## Always true (repeated in every project skill)

- **Everything is real.** The scheduler, calendar providers and model calls are real implementations. No mocking, stubs, canned or hardcoded responses, no hardcoded snippets or slots standing in for behavior.
- **Ollama is the local fallback** and only extracts or drafts text here (`crm-ollama-local-model`); all scheduling math is plain code.
- **`.env` (R7):** Claude never opens, prints, searches or copies a `.env*` file; use `example.env` only. The application's own settings loader may read `.env` when tests or smoke runs execute (Phase 1, no real secrets); it never prints values.
- **`REQUIREMENTS.md` is authoritative** (sections 7, 8, 10). `inputs/decisions.md` records owner decisions where it is silent.

## Split of work (R4)

| The model (text only) | Plain code (all decisions) |
|---|---|
| Detect scheduling intent; extract offered windows as stated (date phrase, start/end text, stated zone or hint, preferences like "mornings"); draft reply prose | Resolve relative dates ("next Thursday") against **the email's sent date in the sender's time zone** (FR-SCH-2); use the simulated clock only to discard times already in the past; convert to UTC; cap by working hours (taken per user from the `CalendarProvider`); read availability; apply blocking rules; intersect; rank; pick at most 3; choose the outcome; format and insert times into the reply |

Have the model draft prose around placeholders and let code fill slot times in the customer's zone (FR-SCH-8); do not let the model format or convert times.

## Time rules (R9)

- Store UTC plus the relevant IANA zone (for example `Europe/London`, `America/Chicago`). **Never** convert between regions with a fixed UTC offset; DST dates differ (UK ends Oct 25 2026, US Nov 1 2026, so London-Chicago is 6 hours before Oct 25 and 5 hours after).
- Zone abbreviations in email text (BST, GMT, MDT) are hints, not authority. **The sender's zone is determined in this order (FR-SCH-2; decisions.md OQ-7):** the contact's stored zone; else an explicit zone in the email text; else candidate zones implied by the `Date` header offset plus hints in the text, **validated in code**. If it is still ambiguous, ask the customer to confirm instead of guessing: the outcome is `request_clarification` asking for the zone, with no slots and no meeting (FR-SCH-3, decisions.md OQ-34).
- Use the language's IANA zone database. TODO: Python `zoneinfo` usage and the need for the `tzdata` package are not in `inputs/references.md`; verify against official Python docs before writing, and do not write conversion code from memory.
- The simulated clock for the dataset is `2026-10-16T10:00:00` in `America/Chicago`. In `example.env` it is `SIMULATED_NOW=2026-10-16T10:00:00` (naive local time) plus `SIMULATED_TZ=America/Chicago`; combine them with the IANA zone, never with a hardcoded offset. Per `inputs/decisions.md` (OQ-5), `SIMULATED_NOW` and `SIMULATED_TZ` in the environment override `organization.simulationNow` in `config/team.json`. The clock decides which emails have arrived and which offered times are already in the past; it is **not** the reference for relative dates (those use the email's sent date, FR-SCH-2). "Now" is always injected from config, never read from the system clock in scheduling code.

## Policy and working hours (never hardcoded)

**Policy from `config/team.json`:** organization zone `America/Chicago`; 30-minute granularity; default durations (intro 30, discovery 30, demo 60, walkthrough 60, kickoff 60); hard-blocking `busy`, `oof`; soft-blocking `tentative` (lower-ranked fallback, always shown with a warning, never silently ignored); non-blocking `free`, `workingElsewhere`; max 3 suggestions; approval always required. Read these at runtime.

**Working hours come from the `CalendarProvider`, per user** (REQUIREMENTS section 8, `inputs/decisions.md` OQ-6): local mode reads `workingHours` from `mock_calendars.json`; live mode would take them from Graph (UNVERIFIED). If a user has none, default to 08:00-17:00 Mon-Fri `America/Chicago`. `team.json` has no working-hour values. `get_availability` returns them per user next to the busy blocks: `{working_hours, busy_blocks: [{start, end, showAs}]}` (REQUIREMENTS section 6; decisions.md OQ-28). Availability outside the mock calendar window is unknown and not offerable, reason "no calendar data" (OQ-15). The window is read from the JSON (`2026-10-19T00:00` to `2026-10-31T00:00` America/Chicago) and is **end exclusive** (OQ-37): at or after 2026-10-31T00:00 is unknown.

## Algorithm outline

1. Detect intent in the **new** text only; never trigger from historical times in quoted or old emails (FR-SCH-1, FR-SCH-2). The Scheduler extracts the windows itself; the Ingestion Agent only passes on the cleaned new-email text (decisions.md OQ-11). Resolve relative dates against the email's sent date in the sender's zone and discard windows already in the past by the simulated clock.
2. No concrete times, or a sender zone that is still ambiguous: outcome `request_clarification` (a scheduling request, OQ-34), draft the question, create no meeting (FR-SCH-3). A clarification request stays `pending` until a newer email in the same thread offers concrete times and supersedes it (OQ-16).
3. Select attendees from assignment rules; add CC'd customer contacts as external attendees (FR-SCH-4). **Only assigned attendees block** (FR-SCH-10).
4. Convert each window to UTC; cap open-ended windows by each attendee's working hours (from the `CalendarProvider`); read availability through `CalendarProvider`; apply blocking rules (FR-SCH-5, FR-SCH-6).
5. Intersect in code, split into granularity slots of the meeting duration, rank, keep at most 3. Fallback slots with tentative attendees rank lowest and carry a warning.
6. Outcome, exactly one of `recommend_slots`, `counter_propose` (no overlap; 2 or 3 mutual slots in the customer's zone within stated preferences; no meeting created), `request_clarification`, `update_existing_meeting` (find and update the existing event, add new attendees, never create a duplicate) (FR-SCH-7 to FR-SCH-9).
   **Locating the meeting to reschedule (FR-SCH-9, decisions.md D11), plain code:** call `CalendarProvider.find_events` for the assigned attendees; keep upcoming (at or after the simulated now), non-cancelled events that include an external attendee address from the trigger email (From, To, Cc), falling back to the sender's domain read from that email at run time; exactly one match is the target; several are narrowed by the original meeting day the email mentions (the model extracts the phrase as text only; code resolves it with the sent-date rule); otherwise the outcome is `request_clarification` and **nothing is created**. Never match on customer names, event keys or dates from the dataset (R8). Events held on several attendees' calendars share one event key and count once.
7. Store a human-readable reason for every accepted and rejected slot (FR-SCH-11).

## Approval and idempotency

Nothing is booked, updated or sent until a person approves (R5, FR-APP-1 to 3); record the `decision` (`approve` or `reject`), `decided_by` and `decided_at` (REQUIREMENTS section 9). **Edit** changes only the draft reply text, is recorded as an audit entry and does not change the state (OQ-4). Approval names exactly one proposed slot by id; a tentative fallback is listed last with its warning. Meetings are keyed by iCalUId or a stable internal key; replay and re-approval never duplicate (R6, TR-6). Local mode persists created meetings so later availability sees them; the join link is stored as simulated (R10).

**Request states (FR-SCH-12):** `pending`, `approved`, `rejected`, `superseded`, `cancelled`, `expired`, `needs_review`. Per `decisions.md` (OQ-16): a newer email in the same thread offering new times **supersedes** the pending request; a withdrawal **cancels** it; it **expires** when all offered windows are past; old requests are kept for audit. TR-10 tests these transitions; the clock is fixed at `SIMULATED_NOW` for a run (OQ-24), so expiry needs an injected later clock. After a rejection the state is `rejected` and nothing happens automatically (OQ-26).

**Approval runs as recorded steps (FR-APP-4, FR-APP-5; decisions.md OQ-18, OQ-20).** The approval handler in the Orchestrator (not an agent) calls `CalendarProvider` and `MailProvider.send_draft`; agents only prepare drafts. Record the intent first (approval progress `in_progress`; the progress values are `not_started`, `in_progress`, `completed`, `partially_completed`), then in order: (1) re-check availability for the chosen slot; (2) create or update the event; (3) send the confirmation (`create_reply_draft` then `send_draft`, OQ-25); (4) write the CRM updates. Each step is idempotent and **its result is recorded as an `AgentRun` audit entry linked to the request**. The request `state` becomes `approved` once the re-check passes (OQ-27). If a conflict has appeared at step 1, do not book or send: mark the request `needs_review` with fresh options (TR-11). A later failure leaves the approval `partially_completed` and retryable, with no automatic rollback in Phase 1; the UI shows the failed step (TR-12). For outcomes with no chosen slot (`counter_propose`, `request_clarification`) the re-check is recorded as not applicable (OQ-29). After a conflict the approval progress returns to `not_started`, the fresh options replace the proposed slots (the earlier ones go to an audit entry), and the approver approves one fresh option or rejects (FR-APP-4; hld.md OQ-31, OQ-32).


## Test oracles (tests only, never production)

SCH-ADV (DST trap, tentative fallback), SCH-TAIL (no overlap, counter-propose, out-of-office, vague first email), SCH-WING (reschedule existing event located by `find_events`, `showAs: free` lunch does not block, unassigned team member out of office does not block). Also test the lookup itself: the W06 case (one match), several matches narrowed by day, several unresolved, and no match (clarification, never a duplicate). Exact expected slots live in REQUIREMENTS section 10 and `data/synthetic/expected/expected_outcomes.json`. Production code must not mention client names, email IDs or dataset dates (R8); if the data or key looks wrong, tell the user, do not change them.

## Graph note

On the live path, `getSchedule` statuses and time zone name handling are UNVERIFIED (`crm-graph-integration`).
