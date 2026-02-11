"""
Pytest configuration and shared fixtures.
"""

import sys
from pathlib import Path
from typing import Generator

import pytest

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


@pytest.fixture
def project_root() -> Path:
    """Return project root directory."""
    return _project_root


@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """Return test data directory."""
    test_dir = project_root / "tests" / "fixtures" / "test_data"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def mysql_config():
    """MySQL test configuration."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "threads_user"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "threads_analytics"),
        "charset": "utf8mb4"
    }


@pytest.fixture
def temp_json_file(tmp_path):
    """Create temporary JSON file for testing."""
    import json
    
    def _create_file(data: dict, filename: str = "test.json"):
        file_path = tmp_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path
    
    return _create_file


@pytest.fixture
def mock_logger():
    """Mock structured logger."""
    from unittest.mock import Mock
    from services.logger import StructuredLogger
    
    logger = Mock(spec=StructuredLogger)
    logger.log_step = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    
    return logger
