---
name: crm-ollama-local-model
description: Ollama as the local fallback model for CRM Agents - llama3.1:8b on a MacBook Air M4 (16 GB), ollama Python client 0.6.3, small context, schema-validated JSON with retry, warm-up call, qwen3:8b comparison via TR-8. Use when writing or tuning the local ChatModelProvider, any prompt, the warm-up, or the model-accuracy report.
---

# Ollama: the local fallback agent model

## Always true (repeated in every project skill)

- **Everything is real.** The local provider calls a real Ollama server and a real model. No mocking, stubs, canned or hardcoded model responses, no hardcoded snippets standing in for behavior.
- **Ollama is the local fallback** and the working model path in Phase 1 (R3). Live Foundry/Azure OpenAI is the later path (`crm-agent-framework-azure-openai`).
- **`.env` (R7):** Claude never opens, prints, searches or copies a `.env*` file; use `example.env` only. The application's own settings loader may read `.env` when tests or smoke runs execute (Phase 1, no real secrets); it never prints values.
- **`REQUIREMENTS.md` is authoritative** (sections 11, 13). `inputs/decisions.md` records owner decisions where it is silent.

## Decisions (D5, confirmed)

- Machine: **MacBook Air M4, 16 GB RAM**. Model: **`llama3.1:8b`**, set through `OLLAMA_MODEL`. Never hardcode the name.
- Compare **`qwen3:8b`** against it later using TR-8 (accuracy per run against the answer key). Do not pull or switch until asked.

## Client choice and install

Use the **`ollama` Python client directly**, pinned `ollama==0.6.3`. Snippets: [ollama-python-client.md](snippets/ollama-python-client.md) (verbatim README at tag v0.6.3; confirms `chat(format=, options=, keep_alive=)` in the pinned source).

The framework's `OllamaChatClient` (`agent-framework-ollama 1.0.0b261015`) is an **option only** ([maf-ollama-chat-client.md](snippets/maf-ollama-chat-client.md)). It requires `ollama>=0.5.3,<0.5.4`, which conflicts with 0.6.3, and `pip install agent-framework` pulls it in. Use one or the other in an environment, never both.

## Prompt and context discipline

- The classifier input is fixed by FR-CLS-1 (decisions.md OQ-19): the **new email text** (quoted history already stripped, FR-ING-2) plus the **current stage, the running summary, and the most recent engagement entries, bounded to fit the context window**. Never the full thread or the full history.
- **Bounding is deterministic code, not the model:** derive a token budget from `OLLAMA_NUM_CTX` minus the system prompt, the schema and room for the output; always keep the new text, current stage and running summary; fill what remains with the newest engagement entries, newest first. Log what was included and dropped (counts, not bodies). The exact trimming rule and token counting method are a Slice 2 implementation detail to verify with `ollama ps` and real runs; do not assume a tokenizer from memory.
- Other agents (summary, scheduler text tasks) get only the inputs they need, same budget rule.
- Short system prompts. Put the output JSON schema in the prompt as a string and also pass it as `format` (docs: "ideal to also pass the JSON schema as a string in the prompt").
- Set the context window **explicitly** with `options={"num_ctx": ...}` from config; do not rely on the default. Docs conflict (FAQ: 4096; context-length page: VRAM-based, under 24 GiB gives 4k), so confirm the real value with `ollama ps` (CONTEXT, PROCESSOR columns) on this machine. Keep it small; larger contexts cost memory, and CPU offload means it is too big.
- Temperature `0` for classification and extraction (docs tip).

## Structured output: validate and retry

1. Call `chat(..., format=Model.model_json_schema(), options={...})`.
2. Validate with `Model.model_validate_json(response.message.content)` (docs pattern in [structured-output-context-keepalive.md](snippets/structured-output-context-keepalive.md)).
3. On malformed or schema-invalid output, retry a bounded number of times (config), optionally feeding the validation error back; after that raise a typed error. The pipeline records the failure in the audit log and continues with the remaining emails (section 14).
4. Log provider, model, attempt count, duration per call (FR-AUD-1). Never log full email bodies at INFO.
5. The model never does time zone conversion, overlap or slot choice (R4); it extracts and drafts text only.

## Warm-up (Ollama unloads idle models)

By default models unload after 5 minutes (docs). So:

- Send a **warm-up call at startup** and as the **first step of the smoke test** (`crm-testing-smoke`), before replaying any email, so the first real call is not a cold load.
- Set `keep_alive` from config so the model stays loaded during a replay (accepts a duration string, seconds, or a negative number; `0` unloads; the API parameter overrides `OLLAMA_KEEP_ALIVE`).
- Docs show the preload only as an empty `/api/chat` HTTP request. **TODO (Slice 0, the warm-up test):** the Python equivalent is undocumented; test an empty-`messages` `chat(model=..., keep_alive=...)` against ollama 0.6.3, or fall back to a minimal real chat call. Do not claim it works until run.
- Check readiness with `ollama ps` / `ollama.ps()`; surface a clear error if Ollama is down or the model is not pulled (`ollama.ResponseError`, 404 means pull the model).

## Accuracy reporting (TR-8)

Each run records stage-classification accuracy against `data/synthetic/expected/expected_outcomes.json`, with the model name and `num_ctx` in the report, written to `reports/` (git-ignored; baselines are copied to `tests/baselines/` only when the owner decides, decisions.md OQ-35), so `llama3.1:8b` vs `qwen3:8b` is judged on evidence. Only tests read the answer key (R8). TODO before testing `qwen3:8b`: check how its thinking mode interacts with `format` (the pinned `chat()` has a `think` parameter; behavior not yet verified).

## Config keys

All in `example.env` (added 2026-10-16): `MODEL_PROVIDER=ollama`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_TEMPERATURE` (`0`), `OLLAMA_MAX_RETRIES`, `OLLAMA_REQUEST_TIMEOUT_S`, `OLLAMA_WARMUP_ON_START` (`true`). `example.env` holds starting values: `OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=llama3.1:8b`, `OLLAMA_NUM_CTX=4096`, `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_TEMPERATURE=0`, `OLLAMA_MAX_RETRIES=2`, `OLLAMA_REQUEST_TIMEOUT_S=120`, `OLLAMA_WARMUP_ON_START=true`. They are tuned on the MacBook Air M4 (check `ollama ps`; Slice 0 records the cold and warm timings); the code must fail clearly on a missing required value rather than silently invent one. See `crm-security-env`.

## Sources (read 2026-10-15)

https://docs.ollama.com (structured outputs, FAQ, context length), https://github.com/ollama/ollama (latest release v0.40.5 that day), https://github.com/ollama/ollama-python (0.6.3). Doc pages were read as raw `.md`; the README at tag v0.6.3. Anything not in a snippet is unverified.
