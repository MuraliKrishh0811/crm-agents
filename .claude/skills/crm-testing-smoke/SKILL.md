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

A slice is done when its tests and the smoke test pass (R11). Commit only then, referencing requirement IDs. Run tests after every small step.

## `tests/` structure (folders exist, empty)

```
tests/
  agents/     exact-match + rubric tests (Python)
  backend/    curl scripts and scripted equivalents for every CRM API endpoint
  frontend/   Playwright scripts
  smoke/      the smoke test
```

Suggested files (finalize in each slice's plan): `agents/test_stage_exact.py` (TR-1), `agents/test_scheduling_exact.py` (TR-2), `agents/test_rubric.py` + `agents/rubrics/*.md` (TR-3), `agents/test_idempotency.py` (TR-6), `agents/test_model_accuracy.py` (TR-8), `agents/test_live_contract.py` (TR-7), `backend/curl/*.sh` and a scripted runner (TR-4), `frontend/*.spec.ts` (TR-5), `smoke/` (TR-9).

## Test types

| ID | What | How |
|---|---|---|
| TR-1 | Stage after every email, customer matching, duplicate F08b ignored, noise ignored, vague Tailspin email gets a clarification | Exact match against `data/synthetic/expected/expected_outcomes.json` |
| TR-2 | SCH-ADV, SCH-TAIL, SCH-WING outcome type and slots, incl. DST trap and non-blocking `free` event | Exact match against the key and section 10 |
| TR-3 | Summaries and drafted replies (no single right answer) | **Written rubric**: accuracy, completeness, tone, no invented facts. Store rubric files in `tests/agents/rubrics/`; record per-criterion scores per run. Scorer (human spot-check vs a judge model) and pass threshold are **open, ask the user**; llama3.1:8b as its own judge is weak |
| TR-4 | Every CRM API endpoint | A `curl` command and a scripted equivalent per endpoint, run against the running local system |
| TR-5 | Pipeline view, customer timeline, scheduling panel, approve/edit/reject | **Playwright** scripts. TODO: Playwright is not in `inputs/references.md`; verify against its official docs before writing, no snippets from memory |
| TR-6 | Idempotency | Replay the full email set twice; CRM state identical |
| TR-7 | Live Graph and Foundry/Azure OpenAI providers | Contract tests: real adapter code against sample responses shaped like real output; labeled contract tests, never live verification |
| TR-8 | Model accuracy | Report stage-classification accuracy per run with model name and `num_ctx`; used for the `qwen3:8b` comparison |
| TR-9 | Smoke | Below: warm-up, then (a) replay with no approval, then (b) explicit approval via the real endpoint |

Rules: tests may read the answer key, production code must not (R8). Add a guard test that fails if production code references the answer-key path or dataset client names. Never edit the dataset or key to make a test pass. LLM-dependent tests are non-deterministic: do not loosen exact-match; record the failure and the accuracy number.

## Smoke test (TR-9), run after every slice

Section 10 defines "final stage" as the state **after replaying all emails and before any human approval**. Approval is a separate action, so the smoke test has two parts that run in order against one system instance.

**Setup**

1. Start the system in local mode.
2. **Warm-up call to Ollama first** (the model unloads when idle; `crm-ollama-local-model`), and fail fast with a clear message if Ollama is down or `OLLAMA_MODEL` is not pulled.

**Part (a): replay, no approval**

3. Replay all emails against the simulated clock `2026-10-16T10:00:00` `America/Chicago`.
4. Assert each customer's final stage from section 10 and the key: Fabrikam Converted, Northwind Not Converted, Adventure Works Engagement, Tailspin Toys Engagement, Wingtip Toys Presentation/Follow-up.
5. Assert a **pending** scheduling request exists for Adventure Works (`recommend_slots`), Tailspin (`counter_propose`) and Wingtip (`update_existing_meeting`), with the expected slots and reasons (TR-2).
6. Assert nothing approval-gated happened (R5): no meeting created, the Wingtip event `wingtip-walkthrough-20261022` unchanged, no draft sent without an approval record.

**Part (b): explicit approval through the real approval endpoint** (the CRM API's approval route, FR-API-1 and FR-APP-2; never a direct repository or provider call)

7. Approve Adventure Works: the meeting is created once with attendees Emily, Raj, Oliver Bennett, Sophie Turner at the expected slot, join link stored as simulated (R10); stage moves to Presentation/Follow-up with a stage-history entry; approval records who and when (FR-APP-3).
8. Approve Tailspin: the counter-proposal reply is sent (local mode records it through the real `MailProvider`), no meeting is created, stage stays Engagement.
9. Approve Wingtip: the existing event is updated (not duplicated) to the expected new slot, `lisa.park@wingtiptoys.com` is added, stage stays Presentation/Follow-up.
10. Repeat each approval call: no duplicate meeting, event or sent message (R6). This repeat check is my addition, not in section 13; drop it if you disagree.

**Always**

11. Assert no duplicate records (Message-ID, meetings by key).

Failures stop the slice; they are fixed in code, not in the test or data.
