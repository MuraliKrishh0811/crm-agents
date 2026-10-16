# Reply draft, send, and message identifiers

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Sources: https://learn.microsoft.com/en-us/graph/api/message-createreply?view=graph-rest-1.0 , https://learn.microsoft.com/en-us/graph/api/message-send?view=graph-rest-1.0 , https://learn.microsoft.com/en-us/graph/api/resources/message?view=graph-rest-1.0
> - Pages last updated (page metadata): 2026-06-19 / 2025-07-23 / 2026-04-20
> - Library version(s): msgraph-sdk 1.64.0 (pinned in inputs/references.md); Graph REST v1.0
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)
>
> Permission names below are what Microsoft documents for this call. The project's permission set and approver are **to be confirmed with IT** (decision D7, deferred). Do not scope permissions in code.
> R5: `send` is called only after an explicit approval action. **TODO:** `In-Reply-To` and `References` are not first-class `message` properties in the table below; whether they are readable through `internetMessageHeaders` (and what `$select` is needed) must be confirmed on the first day with access.

## createReply: permissions (as documented)

```
| Permission type | Least privileged permissions | Higher privileged permissions |
| --- | --- | --- |
| Delegated (work or school account) | Mail.ReadWrite | Not available. |
| Delegated (personal Microsoft account) | Mail.ReadWrite | Not available. |
| Application | Mail.ReadWrite | Not available. |
```

## createReply: HTTP request

```http
POST /me/messages/{id}/createReply
POST /users/{id | userPrincipalName}/messages/{id}/createReply
POST /me/mailFolders/{id}/messages/{id}/createReply
POST /users/{id | userPrincipalName}/mailFolders/{id}/messages/{id}/createReply
```

## createReply: Python SDK

```python

# Code snippets are only available for the latest version. Current version is 1.x
from msgraph import GraphServiceClient
# To initialize your graph_client, see https://learn.microsoft.com/en-us/graph/sdks/create-client?from=snippets&tabs=python

result = await graph_client.me.messages.by_message_id('message-id').create_reply.post(None)
```

## send: permissions (as documented)

```
| Permission type | Least privileged permissions | Higher privileged permissions |
| --- | --- | --- |
| Delegated (work or school account) | Mail.Send | Not available. |
| Delegated (personal Microsoft account) | Mail.Send | Not available. |
| Application | Mail.Send | Not available. |
```

## send: HTTP request

```http
POST /me/messages/{id}/send
POST /users/{id | userPrincipalName}/messages/{id}/send
```

## send: Python SDK

```python

# Code snippets are only available for the latest version. Current version is 1.x
from msgraph import GraphServiceClient
# To initialize your graph_client, see https://learn.microsoft.com/en-us/graph/sdks/create-client?from=snippets&tabs=python

await graph_client.me.messages.by_message_id('message-id').send.post()
```

## message resource: identifier properties (rows copied from the property table)

```
| conversationId | String | The ID of the conversation the email belongs to. |
| id | String | Unique identifier for the message. By default, this value changes when the item is moved from one container (such as a folder or calendar) to another. To change this behavior, use the `Prefer: IdType="ImmutableId"` header. See [Get immutable identifiers for Outlook resources](/en-us/graph/outlook-immutable-id) for more information. Read-only. |
| internetMessageHeaders | [internetMessageHeader](internetmessageheader) collection | A collection of message headers defined by [RFC5322](https://www.ietf.org/rfc/rfc5322.txt). The set includes message headers indicating the network path taken by a message from the sender to the recipient. It can also contain custom message headers that hold app data for the message.  Requires `$select` to retrieve. Read-only. |
| internetMessageId | String | The message ID in the format specified by [RFC2822](https://www.ietf.org/rfc/rfc2822.txt). |
```

