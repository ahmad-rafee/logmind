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
RULE_SPLIT ?= validation
RUN_DIR ?= experiments/runs/rules-v1-$(RULE_SPLIT)
EVALUATION_REPORT ?= $(RUN_DIR)/metrics-recomputed.json
MODEL_CONFIG ?= experiments/configs/qwen3-1.7b-zero-shot-v1.json
MODEL_RUN_DIR ?= experiments/runs/qwen3-1.7b-v1-test
BENCHMARK_DIR ?= experiments/runs/phase0-benchmark

.DEFAULT_GOAL := help
.PHONY: help setup test lint format format-check check build schemas validate validate-predictions cli generate freeze verify-dataset rules evaluate model-setup download-model model phase0-benchmark

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

rules: ## Run CPU rules on RULE_SPLIT (default validation), saving artifacts in RUN_DIR
	$(UV) run --locked logmind predict-rules --dataset "$(FROZEN_DIR)" --split "$(RULE_SPLIT)" --output "$(RUN_DIR)"

evaluate: ## Recompute metrics from RUN_DIR/records.jsonl into EVALUATION_REPORT
	$(UV) run --locked logmind evaluate "$(FROZEN_DIR)/$(RULE_SPLIT).jsonl" "$(RUN_DIR)/records.jsonl" --output "$(EVALUATION_REPORT)"

model-setup: ## Install exact CUDA model runtime alongside CPU tooling
	$(UV) sync --locked --extra model

download-model: ## Cache exact public model/tokenizer commits from MODEL_CONFIG
	$(UV) run --locked --extra model logmind download-model --config "$(MODEL_CONFIG)"

model: ## Run fixed zero-shot inference on frozen test into MODEL_RUN_DIR
	$(UV) run --locked --extra model logmind predict-model --dataset "$(FROZEN_DIR)" --config "$(MODEL_CONFIG)" --split test --output "$(MODEL_RUN_DIR)"

phase0-benchmark: ## Benchmark both backends on seven fixed inputs, three cold/warm repetitions
	$(UV) run --locked --extra model logmind benchmark --dataset "$(FROZEN_DIR)" --config "$(MODEL_CONFIG)" --output "$(BENCHMARK_DIR)" --repetitions 3
