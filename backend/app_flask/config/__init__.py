"""
Configuration management for Flask app.

Loads configuration based on environment.
"""

# Standard library
import os

# Local
from backend.app_flask.config.development import DevelopmentConfig
from backend.app_flask.config.production import ProductionConfig
from backend.app_flask.config.testing import TestingConfig

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}


def get_config(config_name=None):
    """
    Get configuration class based on environment.
    
    Args:
        config_name: Configuration name. If None, uses FLASK_ENV env var.
    
    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)
