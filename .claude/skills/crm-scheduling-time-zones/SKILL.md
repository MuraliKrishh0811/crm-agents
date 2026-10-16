---
name: crm-scheduling-time-zones
description: Deterministic scheduling and time zone rules for CRM Agents - IANA zones and DST, window parsing to UTC, working-hours cap, blocking rules, ranking, the four outcomes, approval and idempotency, and the three dataset scenarios as test oracles (never special-cased). Use when writing or reviewing the Scheduler agent, anything touching dates or time zones, or its tests.
---

# Scheduling logic and time zones

## Always true (repeated in every project skill)

- **Everything is real.** The scheduler, calendar providers and model calls are real implementations. No mocking, stubs, canned or hardcoded responses, no hardcoded snippets or slots standing in for behavior.
- **Ollama is the local fallback** and only extracts or drafts text here (`crm-ollama-local-model`); all scheduling math is plain code.
- **Never read `.env`.** Use `example.env` only.
- **`REQUIREMENTS.md` is authoritative** (sections 7, 8, 10). Only `inputs/decisions.md` can override it.

## Split of work (R4)

| The model (text only) | Plain code (all decisions) |
|---|---|
| Detect scheduling intent; extract offered windows as stated (date phrase, start/end text, stated zone or hint, preferences like "mornings"); draft reply prose | Resolve relative dates against the simulated clock and the sender zone; convert to UTC; cap by working hours; read availability; apply blocking rules; intersect; rank; pick at most 3; choose the outcome; format and insert times into the reply |

Have the model draft prose around placeholders and let code fill slot times in the customer's zone (FR-SCH-8); do not let the model format or convert times.

## Time rules (R9)

- Store UTC plus the relevant IANA zone (for example `Europe/London`, `America/Chicago`). **Never** convert between regions with a fixed UTC offset; DST dates differ (UK ends Oct 25 2026, US Nov 1 2026, so London-Chicago is 6 hours before Oct 25 and 5 hours after).
- Zone abbreviations in email text (BST, GMT, MDT) are hints, not authority. Resolve the customer's IANA zone from contact data, the `Date` header, or the signature, and check it against the stated abbreviation; on a conflict flag it or ask for clarification rather than guessing.
- Use the language's IANA zone database. TODO: Python `zoneinfo` usage and the need for the `tzdata` package are not in `inputs/references.md`; verify against official Python docs before writing, and do not write conversion code from memory.
- The simulated clock for the dataset is `2026-10-16T10:00:00` in `America/Chicago`. In `example.env` it is `SIMULATED_NOW=2026-10-16T10:00:00` (naive local time) plus `SIMULATED_TZ=America/Chicago`; combine them with the IANA zone, never with a hardcoded offset. "Now" is always injected from config, never read from the system clock in scheduling code.

## Policy (source: `config/team.json`; never hardcoded)

Organization zone `America/Chicago`; working hours 08:00-17:00 Mon-Fri; 30-minute granularity; default durations (intro 30, discovery 30, demo 60, walkthrough 60, kickoff 60); hard-blocking `busy`, `oof`; soft-blocking `tentative` (lower-ranked fallback, always shown with a warning, never silently ignored); non-blocking `free`, `workingElsewhere`; max 3 suggestions; approval always required. Read these at runtime.

## Algorithm outline

1. Detect intent in the **new** text only; never trigger from historical times in quoted or old emails (FR-SCH-1, FR-SCH-2).
2. No concrete times: outcome `request_clarification`, draft the question, create nothing (FR-SCH-3).
3. Select attendees from assignment rules; add CC'd customer contacts as external attendees (FR-SCH-4). **Only assigned attendees block** (FR-SCH-10).
4. Convert each window to UTC; cap open-ended windows by working hours; read availability through `CalendarProvider`; apply blocking rules (FR-SCH-5, FR-SCH-6).
5. Intersect in code, split into granularity slots of the meeting duration, rank, keep at most 3. Fallback slots with tentative attendees rank lowest and carry a warning.
6. Outcome, exactly one of `recommend_slots`, `counter_propose` (no overlap; 2 or 3 mutual slots in the customer's zone within stated preferences; no meeting created), `request_clarification`, `update_existing_meeting` (find and update the existing event, add new attendees, never create a duplicate) (FR-SCH-7 to FR-SCH-9).
7. Store a human-readable reason for every accepted and rejected slot (FR-SCH-11).

## Approval and idempotency

Nothing is booked, updated or sent until a person approves (R5, FR-APP-1 to 3); record who and when. Meetings are keyed by iCalUId or a stable internal key; replay and re-approval never duplicate (R6). Local mode persists created meetings so later availability sees them; the join link is stored as simulated (R10).

## Test oracles (tests only, never production)

SCH-ADV (DST trap, tentative fallback), SCH-TAIL (no overlap, counter-propose, out-of-office, vague first email), SCH-WING (reschedule existing event, `showAs: free` lunch does not block, unassigned team member out of office does not block). Exact expected slots live in REQUIREMENTS section 10 and `data/synthetic/expected/expected_outcomes.json`. Production code must not mention client names, email IDs or dataset dates (R8); if the data or key looks wrong, tell the user, do not change them.

## Graph note

On the live path, `getSchedule` statuses and time zone name handling are UNVERIFIED (`crm-graph-integration`).
