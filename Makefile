# Makefile for Git CLI CI/CD

.PHONY: help test test-unit test-integration test-coverage lint format type-check security clean install

help: ## Show this help message
	@echo "Git CLI - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

install-dev: install ## Install development dependencies
	pip install -r requirements-dev.txt

test: test-unit ## Run all tests

test-unit: ## Run unit tests
	pytest tests/unit/test_git_cli.py -v

test-integration: ## Run integration tests
	pytest tests/integration/test_git_cli_integration.py -v -m integration

test-coverage: ## Run tests with coverage report
	pytest tests/unit/test_git_cli.py --cov=scripts/cli/git_cli --cov-report=html --cov-report=term --cov-report=xml
	@echo "Coverage report: htmlcov/index.html"

lint: ## Run pylint
	pylint scripts/cli/git_cli.py --rcfile=.pylintrc

format: ## Format code with black
	black scripts/cli/git_cli.py

format-check: ## Check code formatting
	black --check scripts/cli/git_cli.py

type-check: ## Run mypy type checking
	mypy scripts/cli/git_cli.py --ignore-missing-imports

security: ## Run security scan
	bandit -r scripts/cli/git_cli.py -f json -o bandit-report.json

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

ci: format-check lint type-check test-coverage security ## Run all CI checks

clean: ## Clean generated files
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
