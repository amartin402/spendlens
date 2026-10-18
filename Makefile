.PHONY: setup test build

setup:
	@printf '%s\n' 'SpendLens development environment ready.'

test:
	cd frontend && npm install --silent && npm test

build:
	cd frontend && npm install --silent && npm run build
