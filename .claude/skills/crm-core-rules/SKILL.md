---
name: crm-core-rules
description: Core rules for the CRM Agents project (R1-R12 from REQUIREMENTS.md), the confirmed decisions D1-D10, and the working method (plan first, small slices, tests, commit gate). Use at the start of any planning, coding, review or commit in this repo, and whenever instructions seem to conflict or something is ambiguous.
---

# CRM Agents: core rules

## Always true (repeated in every project skill)

- **Everything is real.** Agents, Graph calls, provider adapters and model calls are real implementations. No mocking, stubs, canned or hardcoded responses, and no hardcoded snippets standing in for behavior (R1, R8).
- **Ollama is the local fallback.** Local mode (Ollama + `.eml` files + mock calendar JSON + SQLite) is the working system in Phase 1 and the default (R3).
- **Never read `.env`.** Use `example.env` only. `.claude/settings.json` denies `Read(./.env)` and `Read(./.env.*)`.
- **`REQUIREMENTS.md` is authoritative.** Only `inputs/decisions.md` can override it. Do not edit `REQUIREMENTS.md`; propose changes to the user.

## Source of truth, in order

1. `REQUIREMENTS.md`
2. `inputs/decisions.md` (confirmed decisions)
3. `docs/architecture/eraser-code.txt` (authoritative; `decisions.md` says no rendered image is kept in the repository)
4. `inputs/references.md` (the only allowed authority for Agent Framework, Foundry/Azure OpenAI, Ollama, Graph, taste-skill, graphify)
5. `inputs/crm_scheduling_agents_project_description.txt` is background only.

## Hard rules

| ID | Rule | How to apply |
|---|---|---|
| R1 | Real code only | Never stub an agent, provider or API call to make a demo or test pass |
| R2 | Provider interfaces | Agents use only MailProvider, CalendarProvider, ChatModelProvider, CrmRepository (see `crm-provider-pattern`) |
| R3 | Local default | Live providers (Graph, Azure OpenAI/Foundry) are written from docs, disabled by default, refuse to start without config, labeled `implemented, unverified` |
| R4 | Deterministic scheduling | Time zones, overlap, durations, working hours, blocking rules are plain code. The model only classifies, extracts and drafts text (see `crm-scheduling-time-zones`) |
| R5 | Human approval | Nothing is booked, updated or sent without an explicit approval action |
| R6 | Idempotency | Emails keyed by Message-ID, meetings by iCalUId or a stable internal key; replay must not duplicate |
| R7 | Secrets | See `crm-security-env` |
| R8 | No test gaming | Production code never special-cases client names, email IDs, dates or answers; only tests read `expected_outcomes.json` |
| R9 | Time | Store UTC plus IANA zone; never a fixed UTC offset between regions |
| R10 | Label simulation | Simulated values (for example a Teams join link) are marked simulated in data and UI |
| R11 | Test as you go | Every slice ships with tests and passes the smoke test (see `crm-testing-smoke`) |
| R12 | Ask when blocked | Missing access, decision or documentation: say so and stop on that item |

## Confirmed decisions (`inputs/decisions.md`)

Python backend (D1); React + Vite + TypeScript (D2); SQLite locally behind `CrmRepository` (D3); Claude Code (D4); Ollama `llama3.1:8b` on a MacBook Air M4 with 16 GB RAM, name kept in `OLLAMA_MODEL`, `qwen3:8b` compared later via TR-8 (D5); Teams agent after the web dashboard (D6); Graph permission set and approver deferred to IT, written as "to be confirmed" in `docs/first_day_with_access.md` and never scoped in code (D7); hosting out of Phase 1 (D8); plain Python orchestrator behind an `Orchestrator` interface for Phase 1, with Agent Framework Workflows revisited once live access exists and the outcome recorded in `decisions.md` (D9); Python 3.13, with Python 3.14 not used (D10).

## Working method (`CLAUDE.md`)

- Read `REQUIREMENTS.md` and `inputs/decisions.md` before any planning or coding. Reference requirement IDs (`FR-SCH-3`, `TR-2`) in plans, tests and commit messages.
- Make a plan first and wait for approval. Work in small vertical slices (order in REQUIREMENTS section 16); run tests after each.
- Verify Microsoft Graph, Agent Framework, Azure OpenAI/Foundry and Ollama details against current official docs listed in `inputs/references.md`. Record URL, library version and retrieval date next to the code that uses them. Mark anything unverified `UNVERIFIED`. Never rely on memory.
- Commit points: only when the slice's tests and the smoke test pass. **The owner makes all commits**: at each commit point show `git status`, propose a message with requirement IDs and wait; never commit.
- Pin exact versions (no ranges). Do not upgrade without a reason recorded in `decisions.md`.

## Domain constants

- Stages: Initial Lead, Engagement, Presentation/Follow-up, Converted, Not Converted. Every change is recorded in stage history (previous, new, timestamp, reason, source email).
- Scheduling outcomes, exactly one of: `recommend_slots`, `counter_propose`, `request_clarification`, `update_existing_meeting`.
- Simulated clock for the dataset: `2026-10-16T10:00:00` in `America/Chicago`; `SIMULATED_NOW` and `SIMULATED_TZ` in the environment override `organization.simulationNow` in `config/team.json`. The clock decides which emails have arrived and which offered times are past; relative dates resolve against the email's sent date (FR-SCH-2).
- Scheduling request states (FR-SCH-12): `pending`, `approved`, `rejected`, `superseded`, `cancelled`, `expired`, `needs_review`. Scheduling **policy** comes from `config/team.json`; **working hours** come from the `CalendarProvider` per user (default 08:00-17:00 Mon-Fri `America/Chicago`). Neither is hardcoded.
- All design questions OQ-1 to OQ-33 and the API safety rules are resolved in `inputs/decisions.md` (its OQ numbers refer to `docs/hld.md` section 12). Anything not listed there is resolved, and then recorded in that file, when the slice that needs it starts; `docs/hld.md` section 12.2 lists what is still open and which slice needs it. Audit goes through `CrmRepository`; after approval the Orchestrator's approval handler books and sends (see `crm-provider-pattern`).
- Approval fields (REQUIREMENTS section 9): `decision` is `approve` or `reject`; `decided_by`, `decided_at`; approval progress is `not_started`, `in_progress`, `completed` or `partially_completed`; each approval step's result is an `AgentRun` linked to the request. Editing changes only the draft text and is an audit entry. Tests TR-10 to TR-13 cover request lifecycle, approval re-check, approval failure and API safety (see `crm-testing-smoke`).

## Do not

Read `.env`; use an LLM for time zone conversion or slot intersection; book or send without approval; stub or hardcode behavior; special-case dataset values; use a fixed UTC offset; modify the dataset or answer key to make tests pass; claim live Graph or Azure behavior is verified; start coding before the plan is approved.
