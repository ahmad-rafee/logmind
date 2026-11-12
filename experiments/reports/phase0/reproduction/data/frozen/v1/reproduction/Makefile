# Developer commands. Run `make help` to list targets.
# Override paths/tools on the command line, e.g.:
#   make validate INCIDENTS=data/generated/incidents.jsonl
#   make validate-predictions PREDICTIONS=predictions.jsonl INCIDENTS=incidents.jsonl
UV ?= uv
INCIDENTS ?= tests/fixtures/incident.jsonl
PREDICTIONS ?=
SCHEMA_DIR ?= schemas
SEED ?= 42
DATA_DIR ?= data/generated/v1-seed$(SEED)
TEMPLATES ?= data/scenarios/templates
FROZEN_DIR ?= data/frozen/v1
DATASET_VERSION ?= v1

.DEFAULT_GOAL := help
.PHONY: help setup test lint format format-check check build schemas validate validate-predictions cli generate freeze verify-dataset

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

generate: ## Generate 150 candidate records in DATA_DIR using SEED and TEMPLATES
	$(UV) run --locked logmind generate --output "$(DATA_DIR)" --seed "$(SEED)" --templates "$(TEMPLATES)"

freeze: ## Audit DATA_DIR and create FROZEN_DIR with pinned reproduction inputs
	$(UV) run --locked logmind freeze --candidate "$(DATA_DIR)" --output "$(FROZEN_DIR)" --templates "$(TEMPLATES)" --dataset-version "$(DATASET_VERSION)"

verify-dataset: ## Verify FROZEN_DIR data, provenance, and checksums
	$(UV) run --locked logmind verify-dataset "$(FROZEN_DIR)"
