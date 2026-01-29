"""
Production configuration.
"""

# Standard library
import os


class ProductionConfig:
    """Production configuration."""
    
    # Flask
    DEBUG = False
    TESTING = False
    
    # CORS
    CORS_CONFIG = {
        'allow_origins': os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else [],
        'allow_credentials': True,
        'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization'],
    }
    
    # Logging
    LOG_LEVEL = 'INFO'
