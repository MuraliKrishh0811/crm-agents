# Update event (reschedule / add attendee)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Source: https://learn.microsoft.com/en-us/graph/api/event-update?view=graph-rest-1.0
> - Page last updated (page metadata): 2026-05-19
> - Library version(s): msgraph-sdk 1.64.0 (pinned in inputs/references.md); Graph REST v1.0
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)
>
> Permission names below are what Microsoft documents for this call. The project's permission set and approver are **to be confirmed with IT** (decision D7, deferred). Do not scope permissions in code.
> **TODO:** the page's Python example is a generic PATCH (reminder, categories, online meeting). It does not show a change of `start`/`end` or an `attendees` list. Do not invent one: build the reschedule request from the property table below and verify it on the first day with access (`docs/first_day_with_access.md`).
> **TODO:** on 2026-10-15 I found no documented way to look an event up by `iCalUId` on the event resource, get event, list events and update event pages (the resource page only lists `iCalUId` as a read-only property that differs per occurrence of a recurring series). `CalendarProvider.find_event(event_key)` needs a documented lookup approach before it can be written; mark it UNVERIFIED.

## Permissions table (as documented)

```
| Permission type | Permissions (from least to most privileged) |
| --- | --- |
| Delegated (work or school account) | Calendars.ReadWrite |
| Delegated (personal Microsoft account) | Calendars.ReadWrite |
| Application | Calendars.ReadWrite |
```

## HTTP request

```http
PATCH /me/events/{id}
PATCH /users/{id | userPrincipalName}/events/{id}
PATCH /groups/{id}/events/{id}

PATCH /me/calendar/events/{id}
PATCH /users/{id | userPrincipalName}/calendar/events/{id}
PATCH /groups/{id}/calendar/events/{id}

PATCH /me/calendars/{id}/events/{id}
PATCH /users/{id | userPrincipalName}/calendars/{id}/events/{id}

PATCH /me/calendarGroups/{id}/calendars/{id}/events/{id}
PATCH /users/{id | userPrincipalName}/calendarGroups/{id}/calendars/{id}/events/{id}
```

## Doc notes on attendees, start and end

> - **attendees** property and meeting updates
>
>     - An event update that includes only the **attendees** property in the request body sends a meeting update to only the attendees that have changed.
>     - An event update that removes an attendee specified as a member of a distribution list sends a meeting update to all the attendees.
> - **body** property and online meetings
>
>     Before updating the body of an event that has been set up as an online meeting, be sure to first get the **body** property, apply the appropriate changes to the content, and preserve the meeting blob for online meeting. Inadvertently removing the meeting blob from the body would disable meeting online.
> - **end** and **start** properties and their time zones
>
>     When updating the time zone of the start or end time of an event, first [find the supported time zones](outlookuser-supportedtimezones) to make sure you set only time zones that have been configured for the user's mailbox server.

## Python SDK (the docs' generic example)

```python

# Code snippets are only available for the latest version. Current version is 1.x
from msgraph import GraphServiceClient
from msgraph.generated.models.event import Event
from msgraph.generated.models.response_status import ResponseStatus
from msgraph.generated.models.response_type import ResponseType
from msgraph.generated.models.online_meeting_provider_type import OnlineMeetingProviderType
# To initialize your graph_client, see https://learn.microsoft.com/en-us/graph/sdks/create-client?from=snippets&tabs=python
request_body = Event(original_start_time_zone = "originalStartTimeZone-value",original_end_time_zone = "originalEndTimeZone-value",response_status = ResponseStatus(	response = ResponseType.None,	time = "datetime-value",),recurrence = None,reminder_minutes_before_start = 99,is_online_meeting = True,online_meeting_provider = OnlineMeetingProviderType.TeamsForBusiness,is_reminder_on = True,hide_attendees = False,categories = [	"Red category",],
)

result = await graph_client.me.events.by_event_id('event-id').patch(request_body)
```

