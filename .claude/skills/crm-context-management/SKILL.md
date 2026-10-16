---
name: crm-context-management
description: Context management for the CRM Agents repo - keeping Claude's context small and the codebase navigable, with the external "graphify" tool referenced (pinned, not installed, not copied). Use at the start of a long session, before reading large docs or the whole repo, when context is filling up, or when asked about codebase maps and knowledge graphs.
---

# Context management

## Always true (repeated in every project skill)

- **Everything is real.** Summaries and maps describe real code; never invent files, APIs or behavior to fill a gap, and never write stub code to "keep moving".
- **Ollama is the local fallback** (Phase 1 working system). Context notes must say which path (local or live) a fact applies to.
- **Never read `.env`.** Use `example.env` only. Any indexing or mapping tool must exclude `.env*`, `*.pem`, `*.key` and `.venv/`.
- **`REQUIREMENTS.md` is authoritative.** Cite its IDs instead of paraphrasing it; only `inputs/decisions.md` can override it.

## Habits that keep context small

- Read `REQUIREMENTS.md` and `inputs/decisions.md` at the start; afterwards re-read only the section or ID in question, not the whole file.
- Refer by ID (`FR-SCH-6`, `TR-2`, `R9`) in plans, tests and commits so intent survives summarization.
- Work in thin vertical slices (REQUIREMENTS section 16) with one plan file per slice in `plans/`; finish and commit before opening the next.
- Fetch large docs to the scratchpad directory and read only the lines needed; do not paste whole pages into the conversation. Record in the skill or snippet header only: URL, version, date, status.
- Use forked or fresh subagents for broad research or review so raw tool output stays out of the main context; hand them exact questions and paths, and verify what they report.
- Keep this repo's skills short; long reference text lives in each skill's `snippets/` folder and is opened only when needed.
- When context is compacted, carry forward: current slice and plan path, decisions made this session, open questions for the user, and unverified items.

## Graphify (external, reference only)

- Repo: https://github.com/Graphify-Labs/graphify (the old `safishamsi/graphify` URL in older notes redirects there). PyPI package **`graphifyy`** (double y), **pinned 0.9.91 (released 2026-10-14)**. The repo has **no GitHub releases**; its default branch is `v8`. License: Apache-2.0 and MIT, dual.
- What I verified on 2026-10-15: the GitHub page and PyPI metadata only. Per the page it turns a codebase and docs into a queryable knowledge graph, is installed with `uv tool install graphifyy` (or `pipx`/`pip`), registers an assistant skill with `graphify install`, and is invoked as `/graphify` plus CLI query, path and explain commands. Its README and behavior were **not reviewed**, and nothing is installed or copied here.
- Before anyone installs it: read its README at 0.9.91, check what `graphify install` writes to the machine and project, confirm it can exclude secrets and `.venv/`, and decide. Record the decision in `inputs/decisions.md`. Do not add it to this project's dependencies; it is a developer tool, not application code.
- Useful targets if adopted: the Python backend, `tests/`, `docs/`, `REQUIREMENTS.md`. Exclude `.env*`, keys, `.venv/`, `node_modules/`, `data/synthetic/emails/` (large, synthetic) unless a question needs them.
