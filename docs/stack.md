# Backend Stack

## Decision

Use **FastAPI + SQLAlchemy + PostgreSQL** for the SpendLens backend.

This stack best matches the existing OpenAPI contract and the developer's Python and SQL experience. It is lightweight for the MVP while remaining suitable for user-scoped relational data and BI-style aggregate reports.

## Components

| Layer | Choice | Purpose |
|---|---|---|
| API | FastAPI | HTTP routing, bearer authentication integration, request validation, and OpenAPI generation |
| Schemas | Pydantic v2 | Validate request payloads and shape responses to the OpenAPI schemas |
| Persistence | SQLAlchemy 2.x | Relational models, transactions, and database access |
| Migrations | Alembic | Versioned database schema changes |
| Database | PostgreSQL | Production persistence, constraints, indexes, and report queries |
| Local database | SQLite | Optional lightweight local development database |
| Password hashing | Argon2 or bcrypt | Secure password storage |
| Authentication | JWT bearer tokens | Implements the `bearerAuth` OpenAPI security scheme |
| Testing | Pytest | Unit, API, and database integration tests |
| Packaging | Docker Compose | Run the API and PostgreSQL consistently in development and deployment |

## Why This Fits SpendLens

- FastAPI maps directly to the OpenAPI 3.0.3 contract and its operation-based endpoints.
- Pydantic models fit request and response objects such as `TransactionCreate`, `Subscription`, and `MonthlyReport`.
- SQLAlchemy supports the CRUD workload while allowing explicit SQL-oriented queries for monthly totals, category breakdowns, top merchants, and spending trends.
- Python's standard CSV tooling and data-processing ecosystem fit the partial-success CSV import requirement.
- PostgreSQL supports the relational constraints and indexes required by the product specification.
- Pytest provides a natural way to test authentication, ownership isolation, validation, CSV imports, and report calculations.

## Backend Boundaries

Organize the backend around the OpenAPI tags:

- `auth`: registration, login, current-user lookup, password hashing, and JWT handling
- `categories`: category CRUD and deletion/reassignment rules
- `transactions`: transaction CRUD, filtering, pagination, and CSV import
- `subscriptions`: subscription CRUD, cancellation, monthly-equivalent calculations, and upcoming renewals
- `reports`: monthly and trend aggregation queries
- `operations`: health checks

Use a service or repository boundary between route handlers and database access. Route handlers should handle HTTP concerns; services should enforce business rules; repositories should perform user-scoped persistence and report queries.

## Required Data Rules

- Store all money as integer cents. Never use floating-point values for money.
- Scope every database query by the authenticated `user_id`.
- Return `404` when a resource ID does not belong to the authenticated user.
- Enforce unique category names per user.
- Use database transactions for category deletion with reassignment and CSV imports.
- Calculate subscription monthly equivalents using integer arithmetic and round only at the end.
- Preserve the consistent error shape defined by `ErrorResponse`.

## Database Indexes

Create the indexes specified by the product requirements:

- `transactions(user_id, date)`
- `transactions(user_id, category_id)`
- `subscriptions(user_id, status, next_renewal_date)`

The report queries should be verified against the requirement of responding in under 500 ms for 10,000 transactions per user.

## Initial Implementation Guidance

1. Define SQLAlchemy models and Alembic migrations for users, categories, transactions, and subscriptions.
2. Implement authentication and a dependency that resolves the current user from the JWT.
3. Implement CRUD endpoints with Pydantic schemas matching `openapi.yaml`.
4. Add CSV parsing with per-row validation and a result containing imported and rejected rows.
5. Implement report queries using explicit, tested SQLAlchemy expressions.
6. Add tests for ownership isolation, money calculations, CSV partial success, and report totals.
