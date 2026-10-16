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
2. `getSchedule`: `scheduleItems[].status` values and `workingHours` as documented; behavior with more than 1000 entries.
3. Create event as a Teams meeting: where the join link appears, and how `transactionId` behaves on retry (idempotency, R6).
4. Look up an event by `iCalUId` (no documented method found on 2026-10-15; needed for `find_event`).
5. Reschedule PATCH body (`start`, `end`, `attendees`) and which `timeZone` names create/update accept (IANA vs Windows names, R9).
6. Read `In-Reply-To` and `References` (via `internetMessageHeaders`?) and the `$select` needed (FR-ING-3); `internetMessageId` and `conversationId` mapping.
7. Reply draft via `createReply`, then `send` only after approval (R5).
8. Customer response tracking: meeting-response messages vs attendee response status.
9. Immutable IDs (`Prefer: IdType="ImmutableId"`) vs our stable event key.
10. Foundry or Azure OpenAI: structured output (`response_format`) with the chosen client, retries and timeouts, tracing to App Insights or Foundry.
11. Imports and behavior of the pinned set (`agent-framework-core` 1.22.0, `agent-framework-foundry` 1.15.0, `agent-framework-openai` 1.17.0, `azure-identity` 1.26.0, `ollama` 0.6.3, `msgraph-sdk` 1.64.0). A pip dry-run on 2026-10-16 resolved this set with no conflicts (details in `.claude/skills/crm-agent-framework-azure-openai/SKILL.md`), but it was not installed or imported. Never install the `agent-framework` meta-package (it pulls in `agent-framework-ollama`, which requires `ollama<0.5.4`).
