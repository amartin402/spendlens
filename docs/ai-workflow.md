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

## Things the AI got wrong (and how I fixed them)
- ...# AI Workflow Log

Running notes for AI-assisted work will be recorded here.
