.PHONY: help lint format test install dev clean

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements_render.txt
	pip install ruff

dev:  ## Setup development environment
	@echo "🔧 Setting up development environment..."
	bash scripts/dev-setup.sh

lint:  ## Run linting checks (ruff only)
	@echo "🔍 Running linting checks..."
	ruff check poe_lastz_v0_8_2/ scripts/ --exclude archive/

lint-fix:  ## Auto-fix linting issues
	@echo "🔧 Auto-fixing linting issues..."
	ruff check poe_lastz_v0_8_2/ scripts/ --fix --exclude archive/
	ruff format poe_lastz_v0_8_2/ scripts/ --exclude archive/

format:  ## Format code with ruff
	@echo "✨ Formatting code..."
	ruff format poe_lastz_v0_8_2/ scripts/ --exclude archive/

check:  ## Run all checks before commit (lint + format check)
	@echo "🔍 Running pre-commit checks..."
	@ruff check poe_lastz_v0_8_2/ scripts/ --exclude archive/
	@ruff format poe_lastz_v0_8_2/ scripts/ --check --exclude archive/
	@echo "✅ All checks passed!"

test:  ## Run tests (if any)
	@echo "🧪 Running tests..."
	@echo "⚠️  No tests configured yet"

clean:  ## Clean up cache files
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned!"
