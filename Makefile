PYTHON ?= $(shell which python3.12 2>/dev/null || which python3)
VENV ?= .venv
BIN = $(VENV)/bin

.PHONY: all setup lock check-docs test test-fast test-live check-coverage visualizer-build visualizer-sync clean dev dev-stop

all: setup test

setup:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment using $(PYTHON)..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@$(BIN)/pip install --upgrade pip setuptools wheel
	@if [ -f "requirements.lock" ]; then \
		$(BIN)/pip install -r requirements.lock; \
		$(BIN)/pip install --no-deps -e .; \
	else \
		$(BIN)/pip install -e ".[dev]"; \
	fi

lock:
	@if [ -f "$(BIN)/python" ]; then \
		$(BIN)/python scripts/generate_lock.py; \
	elif command -v python3 >/dev/null 2>&1; then \
		python3 scripts/generate_lock.py; \
	else \
		echo "Python not found. Please run 'make setup' first."; \
		exit 1; \
	fi

test-fast:
	@if [ -f "$(BIN)/pytest" ]; then \
		$(BIN)/pytest tests/ -m "unit and not pty and not live" -q; \
	elif command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -m "unit and not pty and not live" -q; \
	else \
		echo "pytest not found. Please run 'make setup' first."; \
		exit 1; \
	fi

test:
	@if [ -f "$(BIN)/pytest" ]; then \
		$(BIN)/pytest tests/ -m "not live" --cov=octoflow --cov-report=term --cov-report=json:coverage.json -q && $(BIN)/python scripts/check_coverage.py; \
	elif command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -m "not live" --cov=octoflow --cov-report=term --cov-report=json:coverage.json -q && python scripts/check_coverage.py; \
	else \
		echo "pytest not found. Please run 'make setup' first."; \
		exit 1; \
	fi

test-live:
	@if [ -f "$(BIN)/pytest" ]; then \
		$(BIN)/pytest tests/ -m "live" -q; \
	elif command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -m "live" -q; \
	else \
		echo "pytest not found. Please run 'make setup' first."; \
		exit 1; \
	fi

check-docs:
	@if [ -f "/python" ]; then 		/python scripts/check_docs.py; 	elif command -v python3 >/dev/null 2>&1; then 		python3 scripts/check_docs.py; 	else 		python scripts/check_docs.py; 	fi

check-coverage:
	@if [ -f "$(BIN)/python" ]; then \
		$(BIN)/python scripts/check_coverage.py; \
	elif command -v python >/dev/null 2>&1; then \
		python scripts/check_coverage.py; \
	else \
		echo "python not found."; \
		exit 1; \
	fi

visualizer-build:
	@echo "Building visualizer..."
	@cd visualizer && npm ci && npm run build
	@mkdir -p octoflow/dist
	@cp -R visualizer/dist/* octoflow/dist/

visualizer-sync:
	@bash scripts/sync_visualizer.sh

clean:
	@echo "Cleaning build and cache artifacts..."
	@rm -rf build/ dist/ *.egg-info .eggs/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache htmlcov .coverage .coverage.*

dev:
	@if [ -f "$(BIN)/python" ]; then \
		$(BIN)/python scripts/dev_servers.py start; \
	elif command -v python3 >/dev/null 2>&1; then \
		python3 scripts/dev_servers.py start; \
	else \
		$(PYTHON) scripts/dev_servers.py start; \
	fi

dev-stop:
	@if [ -f "$(BIN)/python" ]; then \
		$(BIN)/python scripts/dev_servers.py stop; \
	elif command -v python3 >/dev/null 2>&1; then \
		python3 scripts/dev_servers.py stop; \
	else \
		$(PYTHON) scripts/dev_servers.py stop; \
	fi
