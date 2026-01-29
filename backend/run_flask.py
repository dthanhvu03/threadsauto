"""
Flask application entry point.

Run Flask development server.
"""

# Standard library
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Local
from backend.app_flask import create_app

# Create Flask app
app = create_app()

if __name__ == "__main__":
    # Run Flask development server
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )
