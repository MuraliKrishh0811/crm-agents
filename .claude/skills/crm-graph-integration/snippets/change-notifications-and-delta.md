# Change notifications (subscriptions), renewal, and message delta

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Sources: https://learn.microsoft.com/en-us/graph/api/subscription-post-subscriptions , https://learn.microsoft.com/en-us/graph/api/resources/subscription (Subscription lifetime) , https://learn.microsoft.com/en-us/graph/api/subscription-update , https://learn.microsoft.com/en-us/graph/api/message-delta (all ?view=graph-rest-1.0)
> - Pages last updated (page metadata): 2026-04-07 / 2026-09-17 / 2026-08-04 / 2026-06-19
> - Library version(s): msgraph-sdk 1.64.0 (pinned in inputs/references.md); Graph REST v1.0
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)
>
> Permission names below are what Microsoft documents for this call. The project's permission set and approver are **to be confirmed with IT** (decision D7, deferred). Do not scope permissions in code.
> The lifetime below is the maximum Graph documents for Outlook message subscriptions (10,080 minutes, under seven days; 1,440 minutes for rich notifications). Renew on a timer well before expiry. The notification endpoint needs a public HTTPS URL, which is a hosting question (D8, deferred).

## Subscription create: permissions rows for message and event (Delegated work/school | Delegated personal | Application)

```
| Supported resource | Delegated (work or school account) | Delegated (personal Microsoft account) | Application |
| --- | --- | --- | --- |
| [event](resources/event) | Calendars.Read | Calendars.Read | Calendars.Read |
| [message](resources/message) | Mail.ReadBasic, Mail.Read | Mail.ReadBasic, Mail.Read | Mail.Read |
```

## Subscription create: example request (HTTP)

```http
POST https://graph.microsoft.com/v1.0/subscriptions
Content-type: application/json

{
   "changeType": "created",
   "notificationUrl": "https://webhook.azurewebsites.net/api/send/myNotifyClient",
   "resource": "me/mailFolders('Inbox')/messages",
   "expirationDateTime":"2016-11-20T18:23:45.9356913Z",
   "clientState": "secretClientValue",
   "latestSupportedTlsVersion": "v1_2"
}
```

## Subscription create: Python SDK

```python

# Code snippets are only available for the latest version. Current version is 1.x
from msgraph import GraphServiceClient
from msgraph.generated.models.subscription import Subscription
# To initialize your graph_client, see https://learn.microsoft.com/en-us/graph/sdks/create-client?from=snippets&tabs=python
request_body = Subscription(change_type = "created",notification_url = "https://webhook.azurewebsites.net/api/send/myNotifyClient",resource = "me/mailFolders('Inbox')/messages",expiration_date_time = "2016-11-20T18:23:45.9356913Z",client_state = "secretClientValue",latest_supported_tls_version = "v1_2",
)

result = await graph_client.subscriptions.post(request_body)
```

## Subscription create: example response

```http
HTTP/1.1 201 Created
Content-type: application/json

{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#subscriptions/$entity",
  "id": "7f105c7d-2dc5-4530-97cd-4e7ae6534c07",
  "resource": "me/mailFolders('Inbox')/messages",
  "applicationId": "24d3b144-21ae-4080-943f-7067b395b913",
  "changeType": "created",
  "clientState": "secretClientValue",
  "notificationUrl": "https://webhook.azurewebsites.net/api/send/myNotifyClient",
  "expirationDateTime": "2016-11-20T18:23:45.9356913Z",
  "creatorId": "8ee44408-0679-472c-bc2a-692812af3437",
  "latestSupportedTlsVersion": "v1_2",
  "notificationContentType": "application/json"
}
```

## Subscription lifetime (Outlook row)

```
| Resource | Maximum expiration time |
| --- | --- |
| Outlook [message](/en-us/graph/api/resources/message), [event](/en-us/graph/api/resources/event), [contact](/en-us/graph/api/resources/contact) | 10,080 minutes (under seven days) For subscriptions with resource data (rich notification subscriptions), subscription lifetime is 1440 minutes (under one day). |
```

## Duplicate subscription behavior (docs)

> Duplicate subscriptions aren't allowed. When a subscription request contains the same values for **changeType** and **resource** that an existing subscription contains, the request fails with an HTTP error code `409 Conflict`.

## Subscription renew (update): HTTP request

```http
PATCH /subscriptions/{id}
```

## Subscription renew (update): Python SDK

```python

# Code snippets are only available for the latest version. Current version is 1.x
from msgraph import GraphServiceClient
from msgraph.generated.models.subscription import Subscription
# To initialize your graph_client, see https://learn.microsoft.com/en-us/graph/sdks/create-client?from=snippets&tabs=python
request_body = Subscription(expiration_date_time = "2016-11-22T18:23:45.9356913Z",
)

result = await graph_client.subscriptions.by_subscription_id('subscription-id').patch(request_body)
```

## Message delta: permissions (as documented)

```
| Permission type | Least privileged permissions | Higher privileged permissions |
| --- | --- | --- |
| Delegated (work or school account) | Mail.ReadBasic | Mail.Read, Mail.ReadWrite |
| Delegated (personal Microsoft account) | Mail.ReadBasic | Mail.Read, Mail.ReadWrite |
| Application | Mail.ReadBasic.All | Mail.Read, Mail.ReadWrite |
```

## Message delta: Python SDK

```python

# Code snippets are only available for the latest version. Current version is 1.x
from msgraph import GraphServiceClient
from msgraph.generated.users.item.mail_folders.item.messages.delta.delta_request_builder import DeltaRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
# To initialize your graph_client, see https://learn.microsoft.com/en-us/graph/sdks/create-client?from=snippets&tabs=python

request_configuration = RequestConfiguration()
request_configuration.headers.add("Prefer", "odata.maxpagesize=2")

result = await graph_client.me.mail_folders.by_mail_folder_id('mailFolder-id').messages.delta.get(request_configuration = request_configuration)
```

