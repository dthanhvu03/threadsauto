"""
CLI tools package.

Contains command-line interface tools for Git operations and job management.
"""

# Import GitCLI for easier access
try:
    from .git_cli import GitCLI
    __all__ = ['GitCLI']
except ImportError:
    # Fallback for direct execution
    __all__ = []
