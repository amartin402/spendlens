# Product Spec: SpendLens

> Expense and subscription tracker with a BI-style dashboard.
> Status: **Draft v1**. Save this in the repo as `product-spec.md` (a copy in `docs/` is fine too).
> Paste it into your coding assistant when building the mocked frontend (Step 2 of the guide).

---

## 1. Problem

People lose track of where their money goes, especially to **recurring charges**: streaming, SaaS tools, gym memberships, cloud bills. Bank apps list transactions but don't answer simple questions like:

- "How much do I spend per month on subscriptions?"
- "What renews in the next 14 days?"
- "Which category grew the most over the last 3 months?"

Spreadsheets can answer these, but they are tedious to maintain and have no reminders.

## 2. Solution

**SpendLens** is a web app where a user logs expenses (manually or via CSV import), tracks recurring subscriptions, and sees a dashboard of spending by category, by month, and over time.

**Primary user:** an individual tracking personal or freelance spending.
**Positioning:** a small, fast, data-first tool. No bank sync and no AI inside the product at launch.

## 3. Scope

### In scope (MVP)

| # | Feature | Notes |
|---|---------|-------|
| F1 | Register / login | Email + password, hashed, bearer-token auth. Each user sees only their own data. | 24 hours.
| F2 | Categories | Create, rename, delete. A default set is seeded on registration (Food, Rent, Transport, Entertainment, Software, Other). |
| F3 | Transactions | Create, list (filter by date range, category, text), edit, delete. |
| F4 | CSV import | Upload a CSV with `date,description,amount,category`. Report how many rows were imported and which were rejected, with reasons. | standard YYYY-MM-DD
| F5 | Subscriptions | Create, edit, cancel, delete. Fields: name, amount, billing period (weekly / monthly / yearly), next renewal date, category. |
| F6 | Monthly report | For a chosen month: total spent, spend per category, top 5 merchants/descriptions, subscription total. |
| F7 | Trend report | Total spend and subscription spend per month for the last N months (default 6). |
| F8 | Upcoming renewals | Active subscriptions renewing in the next N days (default 14), shown on the dashboard. |
| F9 | Health endpoint | `GET /health` for deployment checks and CI. |

### Out of scope (do not build)

Bank/Plaid sync, multi-currency, shared or household accounts, mobile apps, email/push notifications, receipt OCR, budgets and goals, password reset by email, in-app AI features.

### Stretch (only if everything else is done)

Budgets per category, dark mode, export report as CSV.

## 4. User stories and acceptance criteria

**US1: Sign up and get started**
- Given I'm a new visitor, when I register with a valid email and password, then I'm logged in and see an empty dashboard with default categories.
- Registering with an existing email returns a clear error.

**US2: Log an expense**
- When I add a transaction with a date, description, amount, and category, it appears in the list and in the current month's totals immediately.
- Amount must be greater than 0. A missing date or category is rejected with a field-level error.

**US3: Import from CSV**
- When I upload a valid CSV, all valid rows are created.
- Invalid rows (bad date, non-numeric amount, unknown category) are skipped and listed in the result. One bad row must not fail the whole file.

**US4: Track subscriptions**
- When I add a subscription, it appears in the subscriptions list with its **monthly equivalent cost** (yearly / 12, weekly × 52 / 12).
- It shows on the dashboard under "Upcoming renewals" if it renews within the window.
- Cancelling a subscription removes it from the totals but keeps it in a "Cancelled" view.

**US5: Understand my spending**
- The dashboard shows: total this month, a category breakdown chart, a 6-month trend chart, the subscription monthly total, and upcoming renewals.
- Changing the month updates every widget.

**US6: Privacy**
- I can never read or modify another user's data by guessing IDs (the API returns 404).

## 5. Data model

All money is stored as **money**. Dates are ISO `YYYY-MM-DD`.

```text
users
  id (pk), email (unique), password_hash, created_at

categories
  id (pk), user_id (fk), name, created_at
  unique (user_id, name)

transactions
  id (pk), user_id (fk), category_id (fk), date, description,
  amount_cents (int > 0), source ("manual" | "csv"), created_at

subscriptions
  id (pk), user_id (fk), category_id (fk), name, amount_cents (int > 0),
  billing_period ("weekly" | "monthly" | "yearly"),
  next_renewal_date, status ("active" | "cancelled"), created_at
```

Indexes: `transactions(user_id, date)`, `transactions(user_id, category_id)`, `subscriptions(user_id, status, next_renewal_date)`.

**Business rules**
- Monthly equivalent: monthly = amount; yearly = amount / 12; weekly = amount × 52 / 12. Round once, at the end.
- Subscription total in reports = sum of monthly equivalents of **active** subscriptions.
- Deleting a category that has transactions is rejected (409) unless the client passes `reassign_to=<category_id>`.
- Subscriptions do **not** automatically create transactions in the MVP. They are a separate planning view.

## 6. API surface (draft)

The OpenAPI file (`openapi.yaml`) will be generated from the frontend's API client, so treat this as the target, not the final contract.

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /me` |
| Categories | `GET /categories`, `POST /categories`, `PATCH /categories/{id}`, `DELETE /categories/{id}` |
| Transactions | `GET /transactions` (filters: `from`, `to`, `category_id`, `q`, paging), `POST /transactions`, `GET/PATCH/DELETE /transactions/{id}`, `POST /transactions/import` |
| Subscriptions | `GET /subscriptions` (`status`), `POST /subscriptions`, `GET/PATCH/DELETE /subscriptions/{id}`, `GET /subscriptions/upcoming?days=14` |
| Reports | `GET /reports/monthly?month=YYYY-MM`, `GET /reports/trend?months=6` |
| Ops | `GET /health` |

All endpoints except `/auth/*` and `/health` require `Authorization: Bearer <token>`. Errors use one consistent shape: `{ "error": { "code": "...", "message": "...", "fields": { ... } } }`.

## 7. Screens

1. **Login / Register**
2. **Dashboard**: month picker, total spent, category breakdown chart, 6-month trend chart, subscription monthly total, upcoming renewals list.
3. **Transactions**: filterable table, add/edit dialog, CSV import dialog with result summary.
4. **Subscriptions**: Active / Cancelled tabs, add/edit dialog, monthly-equivalent column.
5. **Categories**: simple list with add / rename / delete.

## 8. Proposed technical decisions

(To be confirmed or challenged in the stack step of the guide.)

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React + TypeScript + Vite, a charting library (e.g. Recharts) | Quick to generate with an AI tool, good chart support |
| API client | One `services/` layer with a mock and a real implementation | Required for the mocked-frontend-first workflow |
| Backend | FastAPI (Python) | Fits a data developer's skills, generates OpenAPI natively, easy to test |
| ORM | SQLAlchemy | Lets you switch SQLite → Postgres without rewriting queries |
| Database | SQLite (dev), Postgres (prod / Docker Compose) | Matches the course path |
| Packaging | One Docker image: backend serves the built frontend | Simplest deployment |
| Tests | pytest (backend + integration), Vitest (frontend), Playwright (e2e) | Covers the rubric's test levels |
| CI/CD | GitHub Actions | Course default |
| Cloud | To be chosen in the deployment step | Pick the simplest option that gives a public URL |

## 9. Non-functional requirements

- Passwords are hashed (bcrypt or argon2). No secrets in the repo; use environment variables.
- Every query is scoped by `user_id`.
- Reports respond in under 500 ms for 10,000 transactions per user (add the indexes above).
- `make` targets exist for run, test, lint, and build.
- The whole stack starts with `docker compose up`.

## 10. Manual test scenario

Run this by hand after every major step. It is later automated as the Playwright e2e test.

1. Open the app and register `test@example.com`.
2. Confirm the default categories exist.
3. Add three transactions in two different categories for the current month.
4. Open the dashboard and confirm the total and the category chart match what you entered.
5. Import a CSV with 5 valid rows and 2 invalid rows. Confirm "5 imported, 2 rejected" with reasons.
6. Add a yearly subscription for 120.00 and confirm its monthly equivalent is 10.00.
7. Add a monthly subscription renewing in 5 days and confirm it appears under "Upcoming renewals".
8. Cancel one subscription and confirm the subscription total drops.
9. Log out, register a second user, and confirm none of the first user's data is visible.
10. Restart the app and confirm the data is still there (persistence).

## 11. Metrics to track (for observability)

1. `http_requests_total` and `http_request_duration` by route and status
2. `transactions_created_total` (labelled by source: manual / csv)
3. `csv_import_rows_total` (labelled by result: imported / rejected)
4. `users_registered_total`
5. `report_generation_duration` by report type

## 12. Agent extension idea (Module 5)

An **MCP server** exposing SpendLens to a coding assistant:

- `get_spend_summary(month, category?)`: read-only monthly totals.
- `list_upcoming_renewals(days)`: read-only.
- `add_transaction(...)`: **write**; documented in `docs/permissions.md` and requires explicit confirmation.

## 13. Open questions

- Should subscriptions optionally generate transactions on renewal day? (MVP: no.)
- Is a single currency symbol configurable per user, or fixed? (MVP: configurable per user)
- CSV format: fixed header names, or column mapping UI? (MVP: fixed.)
