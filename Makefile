.PHONY: setup install backend frontend test test-backend test-frontend lint build

setup:
	$(MAKE) install

install:
	python -m pip install -q -r backend/requirements.txt
	cd frontend && npm install --silent

backend:
	python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

test:
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend:
	python -m pytest backend

test-frontend:
	cd frontend && npm test

lint:
	python -m compileall -q backend
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build
