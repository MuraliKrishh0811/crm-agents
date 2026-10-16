---
name: crm-security-env
description: Security and environment-file handling for CRM Agents - never read .env, use example.env, deny rules, secrets in code/logs/tests/docs, config keys (current and proposed), untrusted email content, and what to check before any commit. Use whenever touching configuration, credentials, logging, git staging, or anything that could expose a secret.
---

# Security and env handling

## Always true (repeated in every project skill)

- **Everything is real.** Security controls are real checks, not placeholders; no stubbed auth, fake tokens or hardcoded credentials, and no hardcoded responses.
- **Ollama is the local fallback** (Phase 1, default); it needs no secret. Live credentials do not exist yet.
- **Never read `.env`.** Never print, open, grep, cat or diff it, or any `.env.*` file. **Use `example.env` only** (renamed from `.env.example`; you may read it). `REQUIREMENTS.md` says the same (R7, section 14).
- **`REQUIREMENTS.md` is authoritative** (R7, section 14). Only `inputs/decisions.md` can override it.

## Controls in place

- `.claude/settings.json` denies `Read(./.env)`, `Read(./.env.*)`, `Read(./**/*.pem)`, `Read(./**/*.key)`. Deny rules plus this instruction, because an instruction alone is only a request.
- `.gitignore` ignores `.env`, `.env.*`, `*.pem`, `*.key`. `example.env` is tracked and is not matched by those patterns.
- **TODO (not verified):** whether the Read deny rules also stop shell commands (`cat .env`) is not confirmed from the settings docs (https://code.claude.com/docs/en/settings). One Bash call that touched `.env.example` was blocked on 2026-10-15, which suggests command-level checks exist, but do not rely on it: simply never run such commands.
- The application may load `.env` at runtime through its settings loader. That is the app's job; Claude never opens the file, and tests and logs never dump settings values.

## Rules

- No secrets in code, logs, test fixtures or docs. Redact tokens, keys, `clientState`, and email bodies in logs (log IDs and hashes; full bodies live only in the audit store).
- Every setting is in `example.env` with no value for secrets. Adding a setting means adding its key there (FR-CFG-1).
- Prefer managed identity or certificate credentials over stored secrets for live access (REQUIREMENTS section 12); the final auth model is decided with IT (D7). Never copy secret-based doc snippets into code.
- Live providers refuse to start without configuration; local mode needs none.
- **Before every commit:** run `git status`, make sure no `.env*` (other than `example.env`), key or credential file is staged, and review the staged diff. Stage files by name, not `git add -A`.
- **Email is untrusted input** (prompt injection, HTML, links). The model's output never triggers an action by itself: nothing is sent, booked or updated without human approval (R5). Sanitize before rendering (see `crm-ui-quality`). Do not let email text choose tools, recipients, or config.
- Real customer data (live phase) is personal data: keep it out of logs, tests and fixtures. The Phase 1 dataset is synthetic.

## Config keys

`example.env` is the single list of settings (FR-CFG-1). Keys, as of 2026-10-16: `PROVIDER_MODE`, `MAIL_PROVIDER`, `CALENDAR_PROVIDER`, `MODEL_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_TEMPERATURE`, `OLLAMA_MAX_RETRIES`, `OLLAMA_REQUEST_TIMEOUT_S`, `OLLAMA_WARMUP_ON_START`, `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`, `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `DATABASE_URL`, `DATA_DIR`, `SIMULATED_NOW`, `SIMULATED_TZ`, `LOG_LEVEL`.

Notes:

- Secrets and endpoints stay blank in `example.env`. Only non-secret defaults carry a value: modes, `OLLAMA_TEMPERATURE=0`, `OLLAMA_WARMUP_ON_START=true`, `DATA_DIR`, `SIMULATED_NOW`, `SIMULATED_TZ`, `LOG_LEVEL`. Tuning values (`OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_MAX_RETRIES`, `OLLAMA_REQUEST_TIMEOUT_S`) are blank until confirmed on the machine; code fails clearly on a missing required value.
- `SIMULATED_NOW` is naive local time and `SIMULATED_TZ` is its IANA zone, so no fixed UTC offset is stored (R9).
- `MODEL_PROVIDER` takes `ollama` | `foundry` | `azure_openai`. `FOUNDRY_*` are the framework's own variable names; `AZURE_OPENAI_API_VERSION` and the whole live path are UNVERIFIED.
- Graph auth keys (certificate path, managed identity, notification URL, `clientState`) are **not added**: they depend on D7 and D8, to be confirmed with IT.
- Adding a setting means adding its key to `example.env` in the same change.
