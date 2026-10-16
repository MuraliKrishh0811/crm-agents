# Step-by-step implementation checklist

Status: **revised 2026-10-16 with your seven decisions (see `inputs/decisions.md`), then with the `REQUIREMENTS.md` R7 amendment (the `ENV LOADER`, now part of R7) and OQ-34 to OQ-38; nothing below has been started.** Companion: [Overall_Implementation_plan.md](Overall_Implementation_plan.md) (rationale, risks, dependency register, smoke staging, test map).

## How to read this file

- Items are numbered by sub-slice (`0.1`, `1a.2`, ...). Tick `[x]` only when the item's **Accept** check passes; write the result or date beside it.
- Every item has **IDs** (FR-, TR-, R-, D-, OQ- as relevant), **Files** it touches, and **Accept**, a check someone else can run.
- **STOP AND ASK** marks a gate: I stop and wait for your answer. The standing triggers are S1 (new dependency not in `references.md`, or an approved-in-principle one that has not yet been pinned), S2 (changing a test or the dataset), S3 (anything unverified), S4 (a pinned package fails on Python 3.13; no fallback branch), S5 (commit points: you commit, I show `git status` and propose a message), S6 (decisions left to the slice), S7 (pulling another model), S8 (model-dependent exact-match failure: report, never loosen), S9 (anything outside the repo). They are defined in the overall plan, section 4.
- File paths follow the layout below. **The layout is a proposal for you to confirm at item 1a.1**; tests live only under `tests/` (`agents`, `backend`, `frontend`, `smoke`). Python tests use **pytest** (approved; pinned as 9.1.1, test-only, in `references.md`). Run: `.venv/bin/python -m pytest -rs` so skip reasons are always printed. Environment: Python 3.13 (D10).
- **Smoke test rule (decisions.md):** from Slice 1 on, "the smoke test" means `tests/smoke/test_smoke.py`, the single smoke test covering everything built so far. Assertions that cannot exist yet are **explicit skips** with the reason `not yet implemented (Slice N)`, shown in the output; **never a silent pass**. It has zero skips at 4d.
- **Commit points:** **you make all commits.** At every commit-point item I show `git status`, propose a message that cites the requirement IDs, and wait. I never commit.
- **`.env` (R7 as now written):** I never open, print, search or copy any `.env*` file myself. The application's own settings loader may read `.env` when tests or smoke runs execute (Phase 1 only, while `.env` holds no real secrets). The loader, logs and settings objects print key names and set or blank status, never values. Slice 0 is unchanged: you run the key-name check (0.14b) and paste its output. Pure config unit tests (1a.4) may still use explicit dictionaries.
- Live Graph, Entra ID, Azure OpenAI and Foundry behavior is UNVERIFIED everywhere in this file until Slice 6.

Proposed layout (confirmed at 1a.1):

```
src/crm_agents/
  domain/        enums.py entities.py timevalues.py errors.py
  config/        settings.py policy.py
  providers/
    interfaces/  mail.py calendar.py chat_model.py repository.py
    local/       eml_mail.py mock_calendar.py ollama_model.py sqlite_repository.py
    live/        graph_mail.py graph_calendar.py foundry_model.py azure_openai_model.py
  scheduling/    zones.py windows.py availability.py ranking.py outcomes.py
  agents/        ingestion.py classifier.py summary.py scheduler.py crm_writer.py
  orchestrator/  interface.py pipeline.py approval.py
  audit/         recorder.py
  api/           app.py safety.py routes_*.py
  app/           composition.py logging.py
frontend/        (Vite + React + TypeScript app, Slice 4e)
tests/           agents/ backend/ frontend/ smoke/   (+ tests/agents/rubrics; tests/baselines/ only when you decide, OQ-35)
reports/         (git-ignored: TR-8 accuracy, TR-3 scores, draft samples; OQ-35)
plans/  docs/  requirements.txt  requirements.lock
```

---

## Slice 0: Environment

- [ ] **0.1 Record the baseline (read-only)**
  - IDs: R12, requirements section 0 item 5, D1, D5
  - Files: none (record results beside this item)
  - Accept: results written here for: `.venv/bin/python --version` (expected 3.13.x; observed 3.13.15 on 2026-10-16), `.venv/bin/python -m pip list` (expected only `pip`: a clean venv), the interpreter path behind the venv (`sys.executable` and `sys.base_prefix`, so it is clear which 3.13 install it uses), `node --version`, `npm --version`, `ollama --version` and `ollama list`. Result: ______

- [ ] **0.2 STOP AND ASK: approvals before anything is installed**
  - IDs: S1, S5, `CLAUDE.md` plan-first rule
  - Files: none
  - Accept: (1) `inputs/references.md` lists `pytest 9.1.1` as test-only (done by you; I only check the file). (2) D10 and D11 are in `decisions.md` (done). (3) `git tag` lists `docs-baseline` (it exists on commit `6411d11`, checked 2026-10-16; I only check, read-only). (4) You acknowledge that the edits made after that commit (the `REQUIREMENTS.md` R7 amendment, `CLAUDE.md`, `decisions.md` OQ-34 to OQ-38, `plans/`, `prompts/`, `tools/`, the skills and docs) are uncommitted until your next commit; the `docs-baseline` tag does not include them. Answers recorded here: ______ .

- [ ] **0.3 Confirm Python 3.13 (D10) and the failure rule**
  - IDs: D1, D10, R12
  - Files: none
  - Accept: the venv is Python 3.13.x and clean (from 0.1). There is **no 3.14 branch and no switch to another version**: **if any pinned package fails to install or import on 3.13, I stop, report the exact error and ask (S4).** I never delete or recreate the venv.

- [ ] **0.4 Create `requirements.txt` and really install the exact pinned set**
  - IDs: R3 (live packages installed but disabled), `references.md` install note, D1
  - Files: `requirements.txt` (six runtime lines: `agent-framework-core==1.22.0`, `agent-framework-foundry==1.15.0`, `agent-framework-openai==1.17.0`, `azure-identity==1.26.0`, `ollama==0.6.3`, `msgraph-sdk==1.64.0`); `requirements-dev.txt` (`pytest==9.1.1`, already in `references.md`)
  - Accept: `.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt` exits 0 on Python 3.13; `.venv/bin/python -m pip show agent-framework agent-framework-ollama` reports both **not found** (meta-package and beta Ollama package absent). `.venv/bin/python -m pytest --version` prints the pinned version. On any failure: copy the exact error, **STOP AND ASK (S4)**. Result: ______

- [ ] **0.5 `pip check`**
  - IDs: R11
  - Files: none
  - Accept: `.venv/bin/python -m pip check` prints "No broken requirements found" and exits 0. Otherwise STOP AND ASK.

- [ ] **0.6 Record each package's `Requires-Python` and installed version**
  - IDs: R12, S3
  - Files: none (record here)
  - Accept: for each of the six pins and for `pydantic`, `httpx`, `python-dotenv`, the installed version (from `importlib.metadata`) and its `Requires-Python` are written here, and none excludes 3.13 (and `pytest`'s own metadata is recorded too). Anything that does: STOP AND ASK. Result: ______

- [ ] **0.7 Lock file**
  - IDs: R11, plan risk "dependency drift"
  - Files: `requirements.lock` (output of `.venv/bin/python -m pip freeze`, with a first comment line giving Python 3.13.x, pip version and date; it includes pytest and its dependencies)
  - Accept: the lock file contains the six direct pins and the pytest pin at their exact versions plus transitive packages; `.venv/bin/python -m pip install --dry-run -r requirements.lock` exits 0 and reports everything already satisfied. No hashes (hash locking needs pip-tools, not in `references.md`; S1).

- [ ] **0.8 Import test of every package**
  - IDs: R3, R11, TR-9 (environment part)
  - Files: `tests/smoke/test_environment.py`
  - Accept: the test passes on Python 3.13 (it fails if the interpreter is not 3.13, per D10). It imports `agent_framework.Agent`, `agent_framework.foundry.FoundryChatClient`, `agent_framework.openai.OpenAIChatClient`, `azure.identity` (`AzureCliCredential`), `ollama` (`Client`, `chat`), `msgraph` (`GraphServiceClient`) (import lines are the ones in the skills' docs-verified snippets); asserts each installed version equals the pin in `references.md`; asserts `agent_framework.ollama` is **not** importable. Import only: no client is created, no network, no credentials (R3). If an import name differs from the snippet, check the official docs (S3) before changing the test.

- [ ] **0.9 Ollama model present**
  - IDs: D5
  - Files: none
  - Accept: `ollama list` shows `llama3.1:8b` (it did on 2026-10-16, 4.9 GB). Only if it is missing: `ollama pull llama3.1:8b` (your Slice 0 instruction covers this one model; any other model is S7).

- [ ] **0.10 Warm-up test against the real model**
  - IDs: D5, R1, R11, TR-9 (warm-up), S3 (closes the skill's TODO on the Python warm-up form)
  - Files: `tests/smoke/test_ollama_warmup.py`
  - Accept: before writing it I read the `ollama-python` README at tag 0.6.3 and the Ollama docs for the base URL and for `keep_alive` / preload (S3), and note the URLs and dates here. The test then: (1) preloads the model with the documented Python form (record whether an empty-`messages` `chat(model, keep_alive=...)` works; if not, record the working form), (2) makes a real `chat` call with an explicit `num_ctx`, `keep_alive` and temperature 0, requesting JSON through `format=`, (3) asserts the reply parses as JSON, (4) asserts `ollama ps` (or the documented equivalent) lists the model as loaded. Non-secret values (`http://localhost:11434` once verified, `llama3.1:8b`) are passed inline. **Cold-start and warm-call durations are written here**: ______ . If only memory supports a call form, STOP AND ASK.

- [ ] **0.11 Run `generate.py` on a copy and confirm it passes**
  - IDs: section 10 (dataset), R8, S2
  - Files: `tests/smoke/test_dataset_integrity.py` (read-only checks); `tests/smoke/test_dataset_regeneration.py` (runs a copy of the generator in a pytest temporary directory and compares); the run writes nothing under `data/`
  - Accept: (your decision 6) `generate.py` alone is copied into an **empty** temporary directory (so every output is freshly written, none inherited) and run with `.venv/bin/python`; it exits 0 (its assertions are the validation). Then the output is compared with `data/synthetic`: **`calendars/mock_calendars.json`, `config/team.json` and `expected/expected_outcomes.json` byte for byte** (`cmp`); the **32 `.eml` files by parsed content, not raw bytes**, because Python's email library picks random multipart boundaries: same file names; same headers (the `boundary` parameter of `Content-Type` excluded); same structure of parts with equal content types and charsets; equal decoded body text; equal attachment file names and attachment bytes. `git status data/` is clean afterwards. `test_dataset_integrity.py` (read-only) asserts 32 `.eml` files in six folders, four calendar users with `workingHours`, F08 and F08b share one Message-ID, exactly one attachment, `config/team.json` has no working-hours values. **Any difference beyond multipart boundaries, or a script failure: STOP AND ASK (S2); the dataset is never edited.** Running `generate.py` in place is not planned (it rewrites the dataset files).

- [ ] **0.12 Toolchain facts for Slice 4 (no install)**
  - IDs: S1
  - Files: none
  - Accept: Node and npm versions recorded; confirmation that no frontend packages are installed; list of frontend and test dependencies that will need approval (React, Vite, TypeScript, Playwright) acknowledged.

- [ ] **0.13 Repository hygiene**
  - IDs: R7, section 14
  - Files: none (verify `.gitignore`, `.claude/settings.json`, `example.env`)
  - Accept: `git check-ignore .env .venv reports/` lists all three (`reports/` is git-ignored, OQ-35); `git ls-files example.env` lists it; `.claude/settings.json` still denies `Read(./.env)`, `Read(./.env.*)`, `*.pem`, `*.key`; `example.env` contains `APPROVER_USER`, `API_PORT`, `DASHBOARD_ORIGIN`, `STALE_LEAD_DAYS`.

- [ ] **0.14 STOP AND ASK: your `.env` (you created it; I do not read it)**
  - IDs: R7, D5, FR-CFG-1
  - Files: your `.env` (yours; I never open it); `example.env` (readable, already holds starting values and comments)
  - Accept: you confirm that `.env` exists and holds non-secret values. `example.env` already has starting values for the local keys (`OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=llama3.1:8b`, `OLLAMA_NUM_CTX=4096`, `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_TEMPERATURE=0`, `OLLAMA_MAX_RETRIES=2`, `OLLAMA_REQUEST_TIMEOUT_S=120`, `APPROVER_USER=local-user`, `API_PORT=8000`, `DASHBOARD_ORIGIN=http://localhost:5173`, `STALE_LEAD_DAYS=14`, the simulated clock) and blank values for the live keys and `DATABASE_URL`; after the 0.10 measurements I say whether the Ollama values look right. I confirm only that you did it, never the contents.

- [ ] **0.14b Confirm configuration key names without me reading `.env` (you run the check)**
  - IDs: R7, FR-CFG-1, `crm-security-env` skill, `decisions.md` (`.env` key-name check)
  - Files: `tests/smoke/check_env_keys.py` (a small checker I write but **never run**; not application code)
  - Accept: **you run the checker yourself** and paste its output. It compares the **key names** in `.env` with the key names in `example.env` and prints **only** names (missing, unknown) and, per key, whether it is set or blank, **never a value**. In Slice 0 I never open `.env` and never run any command that reads it (no `cat`, `grep`, `source`, `python` on it, and not this checker). From 1a, R7 lets tests and smoke runs that I execute use the application's own loader; that loader does not exist until 1a.4, and the real "the app loads configuration from the environment" confirmation is item 1a.4b, which prints key names only. Result you pasted: ______

- [ ] **0.15 Slice 0 environment tests and commit point**
  - IDs: R11, TR-9
  - Files: `requirements.txt`, `requirements-dev.txt`, `requirements.lock`, `tests/smoke/test_environment.py`, `tests/smoke/test_ollama_warmup.py`, `tests/smoke/test_dataset_integrity.py`, `tests/smoke/test_dataset_regeneration.py`, `tests/smoke/check_env_keys.py`, `pytest.ini` (created now with minimal content, for example `testpaths` and `-rs`; 1a.1 may amend it), this checklist with results ticked
  - Accept: `.venv/bin/python -m pytest -rs tests/smoke` passes with no skips; `git status` shows no `.env*` and no `.venv`; show `git status` and propose a commit message citing R11, D10; **you commit** (S5).

**Slice 0 definition of done:** exact pins and pytest installed and importing on Python 3.13; `pip check` clean; lock file present; warm model proven with timings; dataset generation confirmed identical; `.env` created by you.
**Tests that must pass:** the four files in `tests/smoke/` above (none may skip).
**Smoke test:** the same environment files (staging row 0); the single smoke test starts in 1a.7.
**Commit point:** after 0.15.
**hld.md section 12.2 items settled:** lock file and `pip check`; the Python form of the Ollama warm-up call.

---

## Slice 1: Providers, local mail, SQLite

### 1a Domain, config, interfaces (pure code, no I/O)

- [ ] **1a.1 STOP AND ASK: Slice 1 design gate**
  - IDs: S1, S6, lld section 1
  - Files: none
  - Accept: you confirm (or change) the layout above, packaging (src layout with pytest's `pythonpath` setting added to the minimal `pytest.ini` from Slice 0, no new dependency), how `.env` is loaded by the application (stdlib loader, or `python-dotenv` which is only a transitive package today and would need your approval), and whether real environment variables override `.env` values (proposal: yes, so the process environment wins). **Not asked here:** R7 already allows tests and smoke runs that I execute to use the application's loader on `.env` while it holds no real secrets; the loader, logs and settings objects print key names and set or blank status only. pytest is already approved (`decisions.md`) and pinned at 0.2; pydantic is approved in principle and is pinned at 2a.1, so Slice 1 domain objects use the standard library (dataclasses and enums) unless you say otherwise. Each answer that is a decision is recorded in `inputs/decisions.md`.

- [ ] **1a.2 Enumerations and the nine entities**
  - IDs: requirements sections 5 and 9, FR-SCH-7, FR-SCH-12, OQ-3, OQ-17, OQ-27
  - Files: `src/crm_agents/domain/enums.py`, `entities.py`, `errors.py`; `tests/agents/test_domain.py`
  - Accept: tests assert the exact values: stages (five), outcomes (four), request states (seven), decision (`approve`, `reject`), approval progress (four), engagement types, `showAs` (five), direction, meeting status (`scheduled`, `rescheduled`, `cancelled`), next action status (`open`, `done`, `dismissed`); `SchedulingRequest` has draft reply, `decided_by`, `decided_at`, approval progress, fresh options, state reason and `superseded_by`; `StageHistory.source` accepts an email or an approval.

- [ ] **1a.3 `TimeInZone` value type (UTC plus IANA zone)**
  - IDs: R9, FR-SCH-2, S3
  - Files: `src/crm_agents/domain/timevalues.py`; `tests/agents/test_timevalues.py`
  - Accept: before writing, Python `zoneinfo` docs are read (and the need for `tzdata` checked) and recorded (S3, closes the skill TODO). Tests: a value built from UTC plus `Europe/London` converts to `America/Chicago` with a **6 h** difference on 2026-10-20 and **5 h** on 2026-10-27; a fixed offset such as `+01:00` is rejected as a zone; naive datetimes are rejected.

- [ ] **1a.4 Configuration loader**
  - IDs: FR-CFG-1, R3, R7, OQ-5, OQ-6, OQ-21, section 8, section 14
  - Files: `src/crm_agents/config/settings.py`, `policy.py`; `tests/agents/test_config.py`
  - Accept: tests (using explicit dictionaries, not `.env`) show: every `example.env` key is known to the loader; `SIMULATED_NOW` plus `SIMULATED_TZ` override `organization.simulationNow` in `team.json`; `PROVIDER_MODE` sets all four providers and a non-empty per-provider key overrides it; a missing required value raises an error that names the key and never prints a value; live providers refuse to start without configuration; the real `data/synthetic/config/team.json` parses into durations, granularity, blocking lists, `maxSuggestions`, `requireHumanApproval`, and holds **no** working hours.

- [ ] **1a.4b Real-environment check with the application's own loader**
  - IDs: FR-CFG-1, R7, `crm-security-env` skill
  - Files: `tests/agents/test_config_real_env.py`
  - Accept: the real loader (not a dictionary) reads the process environment and `.env` the way the application will, and the test asserts that every required local key is present and valid (`PROVIDER_MODE`, `OLLAMA_*`, `SIMULATED_NOW`, `SIMULATED_TZ`, `API_PORT`, `APPROVER_USER`, `DASHBOARD_ORIGIN`, `STALE_LEAD_DAYS`, `DATA_DIR`). Failure messages name keys only; no value is printed, logged or put in an assertion message; the test does not skip silently. I may run it (R7): the loader opens `.env`, I never open, print or search it, and I see only pass or fail with key names and set or blank status, so this confirms the app loads its configuration **without me reading the file**. Settings objects redact values in their string form (test this).

- [ ] **1a.5 The four provider interfaces**
  - IDs: R2, requirements section 6, OQ-28, FR-AUD-1
  - Files: `src/crm_agents/providers/interfaces/mail.py`, `calendar.py`, `chat_model.py`, `repository.py`; `tests/agents/test_interfaces.py`
  - Accept: exactly four interfaces with the section 6 signatures (`get_availability` returns per user `working_hours` and `busy_blocks`; `stale_leads(days)`); typed errors exist; a conformance test fails if an operation is missing.

- [ ] **1a.6 Guard tests for R2 and R8**
  - IDs: R2, R8
  - Files: `tests/agents/test_guards.py`
  - Accept: tests scan production code and fail if `agents`, `scheduling`, `orchestrator` or `api` import `providers.local`, `providers.live`, Graph, Azure, Ollama, Agent Framework or a database driver; fail if any production file mentions `expected_outcomes`, a dataset client name, or an email ID; fail if any agent module calls `send_draft`, `create_event` or `update_event` (OQ-2). The scan runs now (nothing violates it yet) and every later slice.

- [ ] **1a.7 Create the single smoke test with explicit skips**
  - IDs: TR-9, R11, `decisions.md` (staged smoke test)
  - Files: `tests/smoke/test_smoke.py`, `tests/smoke/conftest.py` (a helper such as `not_yet_implemented(slice)` that raises `pytest.skip("not yet implemented (Slice N)")`)
  - Accept: the file lists **every assertion of the full TR-9** (warm-up; start in local mode; replay all emails; each customer's final stage; the three pending requests with expected outcomes; nothing booked or sent before approval; approval through the real endpoint; repeat approval; no duplicates). Those that cannot exist yet are skips through the helper, each naming its slice. `pytest -rs tests/smoke/test_smoke.py` prints every skip reason; a guard test fails if the smoke file contains an empty test body or a `pass`-only test (no silent passes). Passing assertions now: the Ollama warm-up reuse from 0.10 only.

- [ ] **1a.8 Commit point (1a)**
  - IDs: R11
  - Files: the files above
  - Accept: all unit tests pass; Slice 0 environment tests still pass; `pytest -rs tests/smoke` shows only explicit "not yet implemented" skips; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 1a definition of done:** domain, time value, config and interfaces implemented and tested; guards active.
**Tests that must pass:** 1a tests plus the Slice 0 environment tests (the four files in `tests/smoke/`).
**Smoke test:** the single smoke test exists with explicit skips (staging row 1 starts to fill in at 1c and 1d).
**hld.md section 12.2 items settled:** `zoneinfo` verification.

### 1b SQLite `CrmRepository`

- [ ] **1b.1 Schema creation**
  - IDs: FR-CRM-1, R6, section 9, OQ-1
  - Files: `src/crm_agents/providers/local/sqlite_repository.py` (schema inside); `tests/agents/test_repository_schema.py`
  - Accept: creating the schema twice on a real temporary SQLite file is safe; unique keys exist for email Message-ID, contact (customer, email), meeting event key, and scheduling request (trigger email, outcome); audit tables are separate tables in the same database. **STOP AND ASK:** I propose a `DATABASE_URL` form (a path under a git-ignored location, since `*.db` is already ignored) for you to put in `.env` and `example.env`; the key is blank in `example.env` today.

- [ ] **1b.2 Idempotent upserts for every entity**
  - IDs: FR-CRM-1, R6, R9, section 9
  - Files: same repository file; `tests/agents/test_repository_upserts.py`
  - Accept: writing each entity twice leaves one row; round trips preserve every field, including `TimeInZone` (UTC plus zone) and all `SchedulingRequest` fields (draft, state, decision, `decided_by`, `decided_at`, approval progress, fresh options, state reason, `superseded_by`).

- [ ] **1b.3 Named queries**
  - IDs: section 6 queries, OQ-12, FR-UI-1, FR-UI-2, FR-UI-5
  - Files: same; `tests/agents/test_repository_queries.py`
  - Accept: `customers_by_stage` returns all five stage keys (empty lists allowed); `stale_leads(days)` uses the configured default (`STALE_LEAD_DAYS`, 14); `next_actions_due(range)` is inclusive on both ends and returns only `open` actions (tests on the boundary days); `customer_timeline` returns emails and meetings in time order.

- [ ] **1b.4 Keyed lookups the pipeline needs**
  - IDs: FR-ING-3, FR-ING-5, FR-CLS-1, FR-SCH-12
  - Files: same; `tests/agents/test_repository_lookups.py`
  - Accept: lookups work for customer by domain and by contact email, email by Message-ID, thread lookups by In-Reply-To and References, scheduling requests by state, customer and thread, meeting by event key, audit entries by run, agent and customer, and the most recent engagement entries newest first with a limit.

- [ ] **1b.5 Audit write path through the repository**
  - IDs: FR-AUD-1, OQ-1, OQ-27
  - Files: same; `src/crm_agents/audit/recorder.py`; `tests/agents/test_audit.py`
  - Accept: an `AgentRun` (agent, input reference, output, provider, model, timestamp, duration, approval decision) is written and read back; an entry whose input reference is a scheduling request id is returned by "entries for this request" (approval step records, OQ-27).

- [ ] **1b.6 Commit point (1b)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: the above
  - Accept: tests pass on real temporary SQLite files (no mocks, R1); earlier tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 1b definition of done:** the repository covers all entities, queries, lookups and audit writes idempotently.
**Tests that must pass:** 1b tests, 1a tests, the Slice 0 environment tests.
**Smoke test:** Slice 0 files plus the repository tests.
**hld.md section 12.2 items settled:** none; the `customers_by_stage` shape is set here and confirmed in 4e.

### 1c Local `MailProvider`

- [ ] **1c.1 `.eml` parsing into the normalized `Email`**
  - IDs: FR-ING-1, FR-ING-9, section 11, R6
  - Files: `src/crm_agents/providers/local/eml_mail.py`; `tests/agents/test_eml_mail.py`
  - Accept: all 32 files in `data/synthetic/emails/**` parse with the standard library; each result has Message-ID, In-Reply-To, References, `Date` with offset converted to UTC, From, To, Cc, plain and HTML bodies and attachment name and metadata; F08 and F08b have the same Message-ID; exactly one email has an attachment; replies have In-Reply-To pointing at an existing Message-ID in the same folder. Data is opened read-only.

- [ ] **1c.2 Replay in date order against the injected clock**
  - IDs: section 11, OQ-5, OQ-24
  - Files: same; `tests/agents/test_eml_replay.py`
  - Accept: `list_new_messages(since)` returns messages in UTC order; with the clock at `2026-10-16T10:00:00 America/Chicago` it returns all 32; with an injected earlier clock it returns only the earlier ones (the test injects the clock; production reads it from config); `get_message(id)` returns the same object. "Now" is never read from the system clock.

- [ ] **1c.3 STOP AND ASK: local outbox for drafts and sent mail**
  - IDs: FR-APP-2, OQ-25, R5, R6, S6
  - Files: decision recorded in `inputs/decisions.md`
  - Accept: you decide where `create_reply_draft` and `send_draft` record drafts and sent mail locally. Proposal: provider-owned tables in the same SQLite file, keyed by a Message-ID derived from the scheduling request id, so a repeat send is a no-op.

- [ ] **1c.4 `create_reply_draft` and `send_draft` (local)**
  - IDs: FR-APP-2, OQ-25, R5, R6, R10
  - Files: `eml_mail.py` (or an outbox module next to it); `tests/agents/test_mail_outbox.py`
  - Accept: creating a draft stores it without sending; sending marks it sent exactly once; sending twice does not duplicate; the sent message is retrievable and carries the thread identifiers of the reply target. (Nothing in the pipeline calls these before approval; only the approval handler will, 3e.)

- [ ] **1c.5 Replay-twice into the repository (TR-6, partial)**
  - IDs: TR-6, R6
  - Files: `tests/agents/test_replay_twice.py`
  - Accept: replaying all emails twice through the real provider into the repository's email table yields identical rows; there are 31 unique Message-IDs for 32 files (F08b is the duplicate); no agents are involved yet.

- [ ] **1c.6 Commit point (1c)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; earlier tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 1c definition of done:** all 32 emails parse and replay in order; a local outbox exists; replay twice is identical.
**Tests that must pass:** 1c tests, earlier tests.
**Smoke test:** staging row 1 partial (replay into SQLite, twice).
**hld.md section 12.2 items settled:** none.

### 1d Composition root, logging, Slice 1 smoke assertions

- [ ] **1d.1 Composition root**
  - IDs: FR-CFG-1, R3, OQ-21, section 6 ("record the active provider")
  - Files: `src/crm_agents/app/composition.py`; `tests/agents/test_composition.py`
  - Accept: local mode builds the local mail provider and repository from configuration; asking for any live provider without configuration fails with a clear error; the active provider labels (`local-eml`, `sqlite`, and so on) are available for later `/providers` and the audit log.

- [ ] **1d.2 Structured logging with a run ID, redaction**
  - IDs: section 14 (Observability), R7
  - Files: `src/crm_agents/app/logging.py`; `tests/agents/test_logging.py`
  - Accept: log lines are structured (key/value or JSON) and carry a run ID; a test writes a message body and a secret-looking value and asserts neither appears in the output (IDs and hashes only).

- [ ] **1d.3 Smoke test: Slice 1 assertions become real**
  - IDs: TR-9, R11, D5
  - Files: `tests/smoke/test_smoke.py`
  - Accept: the "start the local system through the composition root" assertion, the Ollama warm-up call first (re-using 0.10, failing fast with a clear message if Ollama is down or the model is missing) and the replay assertions (all emails replayed into SQLite twice, identical state, no duplicate Message-IDs) are now real; stage, scheduling and approval assertions remain explicit "not yet implemented (Slice N)" skips, visible with `-rs`.

- [ ] **1d.4 Slice 1 close**
  - IDs: R2, R3, R8, R11
  - Files: none new
  - Accept: guard tests (1a.6) pass against all Slice 1 code; `git status` clean of `.env*`; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 1 (overall) definition of done:** see the overall plan, section 8.
**Tests that must pass:** everything in 1a to 1d and Slice 0.
**Smoke test:** `tests/smoke/test_smoke.py` with Slice 1 assertions real and the rest explicit skips.
**Commit point:** after 1d.4.
**hld.md section 12.2 items settled:** see 1a and 1b.

---

## Slice 2: Ingestion and stage classifier on Ollama

### 2a Ollama `ChatModelProvider` and audit

- [ ] **2a.1 STOP AND ASK: pin pydantic (approved in principle)**
  - IDs: S1, S3, `decisions.md` (dependency approvals)
  - Files: `inputs/references.md` (pin line)
  - Accept: I propose the exact `pydantic` version and its release date from PyPI (and confirm it equals the version `ollama` 0.6.3 already installed, or say what differs); you spot-check; only then it goes into `references.md` and our code imports it directly. Model-output validation and the Ollama `format=` schema use it.

- [ ] **2a.2 `complete(messages, output_schema)` on Ollama**
  - IDs: R1, R4, section 11, D5, S3
  - Files: `src/crm_agents/providers/local/ollama_model.py`; `tests/agents/test_ollama_model.py`
  - Accept: the Ollama structured-output usage is re-read in the 0.6.3 README and noted (S3). Against the real model: a small schema returns a validated result; explicit `num_ctx` and `keep_alive` come from config; temperature is 0; the result reports provider and model for the audit. The model never does time zone conversion or slot choice (R4).

- [ ] **2a.3 Bounded retries and a typed error**
  - IDs: section 11, section 14 (Reliability), R1
  - Files: same; `tests/agents/test_ollama_retry.py`
  - Accept: with a real, controllable condition (for example a very small `num_predict` that truncates the JSON), the provider retries within `OLLAMA_MAX_RETRIES`, then raises the typed error and never returns unvalidated text; the retry count is visible in the audit entry.

- [ ] **2a.4 Warm-up at start and fail-fast**
  - IDs: D5, TR-9
  - Files: same; `tests/agents/test_ollama_startup.py`
  - Accept: with `OLLAMA_WARMUP_ON_START=true` the provider preloads the model; pointing it at an unused local port produces a clear "Ollama not reachable" error; asking for a model that is not pulled produces a clear "model not pulled" error (real conditions, no mocks).

- [ ] **2a.5 Bounded history for the classifier input**
  - IDs: FR-CLS-1, OQ-19, S6
  - Files: `src/crm_agents/agents/context.py`; `tests/agents/test_context_budget.py`
  - Accept: a pure function builds the history from the most recent engagement entries, newest first, within a token budget derived from `OLLAMA_NUM_CTX`; it never exceeds the budget and logs how many entries were kept and dropped. The slice-start question (S6) is answered first: how tokens are estimated; the estimate is checked against the token counts Ollama reports for a real call and the result is recorded in `decisions.md`.

- [ ] **2a.6 Audit around model calls**
  - IDs: FR-AUD-1, OQ-1
  - Files: `src/crm_agents/audit/recorder.py`; `tests/agents/test_audit_model_calls.py`
  - Accept: each model call writes an `AgentRun` with agent, input reference, output, provider, model, timestamp, duration through `CrmRepository`.

- [ ] **2a.7 Commit point (2a)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass with the real model running; earlier tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 2a definition of done:** the Ollama provider validates, retries within a bound, fails clearly and is audited.
**Tests that must pass:** 2a tests, Slices 0 and 1.
**Smoke test:** the single smoke test; the warm-up assertion now exercises the provider; stage, scheduling and approval stay explicit skips.
**hld.md section 12.2 items settled:** structured-output usage of the Ollama client verified.

### 2b Ingestion Agent and CRM Writer (no model needed)

- [ ] **2b.1 Strip quoted earlier messages**
  - IDs: FR-ING-2, S2
  - Files: `src/crm_agents/agents/ingestion.py` (quote stripping); `tests/agents/test_quote_stripping.py`
  - Accept: for every reply email, the new body excludes distinctive text from earlier messages in its thread (the test finds those phrases from the thread, not from hardcoded lists) and keeps the sender's new text; Outlook-style headers, "wrote:" lines and `>` quoting are handled; HTML-only bodies are converted with the standard library `html.parser` (STOP AND ASK before adding `beautifulsoup4`, S1).

- [ ] **2b.2 Duplicates and noise**
  - IDs: FR-ING-5, FR-ING-6, TR-1, R8
  - Files: `ingestion.py`; `tests/agents/test_ingestion_dedupe_noise.py`
  - Accept: F08b creates no second record; the HR all-staff email creates no customer, contact or engagement record; the noise rule is general (an internal sender with no customer party and no thread match), with no mention of the HR email, its sender or its ID (the guard test passes); an internal email inside a customer thread is not treated as noise (test built from real emails).

- [ ] **2b.3 Customer matching and new leads**
  - IDs: FR-ING-3, FR-ING-4, TR-1
  - Files: `ingestion.py`; `tests/agents/test_customer_matching.py`
  - Accept: by sender address, sender domain, CC contacts and thread identifiers; emails with a new subject (for example F05, N04, W03) link to the existing customer; for every email the customer equals the folder it came from (test oracle only, R8); an unmatched sender creates a new lead.

- [ ] **2b.4 Contacts, attachments, direction, engagement entries**
  - IDs: FR-ING-7, FR-ING-8, FR-ING-9, FR-CRM-1
  - Files: `ingestion.py`; `tests/agents/test_ingestion_records.py`
  - Accept: Sophie Turner (Adventure Works) and Lisa Park (Wingtip) are added as contacts of the right customers; the one attachment's name and metadata are stored; received and sent mail are marked by direction (internal sender means sent) and both create engagement entries of type email.

- [ ] **2b.5 CRM Writer as the only domain writer**
  - IDs: FR-CRM-1, R2, OQ-1
  - Files: `src/crm_agents/agents/crm_writer.py`; `tests/agents/test_crm_writer.py`
  - Accept: agents return results and the CRM Writer persists them; an architecture test fails if another agent writes domain records directly.

- [ ] **2b.6 Replay twice with ingestion (TR-6)**
  - IDs: TR-6, TR-1
  - Files: `tests/agents/test_ingestion_replay_twice.py`
  - Accept: replaying all emails twice through ingestion gives identical CRM state; one contact each for Sophie and Lisa; no second F08 record.

- [ ] **2b.7 Commit point (2b)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; if a test cannot pass without changing the data or the test, **STOP AND ASK (S2)**; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 2b definition of done:** ingestion and the CRM Writer behave per FR-ING-1 to 9 on the real dataset.
**Tests that must pass:** 2b tests, earlier tests.
**Smoke test:** the single smoke test, with ingestion run during replay; stage, scheduling and approval stay explicit skips.
**hld.md section 12.2 items settled:** none.

### 2c Orchestrator (stage 1) and Stage Classifier

- [ ] **2c.1 Orchestrator interface and plain Python pipeline**
  - IDs: D9, section 14 (Reliability), FR-AUD-1
  - Files: `src/crm_agents/orchestrator/interface.py`, `pipeline.py`; `tests/agents/test_orchestrator.py`
  - Accept: `run(scope)`, `process_message`, `get_run` exist behind an interface; each run has a run ID; messages are processed sequentially in date order; **a failing message is recorded in the audit log and the run continues**, shown by a test with a real malformed `.eml` placed in a temporary mail folder (never in the dataset).

- [ ] **2c.2 Stage Classifier agent**
  - IDs: FR-CLS-1, FR-CLS-2, FR-CLS-3, OQ-19, R4
  - Files: `src/crm_agents/agents/classifier.py`; `tests/agents/test_classifier_schema.py`
  - Accept: input is the new text, current stage, running summary and recent engagement entries within the budget (2a.5); output is schema-validated (proposed stage, confidence, short reason, extracted facts such as user count, current CRM, decision timeline, loss reason); stage names come from the enumeration only.

- [ ] **2c.3 Stage history and extracted facts**
  - IDs: FR-CLS-4, FR-CRM-1, section 9
  - Files: `classifier.py`, `crm_writer.py`; `tests/agents/test_stage_history.py`
  - Accept: each stage change writes previous stage, new stage, timestamp, reason and source email; Adventure Works facts (60 users, Dynamics 365, decision by end of Q4) and Northwind's loss reason are stored on the record.

- [ ] **2c.4 TR-1: stage after every email**
  - IDs: TR-1, R8, S8
  - Files: `tests/agents/test_stage_exact.py` (reads `expected_outcomes.json`; production code never does)
  - Accept: against the real model, the stage after every email equals the answer key, including the unanswered Northwind nudge causing no change. **If it fails: STOP AND ASK (S8).** I report each failing email and propose options; I do not loosen the test or touch the key (S2).

- [ ] **2c.5 TR-8 accuracy report**
  - IDs: TR-8, D5
  - Files: `tests/agents/test_model_accuracy.py`; report written to `reports/` (git-ignored, OQ-35); nothing is copied to `tests/baselines/` unless you decide
  - Accept: every run writes accuracy per email and overall, with model name and `num_ctx`; the replay duration is recorded and shown to you.

- [ ] **2c.6 Smoke test: Slice 2 assertions become real**
  - IDs: TR-9, TR-6
  - Files: `tests/smoke/test_smoke.py`
  - Accept: the skips for stages become real assertions; scheduling and approval stay explicit "not yet implemented (Slice N)" skips. Covers: warm-up; replay all emails through the orchestrator; Fabrikam Converted, Northwind Not Converted, Adventure Works Engagement, Tailspin Engagement, Wingtip Presentation/Follow-up; no duplicate records; replay twice identical; accuracy printed.

- [ ] **2c.7 Commit point (2c)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests and the single smoke test pass (stage assertions real, scheduling and approval explicit skips); show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 2c definition of done:** all five customers reach their final stage and accuracy is reported.
**Tests that must pass:** TR-1 (all parts so far), TR-6 replay, TR-8 report, earlier tests.
**Smoke test:** staging row 2.
**hld.md section 12.2 items settled:** none.
**Slice-start question (S6):** whether FR-CLS-3 needs a deterministic guard if the model cannot meet it; asked only if 2c.4 fails.

### 2d Summary, next action and the TR-3 scorer

- [ ] **2d.1 Summary and Next Action agent**
  - IDs: FR-SUM-1, FR-SUM-2, OQ-23, section 9
  - Files: `src/crm_agents/agents/summary.py`; `tests/agents/test_summary_records.py`
  - Accept: after each email an append-only `note` engagement entry marked as the running summary is stored (the latest is current); a next action (description, optional due date, status `open`) is stored; Fabrikam gets the kickoff on 27 October 09:00 CT as the next action and Northwind a re-engage in April 2027 (checked as part of TR-1 outcomes in section 10).

- [ ] **2d.2 TR-3 gating layer (must pass)**
  - IDs: TR-3, `decisions.md` (TR-3 scorer), R8
  - Files: `tests/agents/scoring/gating.py`, `tests/agents/test_summary_gating.py`
  - Accept: for every generated summary, every date, name, number and company in the text appears in the source emails or CRM record, and the required facts (taken from the extracted facts and the record, never from the answer key) are present. A deliberately altered summary (a made-up company or date, built by the test) fails the check. If normalization of dates or names produces ambiguous cases, **STOP AND ASK** rather than loosening the check.

- [ ] **2d.3 TR-3 advisory layer (never gates)**
  - IDs: TR-3, `decisions.md`
  - Files: `tests/agents/rubrics/summary.md`, `tests/agents/scoring/advisory.py`, `reports/tr3_baseline.json` (git-ignored, OQ-35), `tests/agents/test_summary_advisory.py`
  - Accept: a written rubric (accuracy, completeness, tone, actionability, 1 to 5) is scored by the local model; the first run records a baseline in `reports/` (copied to `tests/baselines/` only when you decide, OQ-35); later runs report regressions; **nothing here fails a slice**. The weakness of an 8B model as its own judge is stated in the report.

- [ ] **2d.4 Owner sample for demos**
  - IDs: `decisions.md` (owner reads a sample of drafts before demos)
  - Files: `reports/draft_samples.md` (generated)
  - Accept: a readable file with a sample of summaries (and, from 3d, drafts) is produced for you to read; the demo is not shown to anyone until you confirm you have read it.

- [ ] **2d.5 Pipeline integration and smoke test update**
  - IDs: FR-SUM-1, TR-9, TR-8
  - Files: `pipeline.py`; `tests/smoke/test_smoke.py`
  - Accept: the full stage-1 pipeline (ingestion, classifier, summary) runs; smoke includes TR-3 gating and prints the TR-8 report; replay twice is identical.

- [ ] **2d.6 Commit point (2d) and Slice 2 close**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: all tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 2 (overall) definition of done:** see the overall plan, section 8.
**Tests that must pass:** TR-1, TR-3 gating, TR-6 replay, TR-8 report, earlier tests.
**Smoke test:** staging row 2.
**hld.md section 12.2 items settled:** the TR-3 scorer (decided in `decisions.md`, implemented here).

---

## Slice 3: Scheduler agent

### 3a Local `CalendarProvider` and time logic (pure code)

- [ ] **3a.1 Read availability and working hours**
  - IDs: section 6, FR-SCH-5, OQ-6, OQ-15, OQ-28, R10
  - Files: `src/crm_agents/providers/local/mock_calendar.py`; `tests/agents/test_mock_calendar_read.py`
  - Accept: `get_availability` returns per user `working_hours` and `busy_blocks` as `TimeInZone`; a user without working hours gets the default (08:00 to 17:00 Mon to Fri `America/Chicago`); the window is read from the JSON `window` (2026-10-19T00:00 to 2026-10-31T00:00 America/Chicago) and is **end exclusive** (OQ-37): availability at or after 2026-10-31T00:00, or before the start, is "unknown, no calendar data", not free; boundary test: a 30-minute range ending at 2026-10-31T00:00 is known, one starting at 2026-10-31T00:00 is unknown; facts check: Raj busy 09:00 to 10:00 on Oct 27, Sarah out of office all of Oct 19, David's lunch is `free`, Raj out of office Oct 23.

- [ ] **3a.2 Create, update, find and find_events with the overlay**
  - IDs: FR-APP-2, FR-SCH-9, OQ-9, OQ-15, OQ-22, D11, R6, R10, requirements section 6
  - Files: `mock_calendar.py`; `tests/agents/test_mock_calendar_write.py`, `tests/agents/test_mock_calendar_find_events.py`
  - Accept: `create_event` is idempotent on the event key and marks the join link simulated; `update_event` on `wingtip-walkthrough-20261022` writes to a SQLite overlay merged over the JSON on read, so `find_event`, `find_events` and `get_availability` see the change; a hash of `mock_calendars.json` is identical before and after (the dataset never changes). **`find_events(users, attendee_addresses, start, end)` (D11)** reads `attendees` and the event key (`iCalUId`) from the mock JSON (attendees there are address strings), merges the overlay (updated events as updated, events the system created, cancelled status), returns **one event per event key** even when several attendees' calendars hold it, returns only events that include one of the given addresses (case-insensitive) as an attendee, marks each attendee internal or external by the organization domain from `config/team.json` (not hardcoded), and returns nothing for ranges outside the mock window (unknown, OQ-15). Tests (real provider, real temporary SQLite, the dataset read-only): Emily's and David's copies of the Oct 22 walkthrough come back as one event for `james.carter@wingtiptoys.com`; an unrelated address returns none; an event created through the provider appears; an overlay-moved event is returned at its new time; a missing `isCancelled` counts as not cancelled.

- [ ] **3a.3 Derive the sender's time zone**
  - IDs: FR-SCH-2, OQ-7, R9, S6
  - Files: `src/crm_agents/scheduling/zones.py`; `tests/agents/test_zone_derivation.py`
  - Accept: order is contact zone, explicit zone in text, then candidate zones whose UTC offset on the email's sent date equals the `Date` offset, narrowed by hints and **validated in code**; unresolved ambiguity returns "ask the customer to confirm", never a guess, and the Scheduler turns it into outcome `request_clarification` asking the customer to confirm their time zone, proposing no times and creating no meeting (FR-SCH-3, OQ-34); a test with a constructed ambiguous `Date` offset and no zone hint asserts this. The slice-start question (S6) is answered first and recorded: how zone abbreviations and city hints are tabulated (as general data, not dataset-specific). Tests include real dataset headers (London +0100, Denver -0600, New York -0400) and constructed ambiguous cases.

- [ ] **3a.4 Resolve windows to UTC (relative dates, DST, past times)**
  - IDs: FR-SCH-2, OQ-5, OQ-24, R4, R9, S6
  - Files: `src/crm_agents/scheduling/windows.py`; `tests/agents/test_windows.py`
  - Accept: the slice-start question "what does 'next Thursday' mean" is answered and recorded first (S6). Relative dates resolve against the email's sent date in the sender's zone; the injected clock only discards past windows; Adventure Works' Oct 27 14:00 to 16:00 GMT converts to 09:00 to 11:00 CDT while Oct 20 15:00 to 17:00 BST is 09:00 to 11:00 CDT as well (6 h versus 5 h offset; a fixed-offset result would be 08:00 on Oct 27 and the test names that failure).

- [ ] **3a.5 Commit point (3a)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; earlier tests and the single smoke test pass (skips unchanged); show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 3a definition of done:** calendar read and write paths and zone and window resolution proven by unit tests, including the DST trap.
**Tests that must pass:** 3a tests, earlier tests.
**Smoke test:** staging row 2 (unchanged) plus these tests.
**hld.md section 12.2 items settled:** none (`zoneinfo` was settled in 1a).

### 3b Availability evaluation and outcomes (pure code)

- [ ] **3b.1 Cap by working hours; blocking rules; assigned attendees only**
  - IDs: FR-SCH-5, FR-SCH-6, FR-SCH-10, section 8, R4
  - Files: `src/crm_agents/scheduling/availability.py`; `tests/agents/test_availability.py`
  - Accept: open-ended windows are capped by each attendee's working hours in their zone; `busy` and `oof` block, `tentative` is a lower-ranked fallback with a warning, `free` and `workingElsewhere` never block; a team member not on the meeting never blocks (Raj on Oct 23 for Wingtip).

- [ ] **3b.2 Slot generation, ranking and reasons**
  - IDs: FR-SCH-6, FR-SCH-11, OQ-4, section 8
  - Files: `src/crm_agents/scheduling/ranking.py`; `tests/agents/test_ranking.py`
  - Accept: slots follow the 30-minute granularity and the meeting duration from policy; at most 3 are returned; the tentative fallback is listed last with its warning; every accepted and rejected window carries a human-readable reason. **STOP AND ASK (S6):** whether `evaluated_results` entries are per window or per slot (decision recorded in `decisions.md`).

- [ ] **3b.3 Outcome selection**
  - IDs: FR-SCH-7, FR-SCH-3, FR-SCH-8, FR-SCH-9
  - Files: `src/crm_agents/scheduling/outcomes.py`; `tests/agents/test_outcomes.py`
  - Accept: exactly one of `recommend_slots`, `counter_propose`, `request_clarification`, `update_existing_meeting` for each input class (selected slot; no overlap; no concrete times; **ambiguous sender time zone, which gives `request_clarification` with no slots, FR-SCH-3, OQ-34**; reschedule of an existing meeting), each with its own test.

- [ ] **3b.4 TR-2 exact-match on the pure code**
  - IDs: TR-2, R8
  - Files: `tests/agents/test_scheduling_exact.py` (structured windows taken from `expected_outcomes.json`, tests only)
  - Accept: SCH-ADV: Oct 20 rejected (Emily busy until 10:30), Oct 21 fallback with warning (Raj tentative 08:30 to 09:00), Oct 27 selected 10:00 to 11:00 CT; SCH-TAIL: both windows rejected (Sarah out of office Oct 19; David busy 08:30 to 10:00 Oct 22), `counter_propose` with 2 or 3 mutual 30-minute morning slots within 09:00 to 13:00 CT and none on Oct 19 (valid-example membership); SCH-WING: Oct 21 rejected (only 30 minutes common after capping at 17:00), Oct 23 selected 10:00 to 11:00 CT, the free lunch does not block. If a result differs: **STOP AND ASK (S2, S8)**; if the key looks wrong I say so and do not change it.

- [ ] **3b.5 Commit point (3b)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 3b definition of done:** pure scheduling code reproduces the three scenario outcomes exactly.
**Tests that must pass:** TR-2 (pure code), earlier tests.
**Smoke test:** staging row 2 plus these tests.
**hld.md section 12.2 items settled:** `evaluated_results` per window or per slot.

### 3c Scheduler Agent (model for text, code for decisions)

- [ ] **3c.1 Intent detection and window extraction**
  - IDs: FR-SCH-1, FR-SCH-2, OQ-11, R4
  - Files: `src/crm_agents/agents/scheduler.py` (extraction part); `tests/agents/test_window_extraction.py`
  - Accept: against the real model and using only the cleaned new text: A05 yields the three Adventure Works windows; T03 yields the two Tailspin windows and the preference "mornings"; W06 yields a reschedule intent with the open-ended Oct 21 window, the Oct 23 window and the customer's reference to the original meeting as text ("Thursday's walkthrough"), unconverted; T01 yields no concrete times; times that appear only in quoted older text never trigger scheduling. The model returns only stated text and hints; it does no conversion. Failures are reported (S8), not loosened.

- [ ] **3c.2 Locate the existing meeting with `find_events` (FR-SCH-9, D11)**
  - IDs: FR-SCH-9, FR-SCH-7, D11, OQ-22, R4, R6, R8
  - Files: `src/crm_agents/scheduling/reschedule.py` (the rule, plain code), `scheduler.py`; `tests/agents/test_reschedule_lookup.py`
  - Accept: decided in `decisions.md` D11 and `REQUIREMENTS.md` FR-SCH-9 (no question left). The rule: candidates come from `find_events` for the assigned attendees and the addresses on the trigger email (From, To, Cc): upcoming (at or after the simulated now), non-cancelled events that include an external attendee address from the email, falling back to the sender's domain read from that email at run time; **exactly one match** is the target (`update_existing_meeting`, `target_event_key` set); **several matches** are narrowed by the original meeting day the email mentions (the model extracts the phrase as text, 3c.1; code resolves it with the sent-date convention from 3a.4 in the sender's zone); anything else is `request_clarification` and **nothing is created or updated, never a duplicate**. No customer names, event keys or dates from the dataset in production code (the guard test passes). Tests (the data they need beyond the dataset is built by the test in a temporary copy of the calendar JSON or through the real provider's `create_event` in a temporary database; **the dataset files are never changed**):
    - **W06 case:** the real W06 email and the real calendars give exactly one match, the Oct 22 walkthrough, and the outcome is `update_existing_meeting` with that event key.
    - **Several matches:** two upcoming events share the customer's address; the original-day phrase picks the right one; with a phrase that matches neither, or none at all, the result is `request_clarification` and nothing changes.
    - **No match:** no upcoming event includes any address from the email (and none shares the sender's domain), so the result is `request_clarification`; asserts that no event was created or updated and the calendar overlay is unchanged (never a duplicate).
    - Also: a cancelled event and a past event are ignored; the domain fallback applies only when no address matches; an event held on two calendars counts once.

- [ ] **3c.3 Build the scheduling request**
  - IDs: FR-SCH-4, FR-SCH-5, FR-SCH-11, OQ-10, FR-CRM-1
  - Files: `scheduler.py`, `crm_writer.py`; `tests/agents/test_scheduler_request.py`
  - Accept: internal attendees come from `config/team.json` assignment rules plus CC'd external addresses at the customer's domain on the trigger email; the request is stored in state `pending` with parsed slots, attendees considered, evaluated results with reasons, proposed slots, outcome type and target event key (for the reschedule); a second replay stores the same request (R6).

- [ ] **3c.4 Stage 1 never books or sends**
  - IDs: R5, section 10 note
  - Files: `tests/agents/test_stage1_no_side_effects.py`
  - Accept: after a full replay there is no meeting created, the Wingtip event is unchanged, the outbox is empty and no draft exists in the mailbox; an architecture test confirms agents do not call `send_draft`, `create_event` or `update_event`.

- [ ] **3c.5 End-to-end TR-2 and TR-1 clarification**
  - IDs: TR-1, TR-2, S8
  - Files: `tests/agents/test_scheduling_end_to_end.py`
  - Accept: against the real model after a full replay, the requests are asserted **by trigger email** (OQ-34): A05 is `pending` with `recommend_slots` (Oct 27 10:00 to 11:00 CT), T03 is `pending` with `counter_propose` (no meeting), W06 is `pending` with `update_existing_meeting`; T01's request has outcome `request_clarification`, guessed no times and is **still `pending` at this point** (3d.4 supersedes it); no other request exists. W06 end to end exercises the same lookup with the real model's extraction. Failures: report and ask (S8).

- [ ] **3c.6 Commit point (3c)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests and the single smoke test pass (the pending-request assertions by trigger email are real; approval ones stay explicit skips until 3f.5, OQ-38); show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 3c definition of done:** replay leaves the three expected scenario requests (trigger emails A05, T03, W06) pending, T01's clarification request still pending until 3d.4 (OQ-34), and nothing booked or sent.
**Tests that must pass:** TR-1 clarification, TR-2 end to end (before approval), the reschedule lookup tests of 3c.2 (W06 single match, several matches, no match), 3a.2 `find_events` tests, earlier tests.
**Smoke test:** staging row 3, part (a).
**hld.md section 12.2 items settled:** none (the event-location rule is decided in D11 and FR-SCH-9).

### 3d Drafts and request lifecycle (TR-10, TR-3 for drafts)

- [ ] **3d.1 Prepare draft replies**
  - IDs: FR-SCH-3, FR-SCH-8, R4, OQ-2
  - Files: `scheduler.py`; `tests/agents/test_drafts.py`
  - Accept: the model writes prose around placeholders and **code inserts the times** formatted in the customer's zone; the Tailspin counter-proposal shows 2 or 3 slots in Mountain time with none on Oct 19; Adventure Works shows the proposed time in London time; a clarification asks for specific times; **a time zone clarification (ambiguous sender zone, FR-SCH-3, OQ-34) asks the customer to confirm their time zone and lists no times, with a test**; **a reschedule clarification (no match, or several unresolved matches in 3c.2) asks which meeting is meant**; the draft is stored on the request and nothing is sent.

- [ ] **3d.2 TR-3 for drafts**
  - IDs: TR-3, `decisions.md`
  - Files: `tests/agents/test_draft_gating.py`, `tests/agents/rubrics/draft.md`
  - Accept: the gating checks (every date, name, number and company appears in the source emails, the CRM record or the computed slots; required facts present) pass for all three drafts; the advisory rubric score is recorded against a baseline and never gates; drafts are added to `reports/draft_samples.md` for you to read.

- [ ] **3d.3 STOP AND ASK: when expiry is evaluated**
  - IDs: FR-SCH-12, OQ-16, OQ-24, S6
  - Files: decision recorded in `inputs/decisions.md`
  - Accept: you decide when "all offered windows are past" is evaluated. Proposal: at the start of every stage-1 run and again before an approval (approving an expired request returns `409 invalid_state`).

- [ ] **3d.4 Supersede, cancel, expire**
  - IDs: FR-SCH-12, OQ-16, OQ-32
  - Files: `scheduler.py`, `crm_writer.py`; `tests/agents/test_request_states.py`
  - Accept: a newer email in the same thread offering new times sets the earlier pending request to `superseded` and records `superseded_by`; a withdrawal sets it to `cancelled`; a request whose windows are all past becomes `expired`; old requests are kept; T01's clarification request becomes `superseded` by the request from T03 (T03 references T01 and T02, so they share a thread; OQ-34) with `superseded_by` set, and T03's counter-proposal stays `pending`; after this item exactly three requests are `pending` (A05, T03, W06).

- [ ] **3d.5 TR-10 with an injected later simulated clock**
  - IDs: TR-10, OQ-24, R11
  - Files: `tests/agents/test_request_lifecycle.py`
  - Accept: because the clock is fixed at `SIMULATED_NOW` and the three scenario windows (19 to 27 Oct) are later than it, **nothing expires in a normal replay**, so the test injects a later clock for the expiry case: replay as normal, then run again with the clock set after every offered window and assert the pending requests become `expired` while being kept. The same file covers supersede (real thread from the dataset) and cancel (a withdrawal `.eml` created in a temporary mail folder by the test, never added to the dataset). All four transitions match FR-SCH-12.

- [ ] **3d.6 Commit point (3d)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 3d definition of done:** drafts are code-formatted and gated; the four lifecycle transitions are tested, including expiry via an injected clock.
**Tests that must pass:** TR-10, TR-3 (drafts), earlier tests.
**Smoke test:** staging row 3, part (a), now with drafts present and T01's request superseded.
**hld.md section 12.2 items settled:** TR-3 scorer extended to drafts.

### 3e Approval handler

- [ ] **3e.1 Intent, steps and states**
  - IDs: FR-APP-3, FR-APP-4, FR-APP-5, OQ-18, OQ-20, OQ-27
  - Files: `src/crm_agents/orchestrator/approval.py`; `tests/agents/test_approval_steps.py`
  - Accept: `approve` records decision `approve`, `decided_by` (the configured approver) and `decided_at` first, with progress `in_progress`; steps run in order (`recheck_availability`, `create_or_update_event`, `send_confirmation`, `write_crm_updates`); each step writes an `AgentRun` linked to the request; the state becomes `approved` after the re-check passes; progress ends `completed`.

- [ ] **3e.2 Outcome matrix**
  - IDs: FR-APP-2, OQ-29, FR-SCH-9
  - Files: `approval.py`; `tests/agents/test_approval_matrix.py`
  - Accept: `recommend_slots` re-checks the chosen slot and creates the event once; `update_existing_meeting` re-checks, re-reads the target event (`find_event` by the key stored on the request, located earlier by `find_events`), updates it and adds the attendee; `counter_propose` and `request_clarification` record the re-check and event steps as not applicable and only send; approval names exactly one slot id for the two booking outcomes.

- [ ] **3e.3 Send path**
  - IDs: FR-APP-2, OQ-25, FR-ING-7
  - Files: `approval.py`, `eml_mail.py`; `tests/agents/test_approval_send.py`
  - Accept: the handler calls `create_reply_draft` then `send_draft`; the sent mail appears as an engagement entry; a later arrival of the same Message-ID is deduplicated. **Optional edited draft body (OQ-36):** `Orchestrator.approve` accepts it, records it as an audit entry like an edit (OQ-4) and sends the approved text; tests: approve with an edited body sends exactly that text and leaves one edit audit entry; approve without one sends the stored draft; the edit changes no other field.

- [ ] **3e.4 Post-approval scenario outcomes (TR-2 after approval)**
  - IDs: TR-2, section 10 note, FR-CRM-2, OQ-8, R10
  - Files: `tests/agents/test_scheduling_after_approval.py`
  - Accept: SCH-ADV: one meeting 15:00 to 16:00 UTC (10:00 to 11:00 CT) with attendees Emily, Raj, Oliver Bennett, Sophie Turner, simulated join link, customer response status null, stage Presentation/Follow-up with a stage-history entry whose source is the approval; SCH-TAIL: counter-proposal sent, no meeting, stage Engagement; SCH-WING: the existing event moved to Oct 23 10:00 to 11:00 CT with `lisa.park@wingtiptoys.com` added, **no second event**, stage unchanged.

- [ ] **3e.5 Commit point (3e)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 3e definition of done:** approval produces the section 10 outcomes for all three scenarios.
**Tests that must pass:** TR-2 after approval, earlier tests.
**Smoke test:** staging row 3 unchanged. `Orchestrator.approve` exists from 3e and is unit-tested here (OQ-38); the smoke-test approval assertions stay explicit skips and become real at 3f.5.
**hld.md section 12.2 items settled:** none.

### 3f Approval tests: repeat approval, re-check conflict, step failure

- [ ] **3f.1 TR-6: approve twice**
  - IDs: TR-6, R6
  - Files: `tests/agents/test_approve_twice.py`
  - Accept: approving each request twice (also with a retry after completion) creates no second meeting or event, no second sent message, no second stage-history row, and does not re-run completed steps.

- [ ] **3f.2 TR-11: calendar conflict after proposal**
  - IDs: TR-11, FR-APP-4, OQ-18, OQ-31, OQ-32
  - Files: `tests/agents/test_approval_recheck.py`
  - Accept: after replay, a real conflicting busy event is written to the calendar through the real provider (test fixture); approving returns `needs_review`; nothing is booked or sent; progress returns to `not_started`; fresh options replace the proposed slots and the earlier ones are kept in an audit entry; approving one fresh option then completes; rejecting also works.

- [ ] **3f.3 TR-12: forced step failure and retry**
  - IDs: TR-12, FR-APP-5, R1, R6, S6
  - Files: `tests/agents/test_approval_failure.py`
  - Accept: a real, controllable failure at the send step (slice-start question S6, answered first: for example making the outbox location unwritable, **with no test hook in production code**) leaves progress `partially_completed` with the failed step visible and the created meeting kept; fixing the condition and retrying completes without a second meeting. If this cannot be done without a hook in production code, **STOP AND ASK**.

- [ ] **3f.4 Reject and edit**
  - IDs: FR-APP-1, OQ-4, OQ-26
  - Files: `tests/agents/test_reject_edit.py`
  - Accept: reject sets `rejected`, records the optional reason and `decided_by` and `decided_at`, and does nothing else; edit changes only the draft text, adds an audit entry and leaves `decision`, state and approval progress unchanged.

- [ ] **3f.5 Smoke test: Slice 3 assertions become real, and Slice 3 close**
  - IDs: TR-9, TR-6
  - Files: `tests/smoke/test_smoke.py`
  - Accept: the scheduling and approval skips (except the real-endpoint ones) become real assertions. Covers: warm-up; replay (final stages; the three scenario requests pending by trigger email; nothing booked or sent); approval through `Orchestrator.approve` for each; repeat approvals; no duplicates. **The only remaining skips are the real-endpoint approval assertions, each shown as "not yet implemented (Slice 4d)".** show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 3 (overall) definition of done:** see the overall plan, section 8.
**Tests that must pass:** TR-1, TR-2, TR-3, TR-6, TR-10, TR-11, TR-12 and all earlier tests.
**Smoke test:** staging row 3.
**Commit point:** after each of 3a to 3f.
**hld.md section 12.2 items settled:** `evaluated_results` per window or slot (3b); TR-3 for drafts (3d).

---

## Slice 4: CRM API, dashboard, Teams agent

### 4a API foundation and safety

- [ ] **4a.1 STOP AND ASK: pin FastAPI and uvicorn (approved in principle)**
  - IDs: S1, S3, `decisions.md` (dependency approvals)
  - Files: `inputs/references.md` (pin lines)
  - Accept: I propose exact versions and release dates for `fastapi` and `uvicorn` from PyPI, with their official docs read for the safety checks (host, origin, CORS, content type, binding to 127.0.0.1) and their transitive dependencies listed; you spot-check; only then they go into `references.md` and are installed. Endpoint paths and payloads of `docs/api.md` (a proposal) are confirmed here.

- [ ] **4a.2 App skeleton bound to 127.0.0.1**
  - IDs: FR-API-1, OQ-13, OQ-30, `decisions.md` API safety
  - Files: `src/crm_agents/api/app.py`; `tests/backend/test_api_bind.py`
  - Accept: the server listens on `127.0.0.1:API_PORT` only (the bind address is not a setting); a test confirms a connection through the machine's non-loopback address is refused; the API calls the `Orchestrator` and `CrmRepository` interfaces only.

- [ ] **4a.3 Safety checks**
  - IDs: R5, TR-13, `decisions.md` (OQ-33, API safety)
  - Files: `src/crm_agents/api/safety.py`; `tests/backend/test_api_safety.py`
  - Accept: `Host` must be `127.0.0.1:<port>` or `localhost:<port>`; `Origin`, when present, must equal `DASHBOARD_ORIGIN` (`null` rejected); CORS allows only that origin, with `Vary: Origin`, methods `GET, POST, PATCH`, headers `Content-Type, X-CRM-Token, Idempotency-Key`; an empty `DASHBOARD_ORIGIN` allows no cross-origin request; every `POST` and `PATCH` needs `Content-Type: application/json` (else 415) and `X-CRM-Token` (missing 401, wrong 403).

- [ ] **4a.4 `GET /session`, `GET /health`, `GET /providers`**
  - IDs: OQ-33, D5, R3, R10, FR-CFG-1, FR-UI-4
  - Files: `api/routes_system.py`; `tests/backend/test_api_system.py`
  - Accept: the token is generated at start from a cryptographically secure source, kept in memory only and never logged or written to a file; `/health` shows mode, simulated clock, model warm state and the configured approver; `/providers` shows active local providers and the live ones as `implemented, unverified` and disabled (they do not exist until Slice 5, so the live list is empty or marked "not yet written").

- [ ] **4a.5 TR-13**
  - IDs: TR-13, R5
  - Files: `tests/backend/test_tr13.py`, `tests/backend/curl/tr13_*.sh`
  - Accept: against a real running server, the approve endpoint rejects a foreign `Origin`, a missing `X-CRM-Token` and a wrong content type, and in each case the request stays `pending` with nothing created or sent; extras: wrong token, `Origin: null`, wrong `Host`, preflight from another origin gets no CORS allow headers. (The approve endpoint exists from 4d; until then the same checks run on `PATCH` draft or a harmless write; the TR-13 test is finalized at 4d.)

- [ ] **4a.6 Commit point (4a)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; the single smoke test still passes (only the real-endpoint skips remain); show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 4a definition of done:** a localhost-only API with all safety checks and the system endpoints.
**Tests that must pass:** TR-13 (on the endpoints available), system endpoint tests, earlier tests.
**Smoke test:** staging row 3 plus the API starting and answering `/health`.
**hld.md section 12.2 items settled:** none.

### 4b Read endpoints

- [ ] **4b.1 Pipeline, customers, detail, timeline**
  - IDs: FR-API-1, FR-UI-1, FR-UI-2, section 6 queries
  - Files: `api/routes_customers.py`; `tests/backend/test_api_customers.py`, `tests/backend/curl/customers_*.sh`
  - Accept: `GET /pipeline` returns all five stages (empty ones included); `GET /customers` filters by stage, name and owner; `GET /customers/{id}` returns stage, contacts, stage history, summary and next action; `GET /customers/{id}/timeline` returns emails and meetings in time order; each endpoint has a curl command and a scripted equivalent (TR-4); times are UTC plus IANA zone.

- [ ] **4b.2 Next actions and audit**
  - IDs: FR-API-1, FR-UI-4, FR-AUD-1, OQ-12
  - Files: `api/routes_actions.py`, `api/routes_audit.py`; tests and curl scripts
  - Accept: `GET /next-actions` honors inclusive `due_from` and `due_to` and returns open actions by default; `GET /audit/runs` and `GET /audit/runs/{id}` list agent runs with provider and model, filterable, and contain no mail bodies or secrets.

- [ ] **4b.3 Scheduling request reads**
  - IDs: FR-UI-3, FR-SCH-12
  - Files: `api/routes_requests.py`; tests and curl scripts
  - Accept: `GET /scheduling-requests` filters by state (seven values), customer and outcome; `GET /scheduling-requests/{id}` returns the full object including reasons, proposed slots, draft, decision fields, approval progress and steps.

- [ ] **4b.4 Commit point (4b)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 4b definition of done:** all read endpoints work against the replayed data with curl and scripts.
**Tests that must pass:** TR-4 (read endpoints), earlier tests.
**Smoke test:** the single smoke test plus reading `/pipeline` (only the real-endpoint skips remain).
**hld.md section 12.2 items settled:** none.

### 4c Workflow, edit and reject endpoints

- [ ] **4c.1 Workflow trigger and progress**
  - IDs: FR-API-1, OQ-14, R5
  - Files: `api/routes_workflow.py`; `tests/backend/test_api_workflow.py`
  - Accept: `POST /workflow/runs` returns 202; a second request while a run is active returns 409; scope is all or one message; messages run sequentially in date order; `GET /workflow/runs/{id}` reports progress and failures; the run never books or sends.

- [ ] **4c.2 Edit draft**
  - IDs: FR-APP-1, OQ-4
  - Files: `api/routes_requests.py`; tests and curl scripts
  - Accept: `PATCH /scheduling-requests/{id}/draft` changes only the draft text, records an audit entry and leaves state and decision untouched; a non-`pending` request returns 409.

- [ ] **4c.3 Reject**
  - IDs: FR-APP-1, FR-APP-3, OQ-26
  - Files: same; tests and curl scripts
  - Accept: `POST .../reject` sets `rejected`, records `decided_by`, `decided_at` and the optional reason, and does nothing else; repeating returns the same result.

- [ ] **4c.4 Commit point (4c)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 4c definition of done:** the workflow runs through the API; edit and reject work.
**Tests that must pass:** TR-4 (these endpoints), TR-13 on these writes, earlier tests.
**Smoke test:** the single smoke test, with replay now triggered through `POST /workflow/runs` (only the real-endpoint approval skips remain).
**hld.md section 12.2 items settled:** none.

### 4d Approve endpoint and the full smoke test

- [ ] **4d.1 Approve endpoint**
  - IDs: FR-APP-2 to FR-APP-5, R5, R6, OQ-31, OQ-32
  - Files: `api/routes_requests.py`; `tests/backend/test_api_approve.py`, `tests/backend/curl/approve_*.sh`
  - Accept: the endpoint requires `Idempotency-Key` (400 if missing); the replay table of `docs/api.md` holds (same key returns the stored result with `idempotent_replay: true`; a different request or body with the same key is 422; a new key on a completed approval returns the recorded result; a new key while in progress is 409; a `partially_completed` approval retries); it names exactly one slot for booking outcomes; the body may carry an optional `draft_reply_body` (OQ-36), which is recorded as an edit audit entry and is the text sent, tested through HTTP (with and without it, and a repeat with the same key sends once).

- [ ] **4d.2 Conflict and failure responses**
  - IDs: TR-11, TR-12, FR-APP-4, FR-APP-5
  - Files: same; `tests/backend/test_api_approval_errors.py`
  - Accept: a conflict returns `409 availability_changed` with the request in `needs_review`, progress `not_started` and fresh options; a failed step returns `502 approval_step_failed` with progress `partially_completed`; both responses are the shapes in `docs/api.md`. The response codes and error names are a proposal there; confirm them at this item (S6).

- [ ] **4d.3 TR-13 on approve, TR-6 and TR-4 complete**
  - IDs: TR-13, TR-6, TR-4
  - Files: `tests/backend/test_tr13.py` (finalized), `tests/backend/test_api_approve_twice.py`
  - Accept: the three TR-13 cases pass against the approve endpoint; approving the same request twice through HTTP (same key and new key) creates no duplicates; every endpoint now has a curl command and a scripted equivalent.

- [ ] **4d.4 Full smoke test (TR-9)**
  - IDs: TR-9
  - Files: `tests/smoke/test_smoke.py`
  - Accept: **zero skips** (`pytest -rs tests/smoke/test_smoke.py` shows none): start the system in local mode; warm-up; replay all emails; every customer at its final stage; the three scheduling scenarios give their outcomes **before approval (pending)** and **after approval through the real approval endpoint**; the repeat-approval check; no duplicate records.

- [ ] **4d.5 Commit point (4d)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: all backend tests and the full smoke test pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 4d definition of done:** the backend is complete and the full TR-9 smoke test passes.
**Tests that must pass:** TR-4, TR-6, TR-11, TR-12, TR-13, TR-9 full, earlier tests.
**Smoke test:** the full smoke test (staging row 4d).
**hld.md section 12.2 items settled:** none.

### 4e Dashboard: pipeline and customer pages

- [ ] **4e.1 STOP AND ASK: pin React, Vite, TypeScript and Playwright (approved in principle)**
  - IDs: S1, S3, D2, `decisions.md` (dependency approvals)
  - Files: `inputs/references.md` (pins)
  - Accept: I propose exact versions and release dates from the npm registry (and Playwright's browser download requirement stated), with the official docs read; you spot-check; only then they go into `references.md` and are installed (Node 24.21.0 is present). Playwright usage is verified against its docs before any script is written (closes the skill TODO).

- [ ] **4e.2 Scaffold and token handling**
  - IDs: D2, R5, TR-13
  - Files: `frontend/` (Vite app), `frontend/src/api.ts`; `tests/frontend/`
  - Accept: the app builds and runs; it fetches the token from `GET /session` and sends `X-CRM-Token` on writes; the token is not stored in `localStorage`, files or logs; `DASHBOARD_ORIGIN` matches the dev server origin.

- [ ] **4e.3 Pipeline view**
  - IDs: FR-UI-1, R10
  - Files: `frontend/src/pages/Pipeline.tsx`; `tests/frontend/pipeline.spec.ts`
  - Accept: customers are grouped in the five stages after a replay, empty stages shown; Playwright asserts Fabrikam under Converted, Northwind under Not Converted, Adventure Works and Tailspin under Engagement, Wingtip under Presentation/Follow-up; the empty-stage confirmation (hld item) is shown to you here.

- [ ] **4e.4 Customer detail and timeline**
  - IDs: FR-UI-2, R10
  - Files: `frontend/src/pages/Customer.tsx`; `tests/frontend/customer.spec.ts`
  - Accept: stage, contacts, engagement timeline (emails and meetings), next action and the running summary are shown; simulated join links and "not available (simulated)" response status are visibly labeled.

- [ ] **4e.5 Commit point (4e)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: Playwright tests for these pages pass against a real local backend; earlier tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 4e definition of done:** pipeline and customer pages work end to end.
**Tests that must pass:** TR-5 (pipeline, timeline), earlier tests.
**Smoke test:** full TR-9 plus the Playwright pipeline check.
**hld.md section 12.2 items settled:** `customers_by_stage` empty stages; Playwright usage.

### 4f Scheduling panel and the approval flow

- [ ] **4f.1 Scheduling panel**
  - IDs: FR-UI-3, FR-SCH-11, OQ-4
  - Files: `frontend/src/pages/Scheduling.tsx`; `tests/frontend/scheduling.spec.ts`
  - Accept: shows parsed customer windows, availability results with a reason for every accepted and rejected slot, proposed slots (fallback last with its warning), attendees including CC'd externals before approval, the draft reply, state and approval progress.

- [ ] **4f.2 Approve, edit, reject**
  - IDs: FR-APP-1, FR-APP-2, FR-UI-3, R5, OQ-4
  - Files: same; `tests/frontend/approval.spec.ts`
  - Accept: three separate controls; nothing is sent or booked on load or on edit; approving names exactly one slot for booking outcomes; edit changes only the draft text; the approver shown is the configured user; Playwright runs approve, edit and reject on real pending requests.

- [ ] **4f.3 Conflict, partial failure and history display**
  - IDs: FR-APP-4, FR-APP-5, FR-SCH-12, OQ-31
  - Files: same; `tests/frontend/approval_states.spec.ts`
  - Accept: `needs_review` shows that nothing was booked and the fresh options with approve-one or reject; `partially_completed` shows the failed step and a retry control; superseded, cancelled and expired requests stay visible as history.

- [ ] **4f.4 Commit point (4f)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: Playwright scheduling and approval scripts pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 4f definition of done:** a person can review and approve, edit or reject each scenario from the browser.
**Tests that must pass:** TR-5 (scheduling panel, approve/edit/reject), earlier tests.
**Smoke test:** full TR-9 plus the Playwright approval flow.
**hld.md section 12.2 items settled:** none.

### 4g Audit view and UI polish

- [ ] **4g.1 Audit view**
  - IDs: FR-UI-4, FR-AUD-1
  - Files: `frontend/src/pages/Audit.tsx`; `tests/frontend/audit.spec.ts`
  - Accept: lists agent runs with agent, decision, provider and model, time and duration, filterable by run, agent and customer; each approval step is visible with its status; no mail bodies.

- [ ] **4g.2 STOP AND ASK: taste skill and graphify**
  - IDs: S1, S3
  - Files: decision in `inputs/decisions.md`
  - Accept: before anything is installed, the taste skill's `SKILL.md` files at the pinned commit are read (third-party instructions) and summarized to you; you decide whether to use it. Graphify stays a developer tool and is not added to the project unless you decide.

- [ ] **4g.3 UI quality pass and Playwright completion**
  - IDs: TR-5, `crm-ui-quality` skill
  - Files: `frontend/**`, `tests/frontend/**`
  - Accept: the golden path and edge cases (empty pipeline, failed run, rejected slot, edited draft, `needs_review`, `partially_completed`) are exercised in a real browser run, not only type checks; all Playwright scripts pass.

- [ ] **4g.4 Owner sample before any demo**
  - IDs: `decisions.md` (TR-3)
  - Files: `reports/draft_samples.md` refreshed
  - Accept: you confirm you have read the sample of summaries and drafts; `docs/demo.md` is re-read against what the screens actually do.

- [ ] **4g.5 Commit point (4g)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: TR-5 complete; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 4g definition of done:** the dashboard has all four views and TR-5 passes.
**Tests that must pass:** TR-5 (all), earlier tests.
**Smoke test:** full TR-9.
**hld.md section 12.2 items settled:** taste skill review.

### 4h Teams Copilot agent (D6: after the dashboard)

- [ ] **4h.1 STOP AND ASK: scope for the Teams agent**
  - IDs: FR-UI-5, D6, S3, requirements section 17 (explicit deferral allowed)
  - Files: decision in `inputs/decisions.md`
  - Accept: the Microsoft 365 Agents Toolkit and how it would call the CRM API are not researched yet. You decide: research it and write the agent from documentation marked UNVERIFIED (it cannot run without a tenant), or defer it with your agreement (allowed by section 17).

- [ ] **4h.2 If approved: research and write from docs**
  - IDs: FR-UI-5, section 12, R3
  - Files: `docs/first_day_with_access.md` (item 15), agent files under a path you approve; contract-style tests
  - Accept: official docs read and cited with dates; the agent answers "where does Fabrikam stand?" and "what are my next actions this week?" through the same API, uses no private endpoint, and is labeled `implemented, unverified`; the open question of mapping a Teams user to an account owner is recorded (hld item).

- [ ] **4h.3 Commit point (4h) and Slice 4 close**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass (or the deferral is recorded in `decisions.md`); show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 4h definition of done:** the Teams agent is written from documentation and labeled, or its deferral is agreed in writing.
**Tests that must pass:** earlier tests; any contract tests written.
**Smoke test:** full TR-9.
**hld.md section 12.2 items settled:** Teams user to account owner (recorded, not verifiable without a tenant).

**Slice 4 (overall) definition of done:** see the overall plan, section 8.
**Commit point:** after each of 4a to 4h.

---

## Slice 5: Live providers written from documentation (all UNVERIFIED)

Rule for all of Slice 5: **re-read the official docs and changelog for each call before writing it, record the URL and date beside the code, and STOP AND ASK (S3) for anything that cannot be verified.** Live adapters are disabled by default, refuse to start without configuration, and are labeled `implemented, unverified` (R3). Contract tests use sample responses shaped like the documented output and are labeled contract tests, never live verification.

### 5a Live model adapters

- [ ] **5a.1 STOP AND ASK: contract-test approach**
  - IDs: TR-7, S1, S3
  - Files: decision in `inputs/decisions.md`
  - Accept: you approve how sample responses reach the real adapter code without stubbing the adapter (for example an HTTP transport returning documented sample JSON) and which HTTP library is used (`httpx` is transitive; direct use needs approval).

- [ ] **5a.2 Foundry adapter, then Azure OpenAI adapter**
  - IDs: R3, section 12, S3, `crm-agent-framework-azure-openai` skill
  - Files: `src/crm_agents/providers/live/foundry_model.py`, `azure_openai_model.py`; `tests/agents/test_live_model_contract.py`
  - Accept: `FoundryChatClient` is first choice and `agent_framework.openai` with Azure routing second; structured output via `response_format`; validation and bounded retries behave like the Ollama provider; refuses to start without its configuration; contract tests pass and are labeled `contract`, not `live`.

- [ ] **5a.3 Commit point (5a)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; `/providers` shows the adapters `implemented, unverified` and disabled; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 5a definition of done:** both live model adapters exist behind `ChatModelProvider` and are contract-tested.
**Tests that must pass:** TR-7 (model), earlier tests.
**Smoke test:** full TR-9 (local).
**hld.md section 12.2 items settled:** none (client choice remains for Slice 6).

### 5b Live mail provider (Graph)

- [ ] **5b.1 Read paths**
  - IDs: FR-ING-1, FR-ING-3, section 12, S3
  - Files: `src/crm_agents/providers/live/graph_mail.py`; `tests/agents/test_live_mail_contract.py`
  - Accept: subscription on the Inbox with validation handshake, `clientState` and renewal before the documented maximum lifetime; message delta as a safety net; get message including thread identifiers and attachments; contract tests labeled; behavior behind `MailProvider` is the same shape as local.

- [ ] **5b.2 Reply draft and send**
  - IDs: FR-APP-2, OQ-25, R5
  - Files: same; tests
  - Accept: `createReply` then send, called only by the approval handler; no permission set is scoped in code (D7).

- [ ] **5b.3 Sent Items**
  - IDs: FR-ING-7, S3
  - Files: `docs/first_day_with_access.md` (item 12); adapter code if documented
  - Accept: the Microsoft docs for reading Sent Items are read and cited (not yet researched); if they cannot be verified, **STOP AND ASK** and record it as a first-day item.

- [ ] **5b.4 Commit point (5b)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: tests pass; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 5b definition of done:** the live mail adapter exists, is disabled and contract-tested.
**Tests that must pass:** TR-7 (mail), earlier tests.
**Smoke test:** full TR-9 (local).
**hld.md section 12.2 items settled:** none.

### 5c Live calendar provider (Graph)

- [ ] **5c.1 `get_availability` from `getSchedule`**
  - IDs: FR-SCH-5, OQ-6, OQ-28, section 12, S3
  - Files: `src/crm_agents/providers/live/graph_calendar.py`; `tests/agents/test_live_calendar_contract.py`
  - Accept: returns per user `working_hours` and `busy_blocks` using the documented `scheduleItems[].status` values and `workingHours` (including its time zone); intersection stays in our code (R4); contract tests labeled.

- [ ] **5c.2 Create, update, find, find_events**
  - IDs: FR-APP-2, FR-SCH-9, D11, R6, S3
  - Files: same; tests
  - Accept: create event as a Teams meeting with the customer as external attendee and an idempotency key; update (move time, add attendee); `find_event` by `iCalUId` is **not documented** (first-day item 4): **STOP AND ASK** about the fallback and record it. **`find_events` (D11)** is written against Graph `calendarView` per user (`GET /users/{id | userPrincipalName}/calendarView?startDateTime=&endDateTime=`; the event resource has `attendees` and `iCalUId`), recorded in `.claude/skills/crm-graph-integration/snippets/calendar-view-events.md` (read 2026-10-16) and marked **UNVERIFIED**: whether `attendees` comes back without `$select`, whether `Calendars.ReadBasic` includes it, paging, canceled events are TODOs and first-day item 17. Address matching happens in our code; the contract test uses a sample shaped like the documented output and is labeled a contract test. The reschedule `PATCH` body and accepted `timeZone` names are recorded as unverified.

- [ ] **5c.3 Commit point (5c)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: TR-7 complete; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 5c definition of done:** the live calendar adapter exists, is disabled and contract-tested.
**Tests that must pass:** TR-7 (all), earlier tests.
**Smoke test:** full TR-9 (local).
**hld.md section 12.2 items settled:** none (written, not verified).

### 5d First-day checklist and Phase 1 close-out

- [ ] **5d.1 Finalize `docs/first_day_with_access.md`**
  - IDs: section 12, D7, D8, S3
  - Files: `docs/first_day_with_access.md`
  - Accept: every live adapter detail written in 5a to 5c that is unverified has a numbered check with an empty result; permission needs are "to be confirmed with IT" and nothing is scoped in code.

- [ ] **5d.2 Docs reflect what was built**
  - IDs: section 17 (docs)
  - Files: `docs/hld.md`, `docs/lld.md`, `docs/api.md`, `docs/demo.md`
  - Accept: statements that were proposals are updated to what exists; `docs/demo.md` is re-read for jargon; anything unverified stays labeled.

- [ ] **5d.3 Phase 1 definition-of-done review**
  - IDs: section 17, R1 to R12
  - Files: this checklist; `plans/Overall_Implementation_plan.md` section 10
  - Accept: each line of requirements section 17 is checked with evidence (test run output, file); items you agreed to defer are listed.

- [ ] **5d.4 Commit point (5d)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: the entire test suite and the full smoke test pass; `git status` shows no `.env*`; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 5 (overall) definition of done:** see the overall plan, section 8.
**Tests that must pass:** TR-1 to TR-13 and the full smoke test.
**Smoke test:** full TR-9.
**Commit point:** after each of 5a to 5d.
**hld.md section 12.2 items settled:** none are verifiable; all are carried into the first-day checklist.

---

## Slice 6: Switch to live (blocked until access exists)

- [ ] **6.1 STOP AND ASK: access and approvals**
  - IDs: R12, D7, D8
  - Files: none
  - Accept: you confirm tenant access, what IT permits, the approver and the permission set (D7), and where the system runs (D8). Until then this slice does not start.

- [ ] **6.2 Switch by configuration**
  - IDs: R3, FR-CFG-1, OQ-21
  - Files: your `.env` (yours, unread by me), `example.env` if keys change
  - Accept: setting `PROVIDER_MODE=live` or per-provider keys selects the live providers; the active provider is recorded in the audit log; local mode still passes the full smoke test.

- [ ] **6.3 Verify each live provider against the first-day checklist**
  - IDs: `docs/first_day_with_access.md` items 1 to 17, S3
  - Files: `docs/first_day_with_access.md` (date and result beside each item), `tests/agents/test_live_*` (contract samples corrected against real responses)
  - Accept: each numbered check is run on the real service and its result and date written down; failures are fixed only after you decide (S2 applies to tests); nothing is claimed verified until its check is recorded.

- [ ] **6.4 Record decisions**
  - IDs: D7, D8, D9, OQ-13
  - Files: `inputs/decisions.md`
  - Accept: the permission set and approver (D7), hosting (D8), the outcome of revisiting Agent Framework Workflows (D9), the Entra ID design and whether the per-run token is still needed are recorded.

- [ ] **6.5 Commit point (6)**
  - IDs: R11, `CLAUDE.md` commit gate (tests and smoke pass), S5
  - Files: every file added or changed in this sub-slice, reviewed with `git status` and `git diff`; no `.env*`, no `.venv`
  - Accept: per verified provider; show `git status` and propose a commit message citing the IDs; **you commit** (S5).

**Slice 6 definition of done:** see the overall plan, section 8.
**Tests that must pass:** the full local suite and the first-day live checks.
**Smoke test:** local smoke test, then the same flow on the live providers where IT allows.
**Commit point:** after each verified provider.
**hld.md section 12.2 items settled:** Entra ID design and per-run token; optional health-check fallback; Foundry or Azure OpenAI choice; Graph permission set, approver, mailbox scoping and notification URL; `iCalUId` lookup, reschedule body and Sent Items behavior.
