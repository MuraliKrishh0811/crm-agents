---
name: crm-testing-smoke
description: Testing and smoke-testing plan for CRM Agents - tests/ structure (agents, backend, frontend, smoke), exact-match tests against expected_outcomes.json, rubric scoring for summaries and drafts, curl API tests, Playwright UI scripts, idempotency, contract tests, and the smoke test with its Ollama warm-up. Use when writing tests, finishing a slice, or deciding whether a commit is allowed.
---

# Testing and smoke testing

## Always true (repeated in every project skill)

- **Everything is real.** Tests exercise real agents, real providers (local Ollama, `.eml` replay, mock calendar JSON, SQLite) and real API calls. No mocking, stubs, canned or hardcoded responses to make a test pass (R1).
- **Ollama is the local fallback** and is the real model in tests; start it and warm it up first.
- **Never read `.env`.** Use `example.env` only; tests never print settings.
- **`REQUIREMENTS.md` is authoritative** (section 13). Only `inputs/decisions.md` can override it.

## Commit gate

A slice is done when its tests and the smoke test pass (R11). Commit points exist only then. **The owner makes all commits**: show `git status`, propose a message that cites requirement IDs, and wait. Run tests after every small step. **Test runner: pytest** (approved in `decisions.md`; pinned in `inputs/references.md` as 9.1.1, test-only). Run skipped-test reasons visibly (`-rs`).

## `tests/` structure (folders exist, empty)

```
tests/
  agents/     exact-match + rubric tests (Python)
  backend/    curl scripts and scripted equivalents for every CRM API endpoint
  frontend/   Playwright scripts
  smoke/      the smoke test
```

Suggested files (finalize in each slice's plan): `agents/test_stage_exact.py` (TR-1), `agents/test_scheduling_exact.py` (TR-2), `agents/test_rubric.py` + `agents/rubrics/*.md` (TR-3), `agents/test_idempotency.py` (TR-6), `agents/test_model_accuracy.py` (TR-8), `agents/test_live_contract.py` (TR-7), `agents/test_request_lifecycle.py` (TR-10), `backend/test_approval_recheck.py` (TR-11), `backend/test_approval_failure.py` (TR-12), `backend/test_api_safety.py` (TR-13), `backend/curl/*.sh` and a scripted runner (TR-4), `frontend/*.spec.ts` (TR-5), `smoke/` (TR-9).

## Test types

| ID | What | How |
|---|---|---|
| TR-1 | Stage after every email, customer matching, duplicate F08b ignored, noise ignored, vague Tailspin email gets a clarification | Exact match against `data/synthetic/expected/expected_outcomes.json` |
| TR-2 | SCH-ADV, SCH-TAIL, SCH-WING outcome type and slots, incl. DST trap and non-blocking `free` event; **the reschedule lookup (FR-SCH-9, D11)**: W06 one match, several matches narrowed by day, several unresolved, no match (clarification, never a duplicate) | Exact match against the key and section 10; lookup cases built by the test (temporary calendar copy or the provider's `create_event`), never by editing the dataset |
| TR-3 | Summaries and drafted replies (no single right answer) | **Two layers (decisions.md, TR-3 scorer):** *gating*, deterministic checks that every date, name, number and company in a generated summary or draft appears in the source emails or CRM record and that required facts are present (must pass); *advisory*, a rubric score (accuracy, completeness, tone, actionability, 1 to 5) from the local model with a baseline recorded on the first run and regressions reported (never gates a slice). Rubric files in `tests/agents/rubrics/`; baselines in `tests/agents/baselines/`. The owner reads a sample of drafts before demos. llama3.1:8b as its own judge is weak; revisit with a stronger judge once live access exists |
| TR-4 | Every CRM API endpoint | A `curl` command and a scripted equivalent per endpoint, run against the running local system |
| TR-5 | Pipeline view, customer timeline, scheduling panel, approve/edit/reject | **Playwright** scripts. TODO: Playwright is not in `inputs/references.md`; verify against its official docs before writing, no snippets from memory |
| TR-6 | Idempotency | Replay the full email set twice: CRM state identical. **And** approve the same request twice: no duplicates (section 13 TR-6 now says both) |
| TR-7 | Live Graph and Foundry/Azure OpenAI providers | Contract tests: real adapter code against sample responses shaped like real output; labeled contract tests, never live verification |
| TR-8 | Model accuracy | Report stage-classification accuracy per run with model name and `num_ctx`; used for the `qwen3:8b` comparison |
| TR-9 | Smoke | Below: warm-up, then (a) replay with no approval, then (b) explicit approval via the real endpoint |
| TR-10 | Request lifecycle (FR-SCH-12) | Transitions match the requirement: `pending`; **superseded** by a newer email in the same thread with new times; **cancelled** by a withdrawal; **expired** when all offered windows are past. The clock is fixed at `SIMULATED_NOW` for a run (decisions.md OQ-24), and the three scenario windows (19 to 27 Oct) are after it, so **inject a later clock** to test expiry. Old requests are kept |
| TR-11 | Approval re-check (FR-APP-4) | Introduce a real calendar conflict after the proposal (write a busy event through the real calendar provider), then approve: the response is the `409 availability_changed` (proposed in `docs/api.md`), the state is `needs_review`, the fresh options replace the proposed slots, approval progress is `not_started`, **no event is created and nothing is sent**; approving one fresh option then works, and so does rejecting (OQ-31, OQ-32) |
| TR-12 | Approval failure (FR-APP-5, R6) | Force a real failure in one step (for example make the mail provider's send fail through a controllable real condition, not a stub): the approval is `partially_completed` with the failed step visible and earlier steps kept; retry completes with **no duplicate** meeting, event or sent message; each step has an `AgentRun` entry linked to the request |
| TR-13 | API safety (R5) | The approve endpoint rejects a foreign `Origin`, a missing `X-CRM-Token` header (the per-run token) and a wrong content type; each test also asserts the request is still `pending` and nothing was created or sent. Proposed extras: wrong token, `Origin: null`, wrong `Host`, foreign-origin preflight gets no CORS allow headers, no connection on a non-loopback address. See `docs/api.md` section 10.1 |

Rules: tests may read the answer key, production code must not (R8). Add a guard test that fails if production code references the answer-key path or dataset client names. Never edit the dataset or key to make a test pass. LLM-dependent tests are non-deterministic: do not loosen exact-match; record the failure and the accuracy number.

## Smoke test (TR-9), run after every slice

**Staged (decisions.md):** from Slice 1 on there is **one** smoke test, `tests/smoke/test_smoke.py`, covering everything built so far. An assertion that cannot exist yet appears as an explicit `not yet implemented (Slice N)` skip that shows in the output (`pytest -rs`), **never a silent pass**. It is complete, with no skips, at Slice 4d, where part (b) goes through the real approval endpoint. Before Slice 4d, approval in part (b) goes through `Orchestrator.approve` (the handler itself, never a direct repository or provider call).

Section 10 defines "final stage" as the state **after replaying all emails and before any human approval**. Approval is a separate action, so the smoke test has two parts that run in order against one system instance.

**Setup**

1. Start the system in local mode.
2. **Warm-up call to Ollama first** (the model unloads when idle; `crm-ollama-local-model`), and fail fast with a clear message if Ollama is down or `OLLAMA_MODEL` is not pulled.
2b. Get the per-run API token from `GET /session` (it is generated at API start, held in memory and never in `.env`); the writes in part (b) send it in `X-CRM-Token` with `Content-Type: application/json` and, on approve, an `Idempotency-Key`.

**Part (a): replay, no approval**

3. Replay all emails against the simulated clock `2026-10-16T10:00:00` `America/Chicago`.
4. Assert each customer's final stage from section 10 and the key: Fabrikam Converted, Northwind Not Converted, Adventure Works Engagement, Tailspin Toys Engagement, Wingtip Toys Presentation/Follow-up.
5. Assert a **pending** scheduling request (state `pending`, FR-SCH-12) exists for Adventure Works (`recommend_slots`), Tailspin (`counter_propose`) and Wingtip (`update_existing_meeting`), with the expected slots and reasons (TR-2). A request replaced by a newer email is `superseded` and kept for audit; it is not pending.
6. Assert nothing approval-gated happened (R5): no meeting created, the Wingtip event `wingtip-walkthrough-20261022` unchanged, no draft sent without an approval record.

**Part (b): explicit approval through the real approval endpoint** (the CRM API's approval route, FR-API-1 and FR-APP-2; never a direct repository or provider call)

7. Approve Adventure Works, naming exactly one proposed slot by id: the meeting is created once with attendees Emily, Raj, Oliver Bennett, Sophie Turner at the expected slot, join link stored as simulated (R10); stage moves to Presentation/Follow-up with a stage-history entry whose source is the approval; the request records `decision`, `decided_by` and `decided_at` (FR-APP-3), approval progress `completed`, and one `AgentRun` per approval step.
8. Approve Tailspin: the counter-proposal reply is sent (local mode records it through the real `MailProvider`), no meeting is created, stage stays Engagement.
9. Approve Wingtip: the existing event is updated (not duplicated) to the expected new slot, `lisa.park@wingtiptoys.com` is added, stage stays Presentation/Follow-up.
10. **Repeat-approval check (kept; required by TR-6 and recorded in `inputs/decisions.md`):** repeat each approval call; no duplicate meeting, event or sent message (R6).

**Always**

11. Assert no duplicate records (Message-ID, meetings by key).

**Approval and lifecycle tests beyond the smoke path** are now `TR-10` to `TR-13` in `REQUIREMENTS.md` section 13 (rows above); they cover FR-SCH-12, FR-APP-4, FR-APP-5 and the API safety measures, and the Definition of done requires them to pass (section 17). They use real providers; inject the failure or conflict with a real, controllable condition, not a stub (R1). An **edit** (changing only the draft reply text) is not a state change: test that it adds an audit entry and leaves `decision`, `state` and approval progress unchanged. After a conflict the approval progress returns to `not_started`, the fresh options replace the proposed slots (the earlier ones go to an audit entry), and the approver approves one fresh option or rejects (FR-APP-4; hld.md OQ-31, OQ-32).

Failures stop the slice; they are fixed in code, not in the test or data.
