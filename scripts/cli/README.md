# CLI Tools - Documentation

## Overview

CLI Tools cho Threads Automation Tool bao gồm:
- **Git CLI** (`git_cli.py`) - Quản lý Git operations với branch naming convention tự động
- **Jobs CLI** (`jobs_cli.py`) - Quản lý scheduled jobs
- **Unified Menu** (`cli_menu.py`) - Menu tích hợp tất cả tools

## Quick Start

### Sử dụng Unified Menu (Khuyến nghị)

```bash
# Chạy menu tích hợp tất cả tools
python scripts/cli/cli_menu.py
```

Menu sẽ hiển thị:
1. 📦 Git Operations
2. 📋 Jobs Management
3. 🧪 Testing & CI/CD
4. ⚙️ Development Tools
5. 🔍 Utilities

### Sử dụng từng tool riêng lẻ

```bash
# Git CLI
python scripts/cli/git_cli.py status
python scripts/cli/git_cli.py branch --type feature --description "add feature"

# Jobs CLI
python scripts/cli/jobs_cli.py list
python scripts/cli/jobs_cli.py stats

# Testing
python scripts/cli/run_tests.py --ci

# Dev Tools
python scripts/cli/install_dev_deps.py
python scripts/cli/check_node_version.py
```

## Git CLI Tool

Git CLI Tool (`git_cli.py`) là công cụ quản lý Git operations với branch naming convention tự động.

## Setup Development Environment

### Install Dependencies

```bash
# Install base dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

Hoặc install tất cả cùng lúc:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### Verify Setup

```bash
# Test imports (quick verification)
python -c "from scripts.cli.git_cli import GitCLI; print('✅ Imports OK')"

# Run unit tests
pytest tests/unit/test_git_cli.py -v

# Or use the test runner
python scripts/cli/run_tests.py --unit
```

## CI/CD Pipeline

### GitHub Actions Workflow

Workflow tự động chạy khi:
- Push code lên `main` hoặc `develop`
- Pull request vào `main` hoặc `develop`
- Thay đổi trong `scripts/cli/git_cli.py` hoặc tests

### Jobs trong Pipeline

1. **Test** - Chạy unit tests trên multiple OS và Python versions
   - Ubuntu, Windows, macOS
   - Python 3.11, 3.12
   - Coverage reporting

2. **Lint** - Code quality checks
   - Black (formatting)
   - Pylint (linting)
   - MyPy (type checking)
   - Bandit (security)

3. **Integration Test** - Integration tests với real git
   - Requires git repository
   - Tests actual git operations

4. **Security Scan** - Security vulnerability scanning
   - Trivy scanner
   - SARIF report upload

5. **Build Docs** - Documentation generation
   - CLI help text extraction
   - Artifact upload

## Running Tests Locally

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/test_git_cli.py -v

# Run with coverage
pytest tests/unit/test_git_cli.py --cov=scripts/cli/git_cli --cov-report=html

# Run specific test
pytest tests/unit/test_git_cli.py::TestBranchNameFormatting::test_format_feature_branch -v
```

### Integration Tests

```bash
# Run integration tests (requires git)
pytest tests/integration/test_git_cli_integration.py -v -m integration

# Run all tests
pytest tests/ -v
```

### Code Quality Checks

```bash
# Format code
black scripts/cli/git_cli.py

# Lint
pylint scripts/cli/git_cli.py --rcfile=.pylintrc

# Type check
mypy scripts/cli/git_cli.py --ignore-missing-imports

# Security scan
bandit -r scripts/cli/git_cli.py
```

## Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Hooks sẽ tự động chạy khi commit:
- Code formatting (Black)
- Linting (Pylint)
- Type checking (MyPy)
- Security scan (Bandit)
- Unit tests (pytest)

## Coverage Requirements

- **Target**: >80% coverage cho `git_cli.py`
- **Current**: Check via `pytest --cov` report
- **Exclusions**: Test files, venv, __pycache__

## Version Management

Version được quản lý trong:
- `scripts/cli/git_cli.py` - Module docstring
- Git tags cho releases
- Changelog trong commits

## Release Process

1. Update version trong code
2. Run all tests: `pytest tests/ -v`
3. Run linting: `pylint scripts/cli/git_cli.py`
4. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
5. Push tag: `git push origin v1.0.0`

## Troubleshooting

### Tests fail locally but pass in CI

- Check Python version: CI uses 3.11, 3.12
- Check git version: Integration tests require git
- Check dependencies: `pip install -r requirements.txt`

### Coverage too low

- Add tests for uncovered branches
- Check coverage report: `htmlcov/index.html`
- Exclude non-testable code with `# pragma: no cover`

### Pre-commit hooks fail

- Run manually: `pre-commit run --all-files`
- Fix issues reported
- Re-commit

## Contributing

1. Write tests for new features
2. Ensure coverage >80%
3. Run pre-commit hooks
4. Update documentation
5. Create PR
