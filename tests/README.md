# 🧪 Testing Documentation

Testing infrastructure và guidelines cho Threads Automation Tool.

---

## 📋 Test Structure

```
tests/
├── conftest.py              # Pytest fixtures
├── unit/                    # Unit tests
│   ├── test_mysql_storage.py
│   ├── test_excel_storage.py
│   └── test_safety_guard.py
├── integration/             # Integration tests
│   └── test_storage_integration.py
└── fixtures/                # Test fixtures
    └── test_data/
```

---

## 🚀 Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test file:
```bash
pytest tests/unit/test_mysql_storage.py
```

### Run with coverage:
```bash
pytest --cov=services --cov=ui --cov-report=html
```

### Run only unit tests:
```bash
pytest tests/unit/
```

### Run only integration tests:
```bash
pytest tests/integration/
```

### Run with markers:
```bash
pytest -m unit
pytest -m integration
pytest -m "requires_mysql"
```

---

## 📊 Test Coverage

**Target:** 80%+ coverage for core modules

**Current Coverage:**
- Run `pytest --cov` to see current coverage
- View HTML report: `htmlcov/index.html`

---

## 🔧 Test Fixtures

### Common Fixtures (conftest.py):
- `project_root` - Project root directory
- `test_data_dir` - Test data directory
- `mysql_config` - MySQL test configuration
- `temp_json_file` - Temporary JSON file creator
- `mock_logger` - Mock structured logger

---

## 📝 Writing Tests

### Unit Test Example:
```python
def test_save_job(storage, mock_logger):
    """Test saving a job."""
    job = ScheduledJob(...)
    storage.save_job(job)
    loaded = storage.get_job(job.job_id)
    assert loaded is not None
```

### Integration Test Example:
```python
@pytest.mark.integration
def test_complete_workflow(storage):
    """Test complete workflow."""
    # Test full flow
    pass
```

---

## ⚠️ Notes

- Tests requiring MySQL will skip if database is not available
- Use `pytest.skip()` for conditional tests
- Mock external dependencies in unit tests
- Use real database for integration tests

---

**Last Updated:** 2026-01-19
