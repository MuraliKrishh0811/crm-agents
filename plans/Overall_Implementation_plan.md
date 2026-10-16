# Overall implementation plan

Status: **revised 2026-10-16 with your seven decisions applied (recorded in `inputs/decisions.md`: D10 and the staged smoke test, pytest approval, commit policy and dataset-check rules). No application code exists; Slice 0 starts when you say go.** `CLAUDE.md` says to plan first and wait for approval.

Companion file: [step_by_step_implementation_checklist.md](step_by_step_implementation_checklist.md) (every item with requirement IDs, files and an acceptance check).

Authority: `REQUIREMENTS.md` is authoritative (R1 to R12, section 16 order). `inputs/decisions.md` records D1 to D11, OQ-1 to OQ-33, the TR-3 scorer and the process decisions of 2026-10-16 (staged smoke test, pytest, dependency approvals in principle, commits, dataset check). `inputs/references.md` holds the only approved dependencies and pins. Design detail is in `docs/hld.md`, `docs/lld.md`, `docs/api.md`; live-access checks are in `docs/first_day_with_access.md`; the project skills in `.claude/skills/` carry the rules and the UNVERIFIED snippets.

Hard constraints for the whole plan: all code is real (R1); no `.env` is ever read (R7); live Graph, Entra ID, Azure OpenAI and Foundry behavior stays UNVERIFIED until access exists (section 18 of the requirements); `REQUIREMENTS.md` and the dataset are never edited to make a test pass.

## 1. How the slices are cut

`REQUIREMENTS.md` section 16 defines six slices. Several are too large to review in one sitting, so each is split into lettered **sub-slices** (1a, 1b, ...). **Each sub-slice is a unit of work you can review in one sitting and has its own commit point.** Slice 0 (environment) comes first.

| Slice | Requirements section 16 meaning | Sub-slices |
|---|---|---|
| 0 | Environment (added by you) | 0 (one sitting) |
| 1 | Provider interfaces, local mail provider, CRM repository on SQLite | 1a domain, config, interfaces; 1b SQLite repository; 1c local mail provider; 1d composition root, logging, Slice 1 smoke assertions |
| 2 | Ingestion agent and stage classifier on Ollama | 2a model provider and audit; 2b ingestion and CRM Writer; 2c orchestrator and stage classifier; 2d summary, next action, TR-3 scorer |
| 3 | Scheduler agent, validated on all three scenarios | 3a calendar provider and time logic; 3b availability and outcomes; 3c Scheduler Agent; 3d drafts and request lifecycle; 3e approval handler; 3f approval tests |
| 4 | CRM API, then web dashboard; Teams agent per D6 | 4a API foundation and safety; 4b read endpoints; 4c workflow and edit/reject endpoints; 4d approve endpoint and full smoke; 4e dashboard pipeline and customer pages; 4f scheduling panel and approval flow; 4g audit view and UI polish; 4h Teams agent |
| 5 | Live providers written from docs, contract tests, first-day checklist | 5a live model adapters; 5b live mail; 5c live calendar; 5d first-day checklist and Phase 1 close-out |
| 6 | Switch to live by configuration when access arrives | 6 (blocked until access) |

For every slice the checklist gives: a definition of done, the tests that must pass, the smoke test, a commit point, and the `hld.md` section 12.2 open items the slice settles. This document gives the same at slice level (section 8).

## 2. What I found on this machine (read-only checks, 2026-10-16)

| Fact | Consequence |
|---|---|
| `.venv` is now **Python 3.13.15** (you recreated it, D10). Before your change it held only `pip` | Slice 0 verifies it is clean (only `pip`) and does the first real install on 3.13. The 2026-10-16 dry-run ran on 3.14.4, so the pins are **unproven on 3.13** until the real install and import test |
| Python 3.14 is not used (D10); 3.12 is not installed | **No branch for other Python versions.** If a pinned package fails to install or import on 3.13, I stop and ask you what to do |
| Node 24.21.0 and npm 11.19.0 are present | Enough for Slice 4 once you approve the frontend dependencies (none are in `references.md`) |
| Ollama 0.40.5 is installed and `llama3.1:8b` (4.9 GB) is already pulled | Slice 0 confirms it and does the warm-up test; no download needed unless it has gone missing |
| `data/synthetic/generate.py` uses only the standard library (`zoneinfo` included), reads no input files, and **writes into its own folder** | Slice 0 runs a copy of the script in an empty scratch folder (so every output is freshly written) and compares with `data/synthetic`: `calendars`, `config` and `expected` files byte for byte, the `.eml` files by parsed headers, bodies and attachments (multipart boundaries are random). The dataset itself is never touched |
| 32 `.eml` files in 6 folders; all dated before the simulated clock (latest 16 Oct 07:12 CT) | Replay sees every email with the clock fixed at `SIMULATED_NOW` (OQ-24) |
| `example.env` now holds starting values and comments for all 28 keys (live keys and `DATABASE_URL` blank; no secrets; checked 2026-10-16); `.gitignore` covers `.env`, `.venv`, `*.db` | You created `.env` yourself with non-secret values; I never open it. Slice 0 checks key names without values (0.14b) and Slice 1a runs the app's own loader (1a.4b) |
| Docs, skills and decisions are committed (HEAD `543ba0c`, "Finalize docs and skills; add TR-3 scorer decision"); the `docs-baseline` tag is not there yet; `plans/` and the latest `decisions.md` edits are uncommitted | You make the docs-only commit and the `docs-baseline` tag; Slice 0 item 0.2 only checks they exist |
| `tests/` has empty `agents`, `backend`, `frontend`, `smoke` folders | Matches the structure in the `crm-testing-smoke` skill |

## 3. Decisions you made (2026-10-16) and what is still needed from you

Recorded in `inputs/decisions.md` unless noted.

| # | Your decision | Effect on this plan |
|---|---|---|
| 1 | **Staged smoke test approved.** From Slice 1 on there is one smoke test covering everything built so far; assertions that cannot exist yet are explicit "not yet implemented" skips in the output, never silent passes; complete at 4d | Section 6; items 1a.7, 1d.3, 2c.6, 3f.5, 4d.4 |
| 2 | **pytest approved and now pinned** (`pytest==9.1.1`, test-only, in `references.md`). Approved in principle, each pinned at the start of the slice that needs it with the same propose-then-check step: pydantic (Slice 2), FastAPI and uvicorn (Slice 4), React, Vite, TypeScript and Playwright (Slice 4). Nothing else without asking | Section 5; items 0.2, 2a.1, 4a.1, 4e.1 |
| 3 | **D10: Python 3.13.** You recreated the venv on 3.13; Slice 0 starts from a clean 3.13 venv; the 3.14 branch is dropped | Slice 0, risks |
| 4 | **You make all commits.** At each commit point I show `git status`, propose a message and wait. You made the docs-only commit and will tag it `docs-baseline` | Every commit-point item |
| 5 | **`hld.md` section 12.2 updated:** lock file, `pip check` and the warm-up item moved to Slice 0; TR-3 scorer marked as decided | Done in `hld.md`; section 9 here matches |
| 6 | **Dataset check:** `generate.py` on a copy; `calendars`, `config`, `expected` byte for byte; `.eml` by parsed headers, bodies and attachments | Item 0.11 |
| 7 | **Slice-start choices: ask as planned; Wingtip event lookup answered as D11.** You added `CalendarProvider.find_events` to `REQUIREMENTS.md` section 6, rewrote FR-SCH-9 with the lookup rule, and recorded D11 | Item 3c.2 is now an implementation item with tests for the W06 case, several matches and no match; local `find_events` is in 3a.2; live in 5c.2 |
| 8 | **`.env` created by you; I do not read it.** Slice 0 confirms configuration without my reading the file | Items 0.14, 0.14b, 1a.4b |

**Still needed from you**

1. **Nothing is waiting on the pytest pin**: it is in `references.md` (item 0.2 only checks the file).
2. **How to run the key-name check** (item 0.14b): you run it and paste the names-only output, or I run it knowing it opens `.env` and prints names only. The application's own loader is then confirmed in 1a.4b.
3. **The `docs-baseline` tag** (item 0.2): not present yet (`git tag` is empty); I only check that it exists.
4. **Nothing else is outstanding for the Wingtip lookup**: D11 and FR-SCH-9 settle it.

## 4. Standing rules and the "stop and ask me" points

These apply to every sub-slice and are repeated in the checklist where they bite. **STOP AND ASK** means: I stop, state what I found, and wait for your answer.

| # | Stop and ask before... | Why |
|---|---|---|
| S1 | adding **any dependency not in `inputs/references.md`**. pytest is approved; pydantic, FastAPI, uvicorn, React, Vite, TypeScript and Playwright are approved in principle but each still needs its propose-then-check pin step (exact version and release date from the registry, you spot-check, then `references.md`) at the start of the slice that needs it. Everything else (for example `pytest-asyncio`, `beautifulsoup4`, `python-dotenv` used directly, linters): ask first | `references.md` pins exact versions; section 0 item 5 of the requirements; `decisions.md` |
| S2 | **changing any test** to make it pass, loosening an assertion, or **changing the dataset or the answer key** (`data/synthetic/**`) | R8 and section 10: tests are not gamed and the data is not edited. If I think the data or key is wrong I tell you |
| S3 | relying on anything **unverified**: an API signature, a doc detail, a Microsoft Graph or Azure behavior, a flag, a browser behavior. I verify against the official source first and record the URL and date next to the code; if I cannot, I stop (R12) | `CLAUDE.md` and requirements section 0 item 5 |
| S4 | a pinned package failing to install or import on Python 3.13, or any wish to recreate the venv or change the Python version. There is no automatic fallback; I report the exact error and wait | D10 |
| S5 | every **commit point**: **you make all commits**; I show `git status`, propose a message that cites requirement IDs, and wait. I never commit. Also anything outward-facing | `decisions.md` (commits) |
| S6 | a design choice that `decisions.md` leaves to "the slice that needs it". I propose, you decide, then **I record it in `decisions.md`** | `decisions.md`, last rule of "Additional rules". The checklist lists these as **slice-start questions** per slice |
| S7 | pulling or switching Ollama models (`qwen3:8b` comparison is later, TR-8) | D5 |
| S8 | a model-dependent exact-match test (TR-1, TR-2) failing: I report the failures and accuracy, and propose options (prompt change, deterministic guard, model comparison). I **do not loosen the test** | R4, R8, `crm-testing-smoke` |
| S9 | running anything that writes outside the repo (other than the scratch directory), installs system software, or reads outside the project | safety |

Always true, never a question: I never read, print or open any `.env*` file; I write no production behavior that special-cases dataset names, email IDs or dates (R8); nothing is booked, updated or sent without an approval action (R5); no stubs or hardcoded responses (R1); `REQUIREMENTS.md` is not edited.

## 5. Dependency register

**Approved and pinned** (`inputs/references.md`; install the exact set; **never** the `agent-framework` meta-package, because it pulls in `agent-framework-ollama` which needs `ollama<0.5.4`):

`agent-framework-core 1.22.0`, `agent-framework-foundry 1.15.0`, `agent-framework-openai 1.17.0`, `azure-identity 1.26.0`, `ollama 0.6.3`, `msgraph-sdk 1.64.0`.

**Approved and pinned (test-only):** `pytest==9.1.1` (`inputs/references.md`: "Test-only: pytest 9.1.1. Not part of the runtime install set"; PyPI upload 2026-06-19, `Requires-Python >=3.10`, classifiers include 3.13; transitive `iniconfig`, `packaging`, `pluggy<2,>=1.5`, `pygments`). It goes in `requirements-dev.txt`, not `requirements.txt`. `pytest-asyncio` is **not** approved; async tests need a question first.

**Approved in principle, pinned at the start of the slice that needs them** (propose exact version and release date from the registry, you spot-check, then `references.md`): `pydantic` (Slice 2, item 2a.1; it is already installed because `ollama` requires it), `fastapi` and `uvicorn` (Slice 4, item 4a.1), `react`, `vite`, `typescript` and `playwright` (Slice 4, item 4e.1). Using a transitive package directly in our code is still a dependency decision, so pydantic gets its propose-then-check step first.

**Not approved: ask first** (each with a standard-library option where one exists):

| Need | Slice | Standard-library option | Note |
|---|---|---|---|
| `.env` loading in the application | 1a | a small loader | `python-dotenv` is a transitive package; direct use needs approval |
| Time zone data | 1a | `zoneinfo` + system tz database (macOS has it) | `tzdata` only if a lookup fails |
| HTML to text for emails | 2b | `html.parser` | `beautifulsoup4` only if the stdlib route proves inadequate |
| Async test support, mocking helpers | any | `asyncio.run` inside tests | `pytest-asyncio` not approved |
| HTTP client for contract tests | 5 | `urllib` / transitive `httpx` | decide at 5a |
| Linting or formatting tools | any | none | optional; not planned |

## 6. Smoke test staging (approved, `decisions.md`)

From Slice 1 on there is **one** smoke test, `tests/smoke/test_smoke.py`, covering everything built so far (TR-9). It is created in item 1a.7 with **every assertion of the full TR-9 already listed**; the ones that cannot exist yet are explicit skips whose reason reads `not yet implemented (Slice N)`, and the test run prints skip reasons (`pytest -rs`). **A silent pass is never allowed**: a not-yet-possible assertion is a skip, not an empty test. Each slice turns its skips into real assertions. At 4d the smoke test has **no skips**. Every run starts the local system and makes the real warm-up call to Ollama first. The Slice 0 environment checks stay in `tests/smoke/` as separate environment tests.

| After | The smoke test covers |
|---|---|
| 0 | Environment tests only (imports and pins, Ollama warm-up, dataset integrity); the single smoke test starts at 1a |
| 1 | Real assertions: start in local mode; replay all 32 emails through the real mail provider into SQLite; replay twice gives identical rows; no duplicates by Message-ID. Skips: stages, scheduling, approval |
| 2 | Real assertions added: agents run on every email; each customer reaches its final stage (Fabrikam Converted, Northwind Not Converted, Adventure Works Engagement, Tailspin Engagement, Wingtip Presentation/Follow-up); noise and duplicate ignored; TR-8 accuracy printed |
| 3 | Real assertions added: replay leaves a **pending** request for Adventure Works (`recommend_slots`), Tailspin (`counter_propose`), Wingtip (`update_existing_meeting`) with nothing booked or sent. From 3e, approval runs through `Orchestrator.approve` (the handler itself, not a repository or provider call), and repeating it creates no duplicate. Still skipped: approval through the real endpoint |
| 4d | **Full TR-9 as written in section 13, zero skips**: part (a) replay without approval; part (b) approval through the **real approval endpoint**; repeat-approval check; no duplicates |
| 5 and later | Full TR-9 unchanged, local mode only; live providers stay disabled and are covered by contract tests (TR-7) |

## 7. Test map (where each requirement test is first written and where it must pass)

| Test | Written in | Must pass from |
|---|---|---|
| TR-1 customer matching, duplicate, noise | 2b | 2b |
| TR-1 stage after every email | 2c | 2c |
| TR-1 vague Tailspin email gets a clarification | 3c | 3c |
| TR-2 scheduling exact-match (pure code, then end to end) | 3b, 3c | 3b, 3c; post-approval part 3e |
| TR-3 gating (must pass) and advisory (never gates) | 2d (summaries), 3d (drafts) | 2d, 3d |
| TR-4 curl and scripted tests for every endpoint | 4a to 4d | 4d |
| TR-5 Playwright flows | 4e, 4f, 4g | 4g |
| TR-6 replay twice; approve twice | 1c, 2c (replay); 3f (approve) | 3f; again through the API at 4d |
| TR-7 live contract tests | 5a, 5b, 5c | 5c |
| TR-8 stage accuracy per run | 2c | every run from 2c |
| TR-9 smoke | 0, grows each slice | each slice, complete at 4d |
| TR-10 request lifecycle, **with an injected later simulated clock for expiry** | 3d | 3d |
| TR-11 approval re-check | 3f | 3f; through the API at 4d |
| TR-12 approval failure and retry | 3f | 3f; through the API at 4d |
| TR-13 API safety | 4a | 4a and every later slice |

## 8. The slices

For each slice: the goal, the sub-slices (detail in the checklist), then the **definition of done**, **tests that must pass**, **smoke test**, **commit point** and the **hld.md section 12.2 open items it settles**. "Slice-start questions" are implementation choices that `decisions.md` leaves to the slice that needs them; I propose, you decide, I record them in `decisions.md` (S6).

### Slice 0: Environment

Goal: a verified, reproducible Python 3.13 environment, a warm local model and a confirmed dataset, before any code.

- **Definition of done:** the venv is confirmed as a clean Python 3.13 venv (D10: you recreated it) and the exact six pins are really installed; `pytest` is installed at the pin you approved; `pip check` is clean; `requirements.txt` (six runtime pins), `requirements-dev.txt` (pytest) and `requirements.lock` (full freeze) exist; every package imports; `llama3.1:8b` is present and a real warm-up call works with cold and warm timings recorded; `generate.py` ran on a copy and its output matches `data/synthetic/` (calendars, config and expected files byte for byte; each `.eml` by parsed headers, bodies and attachments); you have created `.env` and the key-name check (0.14b) passed without me reading the file.
- **Failure rule:** if any pinned package fails to install **or import** on Python 3.13, I stop and ask you (S4). There is no fallback branch to another Python version.
- **Tests that must pass:** `tests/smoke/test_environment.py`, `tests/smoke/test_ollama_warmup.py`, `tests/smoke/test_dataset_integrity.py`, `tests/smoke/test_dataset_regeneration.py` (pytest; skip reasons shown with `-rs`; none of these may skip).
- **Smoke test:** the four environment files above (staging row 0). The single smoke test starts in 1a.
- **Commit point:** after all four pass: `requirements.txt`, `requirements-dev.txt`, `requirements.lock`, the four test files, `pytest.ini`, the ticked checklist. **You commit**: I show `git status` and propose a message, then wait. The documentation baseline commit and the `docs-baseline` tag are yours and come first.
- **hld.md section 12.2 items settled:** lock file and `pip check`; the Python form of the Ollama warm-up call (`hld.md` was updated to say so). Not settled here: `zoneinfo` verification (1a).

### Slice 1: Providers, local mail, SQLite

Goal: the four interfaces, config, the SQLite repository and the `.eml` mail provider, with no agents.

- **Definition of done:** the nine entities and enumerations match sections 5 and 9; config reads `example.env` keys and `config/team.json` policy with the clock override and provider precedence; four typed interfaces exist; the SQLite repository does idempotent upserts, the four named queries and audit writes; the mail provider parses all 32 emails and replays them in date order against the injected clock; a composition root builds local providers and refuses live ones without configuration; guard tests enforce R2 (no forbidden imports) and R8.
- **Tests that must pass:** unit tests for domain, config, time values (including the London-to-Chicago 6 h / 5 h case), repository (real temporary SQLite files), mail provider (real `.eml` files), the guard tests; replay-twice identical (TR-6, partial).
- **Smoke test:** staging row 1.
- **Commit points:** after each of 1a, 1b, 1c, 1d.
- **Open items settled:** Python `zoneinfo` verification (1a); the `customers_by_stage` shape (the query returns all five stage keys; the dashboard confirms in 4e); meeting and next action status values and request fields are already decided (OQ-3, OQ-17) and are just implemented.
- **Slice-start questions:** layout and packaging (src layout with `PYTHONPATH` or an install step; no new dependency); local mail outbox storage for sent drafts (1c); whether `.env` loading uses a small stdlib loader or `python-dotenv`.

### Slice 2: Ingestion and stage classifier on Ollama

Goal: replay every email through ingestion and classification and match the answer key, with summaries and the TR-3 scorer.

- **Definition of done:** the Ollama `ChatModelProvider` validates against a schema with bounded retries and a typed error; ingestion strips quoted text, ignores duplicates and noise, matches customers, creates leads, adds contacts and stores attachment metadata; the orchestrator runs the stage-1 pipeline and isolates failures; the classifier matches `expected_outcomes.json` after every email and records the TR-8 accuracy report; summaries and next actions are stored as decided (OQ-23); the TR-3 scorer (gating and advisory) exists with a stored baseline; replay twice is identical.
- **Tests that must pass:** TR-1 (customer matching, duplicate, noise, stage after every email), TR-3 gating, TR-6 replay twice, TR-8 report produced, Slice 0 and 1 tests.
- **Smoke test:** staging row 2.
- **Commit points:** after each of 2a to 2d.
- **Open items settled:** the TR-3 scorer (decided in `decisions.md`; implemented in 2d, extended to drafts in 3d); the Ollama client's structured output usage verified in 2a.
- **Slice-start questions:** how token budgets are estimated for the bounded history (calibrated against Ollama's reported token counts, 2a); the definition of "required facts" for TR-3 gating (taken from extracted facts and the CRM record, never from the answer key, 2d); whether FR-CLS-3 (no stage change on an unanswered nudge) needs a deterministic guard if the model cannot meet it (S8).

### Slice 3: Scheduler agent

Goal: all three scenarios produce the expected outcomes before and after approval, with request lifecycle and approval steps tested.

- **Definition of done:** the local `CalendarProvider` returns working hours and busy blocks, persists created events in an overlay, and **`find_events` reads attendees and event keys from the mock JSON and merges the overlay (D11, OQ-22)**; pure scheduling code converts zones correctly (DST trap), caps by working hours, applies blocking rules, ranks at most 3 slots with the fallback last and a reason for every window; the Scheduler Agent extracts windows with the model, **locates the meeting to reschedule with `find_events` (one match is the target, several are narrowed by the original meeting day, anything else is a clarification and never a duplicate; FR-SCH-9)** and chooses exactly one outcome; replay leaves exactly the three expected pending requests with nothing booked or sent; drafts show times formatted by code; supersede, cancel and expire work; the approval handler runs the four recorded steps with idempotency; re-check conflicts, step failures and repeat approvals behave as specified.
- **Tests that must pass:** TR-1 Tailspin clarification, TR-2 (pure code and end to end, before and after approval), **the reschedule lookup tests (W06 single match, several matches, no match giving a clarification and never a duplicate)**, TR-3 for drafts, **TR-10 including the injected later simulated clock for expiry**, TR-11, TR-12, TR-6 approve-twice, all earlier tests.
- **Smoke test:** staging row 3.
- **Commit points:** after each of 3a to 3f.
- **Open items settled:** `evaluated_results` per window or per slot (3b); the TR-3 scorer extended to drafts (3d).
- **Slice-start questions:** the "next Thursday" convention (3a); how sender zone candidates are validated from the `Date` offset and hints (3a); whether expiry is checked at the start of each run and before approval (3d); how a controllable real failure is injected for TR-12 without a test hook in production code (3f).

### Slice 4: CRM API, dashboard, Teams agent

Goal: the localhost-only API, the dashboard flows and the full smoke test.

- **Definition of done:** the API binds 127.0.0.1 only and applies Host, Origin, CORS, content-type and `X-CRM-Token` checks; every endpoint in `docs/api.md` works with a curl command and a scripted equivalent; approval through the endpoint honors the `Idempotency-Key` table, the `409 availability_changed` and `502 approval_step_failed` responses; the dashboard shows the pipeline, customer detail, the scheduling panel with approve/edit/reject, and the audit view; Playwright scripts pass; the full TR-9 smoke test passes; the owner has read a sample of drafts (TR-3 advisory note) before any demo; the Teams agent is either written from documentation or its deferral is agreed with you.
- **Tests that must pass:** TR-4, TR-5, TR-13, TR-6 / TR-11 / TR-12 through the API, the full smoke test, all earlier tests.
- **Smoke test:** staging row 4d (full TR-9).
- **Commit points:** after each of 4a to 4h.
- **Open items settled:** the `customers_by_stage` empty-stage question (4e); Playwright usage (4e); the taste skill review (4g); how a Teams user maps to an account owner (4h).
- **Slice-start questions:** web framework (4a); endpoint paths and payloads are a proposal in `docs/api.md` and are confirmed at 4a; the exact meaning of `stale_leads` in the API (it is a named query with no endpoint in `docs/api.md`).

### Slice 5: Live providers from documentation

Goal: live adapters written from docs, disabled by default, contract-tested, never claimed verified.

- **Definition of done:** live model adapters (Foundry first, Azure OpenAI second), live Graph mail and calendar adapters exist behind the four interfaces, refuse to start without configuration, are labeled `implemented, unverified` in `/providers`, and have contract tests (TR-7) using sample responses shaped like the documented output and labeled as contract tests; `docs/first_day_with_access.md` is complete; Phase 1 definition of done (section 10 of this plan) is checked.
- **Tests that must pass:** TR-7, plus every earlier test and the full smoke test (local mode unchanged).
- **Smoke test:** staging row 5 (full TR-9, local mode).
- **Commit points:** after each of 5a to 5d.
- **Open items settled:** none are *settled* here because live behavior cannot be verified (the Graph call for `find_events`, `calendarView`, is written from the docs read on 2026-10-16 and marked UNVERIFIED); items are written down for the first day: live CRM store (not built), the Foundry-or-Azure-OpenAI choice (both written), Graph permissions and approver (documented as to be confirmed with IT), `iCalUId` lookup, reschedule body, Sent Items ingestion.
- **Slice-start questions:** how contract tests feed sample responses to the Graph SDK and the model clients without stubbing the adapter itself (S3); how Sent Items are read.

### Slice 6: Switch to live (blocked until access exists)

- **Definition of done:** configuration selects live providers; each live provider is verified item by item against `docs/first_day_with_access.md` and the result and date recorded; contract-test sample responses corrected against real ones; D7, D8 and the Entra ID design settled with IT and recorded; the D9 outcome (revisit Agent Framework Workflows) recorded in `decisions.md`.
- **Tests that must pass:** the full local suite, then the live checks of the first-day list.
- **Smoke test:** the local smoke test, then the same flow against the live providers where IT allows.
- **Commit point:** after each verified provider.
- **Open items settled:** Entra ID design, whether the per-run token is still needed, optional health-check fallback.

## 9. `hld.md` section 12.2 open items, mapped to slices

| Item | Settled in | Note |
|---|---|---|
| `zoneinfo` usage and `tzdata` | 1a (verified), reused in 3a | |
| Ollama warm-up call form; structured output usage | 0 (warm-up form), 2a (structured output) | `hld.md` now says the same |
| Lock file and `pip check` | 0 | `hld.md` now says the same |
| TR-3 scorer | 2d (summaries), 3d (drafts) | Decided in `decisions.md`; `hld.md` marks it decided |
| Taste skill and graphify review | 4g (taste skill); graphify is a developer tool outside the slices | Reference only until you decide |
| Playwright usage | 4e | |
| `evaluated_results` per window or per slot | 3b | |
| `customers_by_stage` empty stages | 4e | query returns all five keys from 1b |
| Teams user to account owner | 4h | |
| Live CRM store | not built (D3) | deferred behind `CrmRepository` |
| Foundry or Azure OpenAI client choice | written both in 5a; chosen in 6 | depends on IT |
| Graph permissions, approver, mailbox scoping, notification URL | documented in 5d; settled in 6 | D7, D8 |
| `iCalUId` lookup, reschedule body, Sent Items, customer response status | written in 5b/5c; verified in 6 | |
| Entra ID design; per-run token still needed? | 6 | |
| Optional live-to-local health-check fallback | 6 | not planned unless you ask |

`hld.md` section 12.2 was updated on 2026-10-16 to match this table (lock file, `pip check` and the warm-up form moved to Slice 0; TR-3 scorer marked decided).

## 10. Phase 1 completion gate (requirements section 17)

| Section 17 item | Where it is met |
|---|---|
| R1 to R12 satisfied | guard tests (1a, 1d); review at 5d |
| All FR-* implemented or explicitly deferred with your agreement | FR-UI-5 (Teams) decided at 4h; others by the slices |
| Full email set replays; every customer reaches its final stage | 2c, smoke row 2 |
| SCH-ADV, SCH-TAIL, SCH-WING expected outcomes | 3c to 3f |
| Dashboard: pipeline, timelines, scheduling panel with approval, audit view | 4e to 4g |
| TR-1 to TR-13 pass; stage accuracy reported | per the test map (section 7) |
| Live providers written, disabled, labeled, contract-tested, first-day checklist | 5a to 5d |
| `example.env` present; no secrets; `.env` ignored | 0 and every commit (`git status` review) |
| Docs: HLD, LLD, demo guide | written; refreshed at 5d to match what was built |

## 11. Risks

| Risk | Why it matters | Mitigation and owner action |
|---|---|---|
| **Local model reliability** (`llama3.1:8b`, 16 GB MacBook Air) | An 8B model can return malformed JSON, misjudge stages, invent facts in drafts, ignore instructions in long contexts and run slowly (32 emails times several calls). Output at temperature 0 is not guaranteed repeatable, so exact-match tests can flake | Schema validation with bounded retries and a typed error; scheduling logic in plain code so the model only extracts and drafts (R4); short prompts and an explicit `num_ctx`; the model warm-up in every smoke run; TR-3 gating checks catch invented dates, names, numbers and companies; TR-8 accuracy reported every run; **I never loosen an exact-match test (S8)**; if accuracy is not good enough I propose prompt changes, a deterministic guard, or the `qwen3:8b` comparison (D5), and you decide. Measure replay duration in 2c and tell you early. The owner reads a sample of drafts before demos |
| **Python 3.13** (D10; the venv is 3.13.15) | The pinned packages have never been installed on 3.13 here: the 2026-10-16 dry-run resolved only metadata and ran on 3.14.4. A pinned package or one of its dependencies (for example packages with compiled parts such as `pydantic-core`, `cryptography`, `aiohttp`, `jiter`, `msgspec`, `cffi`, `regex`) may lack 3.13 wheels, need a compiler, or fail at import; the framework packages are new and may behave differently | Slice 0 really installs and imports everything and records each package's `Requires-Python`. On any failure I **stop and ask (S4)**; there is no fallback branch. Later slices re-run the Slice 0 tests, so a regression shows up immediately. Python 3.14 is not used (D10) |
| **Calendar edge cases** | The DST gap (UK ends summer time 25 Oct, the US 1 Nov: 6 h before, 5 h after) is the headline trap, but there are more: customer window starting off the 30-minute grid; windows that cross midnight or the working-hours edge; capping by each attendee's own zone; tentative versus busy versus `free` (David's lunch) versus `oof`; an unassigned member's out-of-office (Raj) that must not block; the same `iCalUId` appearing in several calendars; all-day events; dates outside the mock window (unknown, not offerable); "next Thursday" interpreted differently; ambiguous `Date` offsets mapping to several zones; the clock fixed for a run so expiry needs an injected clock | Time logic is pure code with unit tests for each case (3a, 3b) before the model is involved; IANA zones only, never fixed offsets (R9); TR-2 exact-match on all three scenarios; ambiguous zones ask the customer instead of guessing (FR-SCH-2); slice-start questions are decided and recorded before coding |
| **The localhost approval endpoint** | The Phase 1 API has no login. A web page open in the same browser, a DNS-rebinding page, or another local program could try to approve and book or send, which would break R5 | The accepted measures (`decisions.md`): bind 127.0.0.1 only, Host and Origin checks, CORS limited to `DASHBOARD_ORIGIN`, JSON content type plus `X-CRM-Token`, a random per-run token not stored in `.env`; TR-13 tests foreign Origin, missing token and wrong content type, plus extras (wrong token, `Origin: null`, wrong Host, preflight from another origin, non-loopback connection). Honest limit: other programs on the same machine can still call the API; that is why real authentication is designed for live use. Browser-behavior claims in `docs/api.md` were checked against MDN on 2026-10-16; the Host-check reasoning is unverified |
| Test gaming and R8 | A hard-to-pass test tempts special-casing client names, email IDs or dates | Guard test scans production code (1a); tests, not production code, read the answer key; I stop before touching tests or data (S2) |
| Unverified live code written without running it | Live Graph, Entra, Foundry and Azure OpenAI code cannot be run in Phase 1 | Mark `implemented, unverified`; contract tests only; re-read the docs and changelog at 5a to 5c; stop whenever a detail cannot be verified (S3); first-day checklist |
| Dependency drift | Transitive packages are not pinned by us | `requirements.lock` from Slice 0; any change to it is a reviewed diff |
| SQLite and the API | One file shared by the pipeline, calendar overlay, outbox and the API; concurrent writes | One writer at a time (a single run, OQ-14); transactions per step; decided and tested at 1b and 4c |
| Scope creep (Teams agent, graphify, taste skill) | They have no unverified-free route in Phase 1 | Teams agent is last in Slice 4 and its deferral is a decision for you (4h); taste skill and graphify are reference only until you decide |
| Uncommitted work piling up between commits | `plans/` and recent `decisions.md` edits are not in git; you make all commits | Every sub-slice has a commit point; at each I show `git status` and a proposed message and wait; you tag `docs-baseline` before Slice 0 |

## 12. What is deliberately not in this plan

- No application code and no installs have been done; this is a plan.
- No design choices beyond `decisions.md`: where `decisions.md` is silent the plan lists a slice-start question and waits for you.
- The live CRM store (D3), hosting (D8) and the Graph permission set (D7) stay deferred.
