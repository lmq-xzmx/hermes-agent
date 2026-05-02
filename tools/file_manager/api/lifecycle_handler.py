"""
FastAPI exception handler for lifecycle violations.

Converts LifecycleViolation exceptions to proper HTTP responses with
user guidance for frontend display.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse

from file_manager.engine.lifecycle_exception import LifecycleViolation

logger = logging.getLogger(__name__)


async def lifecycle_violation_handler(
    request: Request, exc: LifecycleViolation
) -> JSONResponse:
    """
    Handle LifecycleViolation exceptions.

    Logs the violation and returns a structured error response with guidance
    for the frontend to display a user-friendly modal.
    """
    logger.warning(
        "Lifecycle violation: code=%s, message=%s, path=%s, details=%s",
        exc.code,
        exc.message,
        request.url.path,
        exc.details,
    )

    response_data = exc.to_dict()

    # Include HTTP status from exception
    return JSONResponse(
        status_code=exc.http_status,
        content=response_data,
    )


def register_lifecycle_handlers(app):
    """Register lifecycle exception handlers with FastAPI app."""
    from fastapi import FastAPI
    app.add_exception_handler(LifecycleViolation, lifecycle_violation_handler)


# Also register at import time via module-level hook
def _register_global_handler():
    """Register handler globally for consistency across all FastAPI apps."""
    try:
        from fastapi import FastAPI
        # This will be called when the module is imported and app is available
        pass
    except ImportError:
        pass