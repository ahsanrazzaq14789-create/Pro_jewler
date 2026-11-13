# Feature Coverage

## Implemented in Source

- Flutter Android and iOS client project.
- Black and gold application theme.
- Email and password registration.
- JWT authentication.
- PostgreSQL backend.
- Docker Compose configuration.
- SQLite local cache.
- Offline create and update queue.
- Cloud record creation and updates.
- Record search and soft deletion.
- Shop registration and profile updates.
- Shop memberships and roles.
- Super Admin checks.
- Audit events.
- Generic jewellery business modules.
- Gold and silver weight and purity fields.
- Rate, making, discount and amount fields.
- Paid and balance fields.
- JSON backup export.
- Shop summary endpoint.
- Chart of accounts.
- Manual double-entry journal posting.
- Debit and credit validation.
- Trial balance endpoint.
- Profit and loss endpoint.
- Journal audit events.

## Accounting API

### Initialize Chart of Accounts

`POST /shops/{shop_id}/accounting/setup`

### List Accounts

`GET /shops/{shop_id}/accounting/accounts`

### Create Account

`POST /shops/{shop_id}/accounting/accounts`

Parameters:

- code
- name
- account_type

Account types:

- asset
- liability
- equity
- income
- expense

### Post Journal

`POST /shops/{shop_id}/accounting/journals`

Example request:

```json
{
  "reference": "JV-001",
  "narration": "Opening capital",
  "lines": [
    {
      "account_id": 1,
      "debit": 10000,
      "credit": 0
    },
    {
      "account_id": 7,
      "debit": 0,
      "credit": 10000
    }
  ]
}
