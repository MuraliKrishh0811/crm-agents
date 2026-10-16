# calendar: getSchedule (internal free/busy)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Source: https://learn.microsoft.com/en-us/graph/api/calendar-getschedule?view=graph-rest-1.0
> - Page last updated (page metadata): 2026-05-19
> - Library version(s): msgraph-sdk 1.64.0 (pinned in inputs/references.md); Graph REST v1.0
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)
>
> Permission names below are what Microsoft documents for this call. The project's permission set and approver are **to be confirmed with IT** (decision D7, deferred). Do not scope permissions in code.
> Note from the page: `workingElsewhere` and `free` are both `0` in `availabilityView`; `tentative` is `1`; `busy` is `2`; `oof` is `3`. Our rules (REQUIREMENTS section 8) use `scheduleItems[].status`, not `availabilityView`, so `free` and `workingElsewhere` stay non-blocking and `tentative` stays soft.

## Permissions table (as documented)

```
| Permission type | Least privileged permissions | Higher privileged permissions |
| --- | --- | --- |
| Delegated (work or school account) | Calendars.ReadBasic | Calendars.Read, Calendars.ReadWrite |
| Delegated (personal Microsoft account) | Not supported. | Not supported. |
| Application | Calendars.ReadBasic | Calendars.Read, Calendars.ReadWrite |
```

## HTTP request

```http
POST /me/calendar/getSchedule
POST /users/{id|userPrincipalName}/calendar/getSchedule
```

## Request body

```
| Property | Type | Description |
| --- | --- | --- |
| availabilityViewInterval | Int32 | Represents the duration of a time slot in an **availabilityView** in the response. The default is 30 minutes, minimum is 5, maximum is 1440. Optional. |
| endTime | [dateTimeTimeZone](resources/datetimetimezone) | The date, time, and time zone that the period ends. |
| schedules | String collection | A collection of SMTP addresses of users, distribution lists, or resources to get availability information for. |
| startTime | [dateTimeTimeZone](resources/datetimetimezone) | The date, time, and time zone that the period starts. |
```

## Example request

```http
POST https://graph.microsoft.com/v1.0/me/calendar/getSchedule
Prefer: outlook.timezone="Pacific Standard Time"
Content-Type: application/json

{
    "schedules": ["adelev@contoso.com", "meganb@contoso.com"],
    "startTime": {
        "dateTime": "2019-03-15T09:00:00",
        "timeZone": "Pacific Standard Time"
    },
    "endTime": {
        "dateTime": "2019-03-15T18:00:00",
        "timeZone": "Pacific Standard Time"
    },
    "availabilityViewInterval": 60
}
```

## Python SDK

```python

# Code snippets are only available for the latest version. Current version is 1.x
from msgraph import GraphServiceClient
from msgraph.generated.users.item.calendar.get_schedule.get_schedule_request_builder import GetScheduleRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.users.item.calendar.get_schedule.get_schedule_post_request_body import GetSchedulePostRequestBody
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
# To initialize your graph_client, see https://learn.microsoft.com/en-us/graph/sdks/create-client?from=snippets&tabs=python
request_body = GetSchedulePostRequestBody(schedules = [	"adelev@contoso.com",	"meganb@contoso.com",],start_time = DateTimeTimeZone(	date_time = "2019-03-15T09:00:00",	time_zone = "Pacific Standard Time",),end_time = DateTimeTimeZone(	date_time = "2019-03-15T18:00:00",	time_zone = "Pacific Standard Time",),availability_view_interval = 60,
)

request_configuration = RequestConfiguration()
request_configuration.headers.add("Prefer", "outlook.timezone=\"Pacific Standard Time\"")

result = await graph_client.me.calendar.get_schedule.post(request_body, request_configuration = request_configuration)
```

## Example response

```http
HTTP/1.1 200 OK
Content-type: application/json

{
    "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(microsoft.graph.scheduleInformation)",
    "value": [
        {
            "scheduleId": "adelev@contoso.com",
            "availabilityView": "000220130",
            "scheduleItems": [
                {
                    "isPrivate": false,
                    "status": "busy",
                    "subject": "Let's go for lunch",
                    "location": "Harry's Bar",
                    "start": {
                        "dateTime": "2019-03-15T12:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T14:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                },
                {
                    "subject": "free is represented by 0 in availabilityView",
                    "status": "free",
                    "start": {
                        "dateTime": "2019-03-15T10:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T11:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                },
                {
                    "subject": "workingElsewhere is also represented by 0 in availabilityView",
                    "status": "workingElsewhere",
                    "start": {
                        "dateTime": "2019-03-15T11:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T12:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                },
                {
                    "subject": "tentative is represented by 1 in availabilityView",
                    "status": "tentative",
                    "start": {
                        "dateTime": "2019-03-15T15:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T16:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                },
                {
                    "subject": "oof is represented by 3 in availabilityView",
                    "status": "workingElsewhere",
                    "start": {
                        "dateTime": "2019-03-15T16:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T17:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                }
            ],
            "workingHours": {
                "daysOfWeek": [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday"
                ],
                "startTime": "08:00:00.0000000",
                "endTime": "17:00:00.0000000",
                "timeZone": {
                    "name": "Pacific Standard Time"
                }
            }
        },
        {
            "scheduleId": "meganb@contoso.com",
            "availabilityView": "200120010",
            "scheduleItems": [
                {
                    "status": "busy",
                    "start": {
                        "dateTime": "2019-03-15T08:30:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T09:30:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                },
                {
                    "subject": "tentative is represented by 1 and overwritten by the busy-appointment (2) starting from 12 to 13.",
                    "status": "tentative",
                    "start": {
                        "dateTime": "2019-03-15T12:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T14:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                },
                {
                    "status": "busy",
                    "start": {
                        "dateTime": "2019-03-15T12:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T13:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                },
                {
                    "status": "busy",
                    "start": {
                        "dateTime": "2019-03-15T13:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T14:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                },
                {
                    "status": "tentative",
                    "start": {
                        "dateTime": "2019-03-15T16:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    },
                    "end": {
                        "dateTime": "2019-03-15T17:00:00.0000000",
                        "timeZone": "Pacific Standard Time"
                    }
                }
            ],
            "workingHours": {
                "daysOfWeek": [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday"
                ],
                "startTime": "08:00:00.0000000",
                "endTime": "17:00:00.0000000",
                "timeZone": {
                    "@odata.type": "#microsoft.graph.customTimeZone",
                    "bias": 480,
                    "name": "Customized Time Zone",
                    "standardOffset": {
                        "time": "02:00:00.0000000",
                        "dayOccurrence": 1,
                        "dayOfWeek": "sunday",
                        "month": 11,
                        "year": 0
                    },
                    "daylightOffset": {
                        "daylightBias": -60,
                        "time": "02:00:00.0000000",
                        "dayOccurrence": 2,
                        "dayOfWeek": "sunday",
                        "month": 3,
                        "year": 0
                    }
                }
            }
        }
    ]
}
```

