"""
Migration flags utility.

Centralized ENV flag parsing for module migration.
All ENV flag parsing must go through this utility - no per-route parsing.

CRITICAL RULES:
- Parse flags once at startup
- Expose immutable functions
- No os.getenv() calls in route handlers
- Kill switch takes precedence over all other flags
"""

# Standard library
import os
from typing import FrozenSet, Set


# Module-level cached values (parsed once at import time)
_enabled_modules: FrozenSet[str] = None
_migration_disabled: bool = None


def _parse_flags():
    """
    Parse migration flags once at startup.
    
    This function is called at module import time to parse flags once.
    """
    global _enabled_modules, _migration_disabled
    
    # Kill switch takes precedence
    disable_flag = os.getenv("DISABLE_NEW_MODULES", "").strip().lower()
    _migration_disabled = disable_flag == "true"
    
    if _migration_disabled:
        # Kill switch active - disable all new modules
        _enabled_modules = frozenset()
        return
    
    # Parse USE_NEW_MODULES flag
    use_new = os.getenv("USE_NEW_MODULES", "").strip()
    
    if use_new.lower() == "all":
        # Enable all modules
        _enabled_modules = frozenset([
            "accounts",
            "dashboard",
            "scheduler",
            "excel",
            "config",
            "selectors"
        ])
    elif use_new:
        # Enable specific modules (comma-separated)
        modules = [m.strip() for m in use_new.split(",") if m.strip()]
        _enabled_modules = frozenset(modules)
    else:
        # Empty/unset - no modules enabled
        _enabled_modules = frozenset()


def get_enabled_modules() -> FrozenSet[str]:
    """
    Get set of enabled module names.
    
    Returns:
        FrozenSet of enabled module names (immutable)
    """
    if _enabled_modules is None:
        _parse_flags()
    return _enabled_modules


def is_module_enabled(module_name: str) -> bool:
    """
    Check if specific module is enabled.
    
    Args:
        module_name: Name of module to check (e.g., "accounts", "dashboard")
    
    Returns:
        True if module is enabled, False otherwise
    """
    if is_migration_disabled():
        return False
    return module_name in get_enabled_modules()


def is_migration_disabled() -> bool:
    """
    Check if migration is disabled (kill switch).
    
    Returns:
        True if DISABLE_NEW_MODULES=true, False otherwise
    """
    if _migration_disabled is None:
        _parse_flags()
    return _migration_disabled


# Parse flags at module import time
_parse_flags()
