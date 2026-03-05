.PHONY: dev backend-dev frontend-dev test test-backend test-frontend lint build

dev:
	@echo "Run backend and frontend in separate terminals:"
	@echo "  make backend-dev"
	@echo "  make frontend-dev"

backend-dev:
	cd backend && python main.py

frontend-dev:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && PYTHONPATH=. pytest -q

test-frontend:
	cd frontend && npm test

lint:
	cd frontend && npm run lint

build:
	cd frontend && npm run build
