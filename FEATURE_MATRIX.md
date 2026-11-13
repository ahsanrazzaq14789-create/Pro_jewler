# Feature coverage and delivery status

## Implemented in this source package
- Flutter Android/iOS client project with black-and-gold theme
- Email/password registration and login API; JWT bearer authentication
- PostgreSQL backend and Docker Compose deployment
- Local SQLite cache and queued offline upserts in the mobile client
- Cloud record create/update, list/search and soft-delete API
- Shop registration/profile updates and shop membership/roles
- Server-side shop membership checks and Super Admin role checks
- Audit events for record upserts and deletions
- Modules: sales, purchase, bills, customers, suppliers, stock, accounts, reports, karigar, repairs, ledger/deposits/udhar, expenses, staff, jewellery orders
- Generic fields for metal, weight, purity, rate, making, discount, amount, paid, balance, status, party, notes and reference
- Summary endpoint, JSON backup export, audit log endpoint
- Gold conversion and pricing helper functions

## Not yet a production-complete implementation
These need additional implementation, configuration and acceptance testing; do not represent them as completed:
- Automated double-entry accounting, chart of accounts, journal posting and reconciliations
- Inventory movement ledger with automatic stock in/out, metal-wise purity/karat valuation and barcode support
- Customer/supplier statement allocation and payment settlement workflows
- Dedicated professionally formatted A5/thermal receipt templates and printer model validation
- PDF export from every report, Excel/CSV exports and scheduled reports
- Full user/staff management UI, password reset, invitation flow, granular permission matrix and admin console UI
- True bidirectional conflict-aware offline sync (current client queues offline creates/updates; server version conflict checks are basic)
- Backup restore UI, scheduled encrypted backups, retention policies and disaster recovery tests
- Cloud deployment, TLS/domain, secrets management, monitoring, rate limiting, database migrations and production hardening
- End-to-end automated tests, Android/iOS builds, device testing and security audit

## Business-specific decisions required before final production sign-off
- Gold and silver units/cut conventions used by the shop (tola/masha/ratti/points, grams, purity)
- Tax/receipt requirements and currency format
- Receipt layout, logo and shop details
- Staff roles and exact permissions
- Hosting provider, domain, backup retention and recovery target

## Safety
Never deploy with the example passwords or development SECRET_KEY. Change all secrets, configure TLS, firewall the database, and create a tested backup before using real customer data.
