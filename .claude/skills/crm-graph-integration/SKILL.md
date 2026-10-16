---
name: crm-graph-integration
description: Microsoft Graph integration for the live MailProvider and CalendarProvider - which documented call backs each interface method, subscriptions and delta, getSchedule, Teams event create/update, reply and send. EVERYTHING IS UNVERIFIED until real tenant access exists; Graph permission set is to be confirmed with IT (D7). Use when writing, reviewing or contract-testing any Graph code.
---

# Microsoft Graph integration (ALL UNVERIFIED)

## Always true (repeated in every project skill)

- **Everything is real.** Graph adapters are real implementations written from current docs. No mocking, stubs, canned or hardcoded responses, no hardcoded snippets standing in for behavior.
- **Ollama is the local fallback.** Phase 1 runs on `.eml` files, mock calendar JSON and Ollama; Graph is off by default and refuses to start without configuration (R3).
- **`.env` (R7):** Claude never opens, prints, searches or copies a `.env*` file; use `example.env` only. The application's own settings loader may read `.env` when tests or smoke runs execute (Phase 1, no real secrets); it never prints values.
- **`REQUIREMENTS.md` is authoritative** (section 12). `inputs/decisions.md` records owner decisions where it is silent.

## Status: UNVERIFIED

No Microsoft 365 or Entra access exists in Phase 1. Every call, shape, limit and permission below was read from docs on 2026-10-15 and has **never been exercised**. Label code `implemented, unverified`. Do not claim Graph behavior is verified (section 18). Contract tests (TR-7) use sample responses shaped like real output and are labeled contract tests. Library: `msgraph-sdk` 1.64.0 (pinned); REST v1.0; the SDK client is async (docs snippets use `await`).

## Permissions: TO BE CONFIRMED WITH IT (D7, deferred)

The permission set, app-only vs delegated split, and approver are decided with IT when live access is requested. **Do not invent a permission set and do not scope permissions in code.** Each snippet file quotes the permission names Microsoft documents for that one call, as reference only; the union of those is not a decision. Needs are recorded as "to be confirmed" in `docs/first_day_with_access.md`.

## Interface method to documented Graph call

| Interface method | Graph call (docs) | Snippet |
|---|---|---|
| `list_new_messages(since)` | change-notification subscription on the Inbox, plus message delta as a polling safety net; renew subscriptions on a timer | [change-notifications-and-delta.md](snippets/change-notifications-and-delta.md) |
| `get_message(id)` | get message; map `internetMessageId` and `conversationId` to our keys | [mail-reply-send-identifiers.md](snippets/mail-reply-send-identifiers.md) |
| `create_reply_draft` / `send_draft` | `createReply` draft, then `send` only after approval (R5) | same file |
| `get_availability` | `calendar/getSchedule`; intersect in code (R4), never `findMeetingTimes` for decisions | [get-schedule.md](snippets/get-schedule.md) |
| `create_event` | create event with `isOnlineMeeting` and `teamsForBusiness` (join link comes from the response) | [create-event-teams-meeting.md](snippets/create-event-teams-meeting.md) |
| `update_event` | PATCH event (move time, add attendee) | [update-event.md](snippets/update-event.md) |
| `find_event` | **no documented iCalUId lookup found** (TODO below) | |
| `find_events` (D11, FR-SCH-9) | `GET /users/{id}/calendarView?startDateTime=&endDateTime=` returns event objects (event resource has `attendees` and `iCalUId`); whether `attendees` is returned without `$select`, and whether `Calendars.ReadBasic` includes it, are **UNVERIFIED**; address matching is done in our code | [calendar-view-events.md](snippets/calendar-view-events.md) |
| client/auth | credential + `GraphServiceClient` | [auth-and-client.md](snippets/auth-and-client.md) |

## Findings from the 2026-10-15 read

- **Subscription lifetime:** Outlook message/event/contact subscriptions max 10,080 minutes (under 7 days); 1,440 minutes with resource data. Anything under 45 minutes is bumped to 45. Duplicate (same changeType and resource) returns 409. The notification endpoint must answer a validation request, so it needs a public HTTPS URL (hosting is deferred, D8). Use `clientState` from config to check notification origin.
- **getSchedule status values:** `free` and `workingElsewhere` map to 0, `tentative` to 1, `busy` 2, `oof` 3 in `availabilityView`. Use `scheduleItems[].status` so our section 8 rules (hard: busy/oof; soft: tentative; non-blocking: free/workingElsewhere) stay exact. The response also carries `workingHours` per user. One page note: more than 1000 calendar entries in a slot returns error 5006. In live mode the per-user `workingHours` in this response are where working hours would come from (decisions.md OQ-6; UNVERIFIED), and the live adapter returns them as `working_hours` next to `busy_blocks` from `get_availability` (REQUIREMENTS section 6; decisions.md OQ-28). Whether `getSchedule`'s `workingHours` (including its time zone) is usable for that is on the first-day checklist.
- **Time zones (R9):** `dateTimeTimeZone.timeZone` examples use Windows names ("Pacific Standard Time"). The page also lists IANA-style names (for example `America/Chicago`) under "Additional time zones" but warns create/update "might not support all". TODO first day: confirm which names create/update accept; until then keep UTC plus IANA internally and convert at the adapter edge, never with a fixed offset.
- **Mail authentication scoping:** the Exchange doc reached from the Graph page `auth-limit-mailbox-access` states **"RBAC for Applications replaces Application Access Policies"**. REQUIREMENTS section 12 now says to use Exchange Online's current mailbox-scoping mechanism for app permissions (Microsoft's docs describe RBAC for Applications) and to confirm it with IT. Follow that wording; do not name an access policy in code or docs. Final auth plan is with IT (D7).

## TODO (do not write from memory; verify on the first day with access)

1. Lookup of an event by `iCalUId` (needed for `find_event`, R6). Not found on the event resource, get, list or update pages. (`find_events` does not need it: it lists a time range with `calendarView`; see snippet and its TODO list, read 2026-10-16.)
2. A documented PATCH body for reschedule (`start`, `end`, `attendees`); the update page's Python example is generic.
3. How `transactionId` behaves on create retries (idempotency).
4. Whether `In-Reply-To` and `References` are readable via `internetMessageHeaders` and the `$select` needed (FR-ING-3).
5. Customer response tracking: meeting-response messages vs attendee response status (REQUIREMENTS section 12; not yet researched).
6. Accepted `timeZone` names for create/update; app-only vs delegated for each call.
7. Outlook immutable IDs (`Prefer: IdType="ImmutableId"`) vs our event key; mailbox `id` changes when an item moves.

## Rules for the code

Disabled by default; refuse to start without config (tenant, client, auth settings from config, never literals); record `provider=graph` in every audit entry; retries with limits; never write secrets to logs; ship `docs/first_day_with_access.md` listing exactly what to verify.

## Sources (read 2026-10-15)

https://learn.microsoft.com/en-us/graph/ and the per-call pages named in each snippet header (with page dates). Excerpts are reference API shape only.
