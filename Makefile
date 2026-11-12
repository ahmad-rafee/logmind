# Developer commands. Run `make help` to list targets.
# Override paths/tools on the command line, e.g.:
#   make validate INCIDENTS=data/generated/incidents.jsonl
#   make validate-predictions PREDICTIONS=predictions.jsonl INCIDENTS=incidents.jsonl
UV ?= uv
INCIDENTS ?= tests/fixtures/incident.jsonl
PREDICTIONS ?=
SCHEMA_DIR ?= schemas

.DEFAULT_GOAL := help
.PHONY: help setup test lint format format-check check build schemas validate validate-predictions cli

help: ## List available commands
	@awk 'BEGIN {FS = ":.*## "; print "Usage: make <target> [VARIABLE=value]\n"} /^[a-z-]+:.*## / {printf "  %-23s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install locked dependencies, including development tools
	$(UV) sync --locked

test: ## Run the test suite
	$(UV) run --locked pytest

lint: ## Check code with Ruff
	$(UV) run --locked ruff check .

format: ## Apply Ruff formatting
	$(UV) run --locked ruff format .

format-check: ## Check formatting without modifying files
	$(UV) run --locked ruff format --check .

check: lint format-check test ## Run all code checks and tests

build: ## Build wheel and source distribution in dist/
	$(UV) build

schemas: ## Export JSON schemas to SCHEMA_DIR (default: schemas)
	$(UV) run --locked logmind export-schemas "$(SCHEMA_DIR)"

validate: ## Validate INCIDENTS (default: the example fixture)
	$(UV) run --locked logmind validate-incidents "$(INCIDENTS)"

validate-predictions: ## Validate PREDICTIONS against INCIDENTS; set both paths for your data
	@test -n "$(PREDICTIONS)" || { echo 'Set PREDICTIONS, e.g. make validate-predictions PREDICTIONS=predictions.jsonl INCIDENTS=incidents.jsonl' >&2; exit 1; }
	$(UV) run --locked logmind validate-predictions "$(PREDICTIONS)" "$(INCIDENTS)"

cli: ## Show the LogMind CLI help
	$(UV) run --locked logmind --help
