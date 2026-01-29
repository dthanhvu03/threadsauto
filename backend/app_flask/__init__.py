"""
Flask application factory.

Creates and configures Flask app instance.
Follows the refactoring plan architecture.
"""

# Standard library
import os
from pathlib import Path

# Third-party
from flask import Flask
from flask_cors import CORS

# Local
from backend.app_flask.config import get_config
from backend.app_flask.core.middleware import register_middleware
from backend.app_flask.core.error_handlers import register_error_handlers


def create_app(config_name=None):
    """
    Create Flask application instance.
    
    Args:
        config_name: Configuration name (development, production, testing)
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    CORS(app, **app.config.get('CORS_CONFIG', {}))
    
    # Register middleware
    register_middleware(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints (will be added as modules are migrated)
    from backend.app_flask.modules.jobs.routes import jobs_bp
    app.register_blueprint(jobs_bp, url_prefix='/api/v1/jobs')
    
    return app
