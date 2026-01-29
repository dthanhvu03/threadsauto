"""
Testing configuration.
"""


class TestingConfig:
    """Testing configuration."""
    
    # Flask
    DEBUG = True
    TESTING = True
    
    # CORS
    CORS_CONFIG = {
        'allow_origins': ['*'],
        'allow_credentials': True,
        'allow_methods': ['*'],
        'allow_headers': ['*'],
    }
    
    # Logging
    LOG_LEVEL = 'DEBUG'
