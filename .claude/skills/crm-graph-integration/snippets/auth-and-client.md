# Graph client and app-only credential (API shape only)

> **Reference excerpt of API shape. Not application code.** Literal values below come from the docs; in project code every value comes from configuration (see `example.env`).

> - Sources: https://learn.microsoft.com/en-us/graph/sdks/choose-authentication-providers?tabs=python , https://learn.microsoft.com/en-us/graph/sdks/create-client?tabs=python
> - Pages last updated (page metadata): 2025-08-06 / 2025-08-06
> - Library version(s): msgraph-sdk 1.64.0 (pinned in inputs/references.md); Graph REST v1.0; azure-identity 1.26.0
> - Date retrieved: 2026-10-15
> - Status: UNVERIFIED (copied from current docs; never executed against a live service)
>
> Permission names below are what Microsoft documents for this call. The project's permission set and approver are **to be confirmed with IT** (decision D7, deferred). Do not scope permissions in code.
> Auth model (app-only vs delegated, managed identity vs certificate) is a decision for IT. The docs' secret-based variants are deliberately not copied: secrets never go in code (R7).

## Client credentials with a certificate (Python tab)

```python
# The client credentials flow requires that you request the
# /.default scope, and pre-configure your permissions on the
# app registration in Azure. An administrator must grant consent
# to those permissions beforehand.
scopes = ['https://graph.microsoft.com/.default']

# Values from app registration
tenant_id = 'YOUR_TENANT_ID'
client_id = 'YOUR_CLIENT_ID'
certificate_path = 'YOUR_CERTIFICATE_PATH'

# azure.identity.aio
credential = CertificateCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    certificate_path=certificate_path)

graph_client = GraphServiceClient(credential, scopes) # type: ignore
```

## Create client (Python tab; delegated device-code example from the docs)

```python
scopes = ['User.Read']

# Multi-tenant apps can use "common",
# single-tenant apps must use the tenant ID from the Azure portal
tenant_id = 'common'

# Values from app registration
client_id = 'YOUR_CLIENT_ID'

# azure.identity
credential = DeviceCodeCredential(
    tenant_id=tenant_id,
    client_id=client_id)

graph_client = GraphServiceClient(credential, scopes)
```

