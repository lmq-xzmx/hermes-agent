"""
Hermes File Manager - API Layer

This __init__.py intentionally avoids importing from auth.py or any module
that depends on services/ (to prevent circular imports).

Direct imports for submodules that don't cause cycles:
    from file_manager.api.middleware import RateLimiter
    from file_manager.api.admin import AdminAPI
"""

# Only import from modules that are completely self-contained
from .middleware import RateLimiter, setup_middleware

__all__ = [
    "RateLimiter",
    "setup_middleware",
]
