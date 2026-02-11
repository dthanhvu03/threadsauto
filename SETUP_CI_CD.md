# CI/CD Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Base dependencies
pip install -r requirements.txt

# Development dependencies (for CI/CD)
pip install -r requirements-dev.txt
```

Hoặc dùng script tự động:
```bash
# Python script (cross-platform)
python scripts/cli/install_dev_deps.py

# Shell script (Linux/Mac)
bash scripts/cli/install_dev_deps.sh

# Makefile
make install-dev
```

### 2. Verify Setup

```bash
# Test imports work
python scripts/cli/test_import.py

# Run unit tests
pytest tests/unit/test_git_cli.py -v
```

### 3. Run CI Checks Locally

```bash
# All CI checks
python scripts/cli/run_tests.py --ci

# Or use Makefile
make ci
```

## What Was Fixed

### Issue 1: Import Error
**Problem**: `ModuleNotFoundError: No module named 'scripts.cli'`

**Solution**: 
- Created `scripts/__init__.py`
- Created `scripts/cli/__init__.py`
- Python now recognizes `scripts` as a package

### Issue 2: Missing Dependencies
**Problem**: `black`, `pylint`, `mypy`, `bandit` not found

**Solution**:
- Created `requirements-dev.txt` with all dev dependencies
- Updated GitHub Actions workflow to use `requirements-dev.txt`

## Files Created/Modified

### New Files
- `scripts/__init__.py` - Package marker
- `scripts/cli/__init__.py` - CLI package marker with exports
- `requirements-dev.txt` - Development dependencies
- `scripts/cli/test_import.py` - Import verification script

### Modified Files
- `.github/workflows/git-cli-ci.yml` - Updated to use `requirements-dev.txt`
- `scripts/cli/README.md` - Added setup instructions
- `Makefile` - Added `install-dev` target

## Next Steps

1. **Install dev dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Run tests**:
   ```bash
   pytest tests/unit/test_git_cli.py -v
   ```

3. **Setup pre-commit hooks** (optional):
   ```bash
   pre-commit install
   ```

4. **Verify everything works**:
   ```bash
   python scripts/cli/run_tests.py --ci
   ```

## Troubleshooting

### Import still fails
- Make sure you're in the project root directory
- Verify `scripts/__init__.py` and `scripts/cli/__init__.py` exist
- Try: `python -c "import sys; sys.path.insert(0, '.'); from scripts.cli.git_cli import GitCLI"`

### Dependencies not found
- Make sure virtual environment is activated
- Run: `pip install -r requirements-dev.txt`
- Verify installation: `pip list | grep black`

### Tests fail
- Check Python version (3.11+)
- Make sure git is installed for integration tests
- Run: `pytest tests/unit/test_git_cli.py -v` to see detailed errors
