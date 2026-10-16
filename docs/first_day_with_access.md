# First day with access: what to verify

Status: draft started 2026-10-15 while writing the project skills. Nothing here has been verified. Every live provider is `implemented, unverified` until each item below is checked against a real tenant. Add the date and result beside each item as it is verified.

## 1. Decisions to make with IT (D7, D8 deferred)

| Item | Status |
|---|---|
| Microsoft Graph permission set (per call, app-only vs delegated) | **To be confirmed with IT.** Do not scope permissions in code. Microsoft's documented per-call permission names are quoted in `.claude/skills/crm-graph-integration/snippets/` as reference only |
| Approver for admin consent | To be confirmed with IT |
| Mailbox scoping for app-only access | To be confirmed with IT. Microsoft's Exchange docs describe RBAC for Applications as replacing Application Access Policies; REQUIREMENTS section 12 now says to confirm the current mechanism with IT |
| Public HTTPS notification URL for Graph subscriptions | Depends on hosting (D8) |

## 2. Which live model client we use

**It depends on what IT provisions:**

- A **Foundry project endpoint** (`https://<account>.services.ai.azure.com/api/projects/<project>`): use `FoundryChatClient` (first choice).
- A standalone **Azure OpenAI resource endpoint** (`https://<resource>.openai.azure.com`): use `agent_framework.openai` clients with Azure routing (second choice).

Record the choice here once known. Both are UNVERIFIED. Also confirm: the model or deployment name, API version, and the production credential type (managed identity preferred; `AzureCliCredential` in doc snippets is for development). See `.claude/skills/crm-agent-framework-azure-openai/SKILL.md`.

## 3. To verify against the real service

1. Subscription on the Inbox: validation handshake, `clientState`, renewal before the documented 10,080-minute maximum, 409 on duplicates, delta polling as a safety net.
2. `getSchedule`: `scheduleItems[].status` values and `workingHours` as documented; behavior with more than 1000 entries. Per `decisions.md` (OQ-6) live working hours come per user from Graph; confirm the returned `workingHours` (including time zone) is usable for capping windows and can be returned from `get_availability` as `working_hours` next to the busy blocks (REQUIREMENTS section 6; hld.md OQ-28, resolved).
3. Create event as a Teams meeting: where the join link appears, and how `transactionId` behaves on retry (idempotency, R6).
4. Look up an event by `iCalUId` (no documented method found on 2026-10-15; needed for `find_event`). For `find_events` (FR-SCH-9, D11) the candidate call is `GET /users/{id}/calendarView` (read 2026-10-16, UNVERIFIED; see item 17).
5. Reschedule PATCH body (`start`, `end`, `attendees`) and which `timeZone` names create/update accept (IANA vs Windows names, R9).
6. Read `In-Reply-To` and `References` (via `internetMessageHeaders`?) and the `$select` needed (FR-ING-3); `internetMessageId` and `conversationId` mapping.
7. Reply draft via `createReply`, then `send` only after approval (R5).
8. Customer response tracking: meeting-response messages vs attendee response status.
9. Immutable IDs (`Prefer: IdType="ImmutableId"`) vs our stable event key.
10. Foundry or Azure OpenAI: structured output (`response_format`) with the chosen client, retries and timeouts, tracing to App Insights or Foundry.
11. Imports and behavior of the pinned set (`agent-framework-core` 1.22.0, `agent-framework-foundry` 1.15.0, `agent-framework-openai` 1.17.0, `azure-identity` 1.26.0, `ollama` 0.6.3, `msgraph-sdk` 1.64.0). A pip dry-run on 2026-10-16 resolved this set with no conflicts (details in `.claude/skills/crm-agent-framework-azure-openai/SKILL.md`), but it was not installed or imported. Never install the `agent-framework` meta-package (it pulls in `agent-framework-ollama`, which requires `ollama<0.5.4`).
12. Sent Items (FR-ING-7): how sent mail is detected and read (subscription or delta on the Sent Items folder). Not researched yet; the skills only cover the Inbox.
13. Contract tests (TR-7): compare the sample responses used by the contract tests with real service responses and correct them. Until then they are shaped from documentation only.
14. How the approver is identified (FR-APP-3) against a real tenant. Phase 1 uses a configured local approver recorded as `decided_by` (decided, hld.md OQ-13), protected by the localhost measures in `docs/api.md` section 10.1 (127.0.0.1 only, Host and Origin checks, CORS limited to the dashboard origin, JSON content type, per-run token). The Entra ID design in `docs/api.md` section 10.2 is UNVERIFIED and was not checked against Entra ID documentation. Verify token validation, mapping the token identity to `decided_by` (a team member), who may approve (with IT, D7), whether the per-run token is still needed, and the Teams agent's on-behalf-of call.
15. Teams Copilot agent (FR-UI-5, D6, after the dashboard): Microsoft 365 Agents Toolkit and how it authenticates to the CRM API. Not researched yet.
16. Phase 1 local decisions that real behavior may confirm or change (hld.md section 12.1): customer response status on events (OQ-8, `null` locally), the meeting key used for local versus live meetings (OQ-9, derived from the request id locally and the iCalUId from Graph live), `getSchedule` behavior over long date ranges and dates outside the calendar data (OQ-15), and creating the reply draft with `createReply` at approval time rather than earlier (OQ-25).
17. `find_events` (FR-SCH-9, D11): confirm the Graph `calendarView` call returns `attendees` and `iCalUId` for each event in a time range, and whether `attendees` needs `$select`; whether the documented least-privileged permission `Calendars.ReadBasic` includes attendees (with IT, D7); paging (`@odata.nextLink`); whether canceled events appear (`isCancelled`); that the same meeting on several attendees' calendars shares one `iCalUId` and a recurring series has a different one per occurrence. Source and open points: `.claude/skills/crm-graph-integration/snippets/calendar-view-events.md`.
