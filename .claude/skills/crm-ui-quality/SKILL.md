---
name: crm-ui-quality
description: UI quality rules for the CRM Agents React + Vite + TypeScript dashboard (pipeline, customer detail, scheduling panel with approve/edit/reject, audit view) and the reference to the external "taste skill" (pinned, not copied). Use when designing, building, reviewing or testing any frontend screen.
---

# UI quality

## Always true (repeated in every project skill)

- **Everything is real.** The UI talks to the real CRM API and shows real agent output. No mocked endpoints, canned data, placeholder responses or hardcoded demo content in shipped code.
- **Ollama is the local fallback.** In Phase 1 the data the UI shows comes from local mode (Ollama, `.eml`, mock calendar); the UI says so (see "Show provenance").
- **Never read `.env`.** Use `example.env` only; the frontend receives no secrets.
- **`REQUIREMENTS.md` is authoritative** (sections 7 FR-UI and FR-API). Only `inputs/decisions.md` can override it.

## Stack and scope

React with Vite and TypeScript (D2). One CRM API serves the web dashboard and, later, the Teams Copilot agent (D6, after the dashboard), so the UI contains no business logic that the Teams agent would also need.

Screens (all required for Phase 1):

- **Pipeline** (FR-UI-1): customers grouped by the five stages.
- **Customer detail** (FR-UI-2): stage and stage history, contacts, engagement timeline (emails and meetings), next action.
- **Scheduling panel** (FR-UI-3): parsed customer windows, availability results with the reason for every accepted and rejected slot, proposed slots, draft reply, approve / edit / reject.
- **Audit view** (FR-UI-4): what each agent decided, with provider and model.

## Taste skill (external, reference only)

- Repo: https://github.com/Leonxlnx/taste-skill, **pinned release v2.0.0 (published 2026-10-13), commit `f624f37a8c650b9cc550253104925efe4c8de246` (2026-10-14)**, MIT license.
- What I verified on 2026-10-15: the GitHub page and release/commit metadata only. Its skill contents were **not reviewed**. `inputs/references.md` says "Reference only", so nothing is installed or copied here.
- Per its page, installation is `npx skills add https://github.com/Leonxlnx/taste-skill` or as a Claude Code plugin; the default skill needs Node 22+ and Chrome/Edge/Chromium, and fetches reference images over the network.
- Before anyone installs it: read its `SKILL.md` files at the pinned commit (third-party instructions run with Claude's authority), then decide. Record the decision in `inputs/decisions.md`. When it is used, apply it to the visual layer only; the rules below still win.

## Product rules the UI must follow

- **Approval is an explicit human action** (R5, FR-APP-1 to 3): approve, edit, reject are separate controls; nothing is sent or booked on load, on edit, or by default. **Edit changes only the draft reply text** (not times or attendees), is recorded as an audit entry and leaves the request state unchanged (decisions.md OQ-4). Approving names exactly one proposed slot; a tentative fallback is listed last with its warning. Show attendees, slot(s) and the full draft before the action; record who and when (`decided_by`, `decided_at`). Phase 1 has no login screen: the approver is a configured local user name (decisions.md OQ-13), shown on the decision. The dashboard fetches the per-run token from the API and sends it with every write (`docs/api.md` section 10.1, TR-13); never store it in `localStorage`, files or logs.
- **Show request state and approval progress**: the seven states (`pending`, `approved`, `rejected`, `superseded`, `cancelled`, `expired`, `needs_review`, FR-SCH-12); for `needs_review` show that nothing was booked and the fresh options (FR-APP-4); show the approval progress (`not_started`, `in_progress`, `completed`, `partially_completed`, requirements section 9); for a `partially_completed` approval show the failed step and a retry control (FR-APP-5); show a meeting's customer response as "not available (simulated)" when it is `null` (OQ-8, R10); after a rejection show state `rejected` and nothing else happening (OQ-26); keep superseded, cancelled and expired requests viewable as history.
- **Show times with their zone**: every time carries its IANA zone label; scheduling shows the customer's zone and the organization zone side by side (R9). Never present a bare offset.
- **Show warnings, never hide them**: tentative-attendee fallbacks carry a visible warning; rejected slots show their reasons.
- **Show provenance and simulation** (R10): simulated join links, local-mode data, and `implemented, unverified` live providers are labeled in the UI; the audit view shows provider and model per run.
- States: loading, empty, error and partial-failure states for every list (the pipeline may continue past a failed email; show the failure from the audit log).
- Treat email content as untrusted: render plain text or sanitized HTML only, never raw HTML from an `.eml` (XSS).
- Accessibility and layout: keyboard-reachable controls, visible focus, sufficient contrast, labels not color-only, responsive down to a laptop split screen.

## Verify in a real browser

Do not report a UI task done from type checks or unit tests alone. Start the dev server and the local backend, exercise the golden path and edge cases (empty pipeline, failed run, rejected slot, edited draft), and run the Playwright scripts in `tests/frontend/` (TR-5; see `crm-testing-smoke`). If the UI cannot be run, say so explicitly.
