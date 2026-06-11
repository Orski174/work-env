# work-env Makefile
# Simple wrappers around the helper scripts in scripts/.

SHELL := /bin/bash
PYTHON ?= python3
VENV := .venv

.DEFAULT_GOAL := help

.PHONY: help setup new-task paths check clean clean-venv

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Create the Python venv and install requirements
	@if command -v uv >/dev/null 2>&1; then \
		echo "==> using uv"; \
		uv venv $(VENV) && uv pip install -r requirements.txt; \
	else \
		echo "==> using venv + pip"; \
		$(PYTHON) -m venv $(VENV); \
		$(VENV)/bin/pip install --upgrade pip >/dev/null; \
		$(VENV)/bin/pip install -r requirements.txt; \
	fi
	@echo "==> done. Activate with: source $(VENV)/bin/activate"

new-task: ## Create a new task dir: make new-task name=example-task
	@if [ -z "$(name)" ]; then echo "usage: make new-task name=short-name"; exit 1; fi
	@scripts/new-task.sh "$(name)"

paths: ## Print useful repo paths
	@scripts/paths.sh

check: ## Run basic checks (syntax, structure)
	@scripts/check.sh

clean: ## Remove caches, temp files, and pyc (keeps venv + data)
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.py[co]' -delete 2>/dev/null || true
	@rm -rf .pytest_cache .mypy_cache .ruff_cache tmp .cache
	@echo "==> cleaned caches and temp files"

clean-venv: ## Remove the virtual environment
	@rm -rf $(VENV)
	@echo "==> removed $(VENV)"
