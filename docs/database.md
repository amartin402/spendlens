# Database

The backend uses SQLAlchemy 2.x and reads its connection string exclusively from
the `DATABASE_URL` environment variable. No database URL is hardcoded in the
application.

## Local SQLite

```sh
export DATABASE_URL=sqlite:///./spendlens.db
make backend
```

SQLite foreign keys are enabled for every connection. The default schema is
created by `Base.metadata.create_all()` from `backend/db.py` when the FastAPI
application is imported. This is the documented schema initialization step for
the current MVP; run the application once against a new database before using
the API. The models and SQLAlchemy URLs are compatible with moving to Postgres
later.

Tests set `DATABASE_URL` to an isolated SQLite file and recreate all tables for
each test.
