FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# The production API is served by the same FastAPI process as the frontend.
ENV VITE_API_URL=
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/spendlens.db

WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY alembic.ini ./alembic.ini
COPY migrations/ ./migrations/
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN useradd --create-home --uid 10001 appuser \
    && mkdir /data \
    && chown -R appuser:appuser /app /data

USER appuser
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
