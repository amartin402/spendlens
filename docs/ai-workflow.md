# AI workflow log

## Tools used
- OpenCode (Go plan): coding agent. Models used: GPT-5.6 Luna

## Context files
- product-spec.md, AGENTS.md, openapi.yaml, docs/stack.md

## Step log
| Date | Step | Tool / model | Agent mode (Plan/Build/subagent) | Prompt (short) | What I reviewed manually | How I verified |
|------|------|--------------|-----------------------------------|----------------|--------------------------|----------------|
| 2026-10-18 | SpendLens mocked frontend | OpenCode / GPT-5.6 Luna | Build | Implemented React dashboard, service boundary, seeded mock, and core tests | Product spec, responsive navigation, dashboard charts, CSV import path | `make test`, `npm run build` |
| 2026-10-19 | Mock sidebar actions | OpenCode / GPT-5.6 Luna | Build | Wired Settings and Sign out buttons to the existing notice feedback | Sidebar action handlers and mock service contract | `make test`, `npm run build` |
| 2026-10-19 | CSV rejection details | OpenCode / GPT-5.6 Luna | Build | Displayed rejected CSV row numbers and validation reasons in the import result notice | CSV result contract and import feedback path | `make test`, `npm run build` |
| 2026-10-19 | Dashboard color refresh | OpenCode / GPT-5.6 Luna | Build | Replaced muted dashboard accents with a balanced coral, teal, saffron, and blue palette | Dashboard surfaces, sidebar, cards, charts, and category colors | `make test`, `npm run build` |
| 2026-10-19 | OpenAPI contract | OpenCode / GPT-5.6 Luna | Build | Documented the draft API surface, payload schemas, consistent errors, and bearer authentication | Frontend service types, mock behavior, and product-spec.md section 6 | `make test` |
| 2026-10-19 | Backend stack selection | OpenCode / GPT-5.6 Luna | Plan | Selected FastAPI, SQLAlchemy, PostgreSQL, Alembic, and Pytest for the backend | `openapi.yaml`, `product-spec.md`, and developer Python/SQL experience | Documentation review |
| 2026-10-19 | In-memory backend implementation | OpenCode / GPT-5.6 Luna | Build | Implemented the OpenAPI endpoints with bearer auth, hashed passwords, user-scoped seeded data, CRUD, CSV import, and reports | Endpoint contract, money rules, ownership isolation, and report semantics | `make test` |
| 2026-10-19 | Codespaces run targets and proxy | OpenCode / GPT-5.6 Luna | Build | Added Makefile install/run/test/lint/build targets and a host-compatible Vite `/api` proxy | Codespaces ports, backend bind address, frontend service boundary, and Vite configuration | `make lint`, `make build`, `make test-backend`, `make test-frontend` |
| 2026-10-19 | Real frontend API client | OpenCode / GPT-5.6 Luna | Build | Switched the default service to the bearer-authenticated backend client and kept the local mock behind `VITE_USE_MOCK=true` | Backend routes, frontend service types, token configuration, and mock selection | `make test`, `make lint`, `make build` |
| 2026-10-19 | SQLAlchemy SQLite persistence | OpenCode / GPT-5.6 Luna | Build | Replaced the in-memory backend store with SQLAlchemy 2 models, SQLite foreign keys, session-scoped routes, and lifecycle persistence coverage | Product data model, API ownership rules, schema indexes, and test isolation | `make test` |

## Things the AI got wrong (and how I fixed them)
- The first error helper passed JSONResponse arguments in the wrong order, which broke every error response; corrected it to use named arguments.
- The first report aggregation counted transaction rows rather than cent amounts; changed category and merchant aggregation to sum integer cents and added a regression test.
