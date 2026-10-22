.PHONY: setup install backend frontend migrate test test-backend test-frontend test-e2e lint build

setup:
	$(MAKE) install

install:
	python -m pip install -q -r backend/requirements.txt
	cd frontend && npm install --silent
	cd e2e && npm install --silent

backend:
	python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

test:
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend:
	python -m pytest backend

test-frontend:
	cd frontend && npm test

test-e2e:
	cd e2e && npm test

lint:
	python -m compileall -q backend
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build
