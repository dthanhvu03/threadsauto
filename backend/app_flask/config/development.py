"""
Development configuration.
"""

# Standard library
import os


class DevelopmentConfig:
    """Development configuration."""
    
    # Flask
    DEBUG = True
    TESTING = False
    
    # CORS
    CORS_CONFIG = {
        'allow_origins': [
            'http://localhost:5173',
            'http://localhost:3000',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:3000',
        ],
        'allow_credentials': True,
        'allow_methods': ['*'],
        'allow_headers': ['*'],
    }
    
    # Logging
    LOG_LEVEL = 'DEBUG'
