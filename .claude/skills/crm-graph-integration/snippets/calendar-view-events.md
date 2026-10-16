# calendar: calendarView (events with attendees and iCalUId, for `find_events`)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Sources (all read 2026-10-16):
>   - https://learn.microsoft.com/en-us/graph/api/user-list-calendarview?view=graph-rest-1.0 (page `updated_at` 2026-06-19)
>   - https://learn.microsoft.com/en-us/graph/api/resources/event?view=graph-rest-1.0 (page `updated_at` 2026-04-20)
>   - https://learn.microsoft.com/en-us/graph/api/user-list-events?view=graph-rest-1.0 (page `updated_at` 2025-07-23)
>   - https://learn.microsoft.com/en-us/graph/api/event-get?view=graph-rest-1.0 (sample response with `iCalUId`)
> - Library version(s): msgraph-sdk 1.64.0 (pinned in inputs/references.md); Graph REST v1.0
> - Status: **UNVERIFIED**. Copied from current docs and never executed against a live service. Used by the live `CalendarProvider.find_events(users, attendee_addresses, start, end)` (REQUIREMENTS section 6, FR-SCH-9, decisions.md D11).
>
> Permission names below are what Microsoft documents for this call. The project's permission set and approver are **to be confirmed with IT** (decision D7, deferred). Do not scope permissions in code.

## What the docs say (verbatim facts)

- **Request** (user calendar view in the default calendar):
  `GET /users/{id | userPrincipalName}/calendarView?startDateTime={start_datetime}&endDateTime={end_datetime}`
  (also `GET /me/calendar/calendarView?...`, and per-calendar forms `/calendars/{id}/calendarView?...`).
- **What it returns:** "Get the occurrences, exceptions, and single instances of events in a calendar view defined by a time range". Success: `200 OK` with a "collection of event objects".
- **Time range:** `startDateTime` and `endDateTime` are required, ISO 8601, interpreted with the offset in the value; with no offset they are read as UTC.
- **Time zone of the result:** `Prefer: outlook.timezone` sets it; if absent, start and end are returned in UTC.
- **Properties:** the `event` resource has `attendees` ("Attendee collection"), `iCalUId` ("A unique identifier for an event across calendars. This ID is different for each occurrence in a recurring series. Read-only."), `isCancelled` ("Set to true if the event has been canceled."), `start`, `end`, `subject`. The calendarView sample response on that page shows `iCalUId`; it does **not** show `attendees`.
- **Which properties come back:** the **list events** and **get event** pages say "Without a $select parameter, all of the event properties are returned". The **calendarView** page does not say this. It says the method "supports some of the OData Query Parameters" and notes `createdDateTime` and `lastModifiedDateTime` "don't support $select".
- **Permissions (as documented for calendarView):** least privileged `Calendars.ReadBasic` for delegated (work or school), delegated (personal) and application; higher privileged `Calendars.Read`, `Calendars.ReadWrite`.
- **Python SDK example on the page** (uses `me`, not a user id):

```python
# Code snippets are only available for the latest version. Current version is 1.x
from msgraph import GraphServiceClient
from msgraph.generated.users.item.calendar_view.calendar_view_request_builder import CalendarViewRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration

query_params = CalendarViewRequestBuilder.CalendarViewRequestBuilderGetQueryParameters(
    start_date_time = "2020-01-01T19:00:00-08:00",
    end_date_time = "2020-01-02T19:00:00-08:00",
)
request_configuration = RequestConfiguration(
    query_parameters = query_params,
)
result = await graph_client.me.calendar_view.get(request_configuration = request_configuration)
```

## Not confirmed (TODO, first-day checklist)

1. Whether calendarView returns `attendees` **without** `$select`, or only when `attendees` is named in `$select` (the calendarView page is silent; list events and get event say all properties return without `$select`).
2. Whether `Calendars.ReadBasic` (the documented least-privileged permission) includes `attendees`; if not, a higher permission is needed (D7, with IT).
3. The Python form for another user: `graph_client.users.by_user_id(...).calendar_view.get(...)` is the pattern used on other Graph pages but is **not shown on this page**.
4. Paging: the page does not mention `@odata.nextLink` or a page size; check before relying on a single response.
5. Whether canceled events appear in a calendar view; `isCancelled` exists, so the adapter filters in code (FR-SCH-9: non-cancelled only).
6. No documented server-side filter on attendee address was found on these pages; matching an external attendee address against the trigger email's addresses is done in our code, not in the query.
7. The `iCalUId` value differs per occurrence in a recurring series (documented); the same meeting on several attendees' calendars shares one `iCalUId` (consistent with the mock data), so events are de-duplicated by `iCalUId`.
8. Why not `getSchedule` for this: its documented sample returns only status, times and subject per item, no attendees and no `iCalUId` (see [get-schedule.md](get-schedule.md)).
9. List events (`GET /users/{id}/events`) was read but not evaluated for this purpose; calendarView is the call the docs describe as returning occurrences, exceptions and single instances within a time range, which is what "upcoming events" needs.
