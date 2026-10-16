---
name: crm-security-env
description: Security and environment-file handling for CRM Agents - never read .env, use example.env, deny rules, secrets in code/logs/tests/docs, config keys, untrusted email content, and what to check before any commit. Use whenever touching configuration, credentials, logging, git staging, or anything that could expose a secret.
---

# Security and env handling

## Always true (repeated in every project skill)

- **Everything is real.** Security controls are real checks, not placeholders; no stubbed auth, fake tokens or hardcoded credentials, and no hardcoded responses.
- **Ollama is the local fallback** (Phase 1, default); it needs no secret. Live credentials do not exist yet.
- **`.env` (R7 as written in `REQUIREMENTS.md`):** Claude never opens, prints, searches, greps, cats, diffs or copies `.env` or any `.env.*` file. **Use `example.env` only** (you may read it). The one exception is the application's own settings loader, which may read `.env` when tests or smoke runs execute, only while `.env` holds no real secrets (Phase 1). The loader, logs and settings objects never print values, only key names and set or blank status.
- **`REQUIREMENTS.md` is authoritative** (R7, section 14). `inputs/decisions.md` records owner decisions where it is silent.

## Controls in place

- `.claude/settings.json` denies `Read(./.env)`, `Read(./.env.*)`, `Read(./**/*.pem)`, `Read(./**/*.key)`. Deny rules plus this instruction, because an instruction alone is only a request.
- `.gitignore` ignores `.env`, `.env.*`, `*.pem`, `*.key`. `example.env` is tracked and is not matched by those patterns.
- **TODO (not verified):** whether the Read deny rules also stop shell commands (`cat .env`) is not confirmed from the settings docs (https://code.claude.com/docs/en/settings). One Bash call that touched `.env.example` was blocked on 2026-10-15, which suggests command-level checks exist, but do not rely on it: simply never run such commands.
- The application loads `.env` at runtime through its settings loader (R7). Tests and smoke runs that Claude executes may use that loader; Claude itself never opens the file. Settings objects redact values in their string form, and tests and logs never dump settings values. Revisit before any real secret (key, token, password) is placed anywhere in the project: then use managed identity or inline environment variables.

## Rules

- No secrets in code, logs, test fixtures or docs. Redact tokens, keys, `clientState`, and email bodies in logs (log IDs and hashes; full bodies live only in the audit store).
- Every setting is in `example.env` with no value for secrets. Adding a setting means adding its key there (FR-CFG-1).
- Prefer managed identity or certificate credentials over stored secrets for live access (REQUIREMENTS section 12); the final auth model is decided with IT (D7). Never copy secret-based doc snippets into code.
- Live providers refuse to start without configuration; local mode needs none.
- **Before every commit (the owner commits; show `git status` and a proposed message, then wait):** run `git status`, make sure no `.env*` (other than `example.env`), key or credential file is staged, and review the staged diff. Stage files by name, not `git add -A`.
- **Email is untrusted input** (prompt injection, HTML, links). The model's output never triggers an action by itself: nothing is sent, booked or updated without human approval (R5). Sanitize before rendering (see `crm-ui-quality`). Do not let email text choose tools, recipients, or config.
- Real customer data (live phase) is personal data: keep it out of logs, tests and fixtures. The Phase 1 dataset is synthetic.

## Config keys

`example.env` is the single list of settings (FR-CFG-1). Keys, as of 2026-10-16: `PROVIDER_MODE`, `MAIL_PROVIDER`, `CALENDAR_PROVIDER`, `MODEL_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_TEMPERATURE`, `OLLAMA_MAX_RETRIES`, `OLLAMA_REQUEST_TIMEOUT_S`, `OLLAMA_WARMUP_ON_START`, `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`, `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `DATABASE_URL`, `DATA_DIR`, `SIMULATED_NOW`, `SIMULATED_TZ`, `LOG_LEVEL`, `APPROVER_USER`, `API_PORT`, `DASHBOARD_ORIGIN`, `STALE_LEAD_DAYS`.

Notes:

- Secrets and endpoints stay blank in `example.env`. Only non-secret values are filled (checked 2026-10-16): the modes, the Ollama starting values (`OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=llama3.1:8b`, `OLLAMA_NUM_CTX=4096`, `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_TEMPERATURE=0`, `OLLAMA_MAX_RETRIES=2`, `OLLAMA_REQUEST_TIMEOUT_S=120`, `OLLAMA_WARMUP_ON_START=true`, to be tuned on the machine), `DATA_DIR`, `SIMULATED_NOW`, `SIMULATED_TZ`, `LOG_LEVEL`, `APPROVER_USER=local-user`, `API_PORT=8000`, `DASHBOARD_ORIGIN=http://localhost:5173` and `STALE_LEAD_DAYS=14`. The live keys and `DATABASE_URL` are blank (`DATABASE_URL` is proposed in Slice 1). Code fails clearly on a missing required value. The owner creates `.env` with non-secret values; Claude never opens it. In Slice 0 the key-name check is run by the owner, who pastes the names-only output. From Slice 1a the application's loader check (plan item 1a.4b) prints names and set or blank status only and may be run by Claude (R7).
- `SIMULATED_NOW` is naive local time and `SIMULATED_TZ` is its IANA zone, so no fixed UTC offset is stored (R9). Both override `organization.simulationNow` in `config/team.json` (decisions.md OQ-5).
- **Phase 1 API access (decisions.md OQ-13 and "Additional rules"):** the approver is a configured local user name (`APPROVER_USER`, no login screen), recorded as `decided_by` with `decided_at` on every approval. The API port is `API_PORT` (OQ-30) and `DASHBOARD_ORIGIN` is the one origin CORS allows. Real authentication (Entra ID) is designed in `docs/api.md` section 10.2, marked UNVERIFIED, and built after live access exists. Because the approver identity is not authenticated, the API applies these measures before any handler (details and error codes in `docs/api.md` section 10.1; tested by TR-13): bind **127.0.0.1 only** (the bind address is deliberately not a setting); check `Host` and `Origin` (a foreign or `null` Origin is refused); CORS limited to `DASHBOARD_ORIGIN`, never `*`; `Content-Type: application/json` plus the `X-CRM-Token` header on writes; and a **random per-run token** (`X-CRM-Token`) generated when the API starts, **held in memory only, never in `.env`**, never logged, written to a file or put in a test fixture, compared in constant time. The token is deliberately not a config key. Clients fetch it from `GET /session` and send it in `X-CRM-Token` (hld.md OQ-33). These stop a web page in the same browser; they do **not** stop other programs on the same machine. Never expose the Phase 1 API beyond localhost.
- `STALE_LEAD_DAYS` is the `stale_leads` threshold (decisions.md OQ-12; starting value 14).
- `MODEL_PROVIDER` takes `ollama` | `foundry` | `azure_openai`. `FOUNDRY_*` are the framework's own variable names; `AZURE_OPENAI_API_VERSION` and the whole live path are UNVERIFIED.
- Graph auth keys (certificate path, managed identity, notification URL, `clientState`) are **not added**: they depend on D7 and D8, to be confirmed with IT.
- Adding a setting means adding its key to `example.env` in the same change.
