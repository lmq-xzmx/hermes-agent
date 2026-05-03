"""
FastAPI exception handler for lifecycle violations.

Converts LifecycleViolation exceptions to proper HTTP responses with
user guidance for frontend display.
"""

import logging
import os
from typing import Any, Dict

import yaml
from fastapi import Request, status
from fastapi.responses import JSONResponse

from file_manager.engine.lifecycle_exception import LifecycleViolation

logger = logging.getLogger(__name__)

# Config file path
_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "config",
    "lifecycle_config.yaml"
)


def load_lifecycle_config() -> Dict[str, Any]:
    """Load lifecycle config from YAML file."""
    if not os.path.exists(_CONFIG_PATH):
        logger.warning(f"Config file not found: {_CONFIG_PATH}")
        return {"lifecycle": {"enabled": True}, "rules": {}}

    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load lifecycle config: {e}")
        return {"lifecycle": {"enabled": True}, "rules": {}}


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

    # Register lifecycle config endpoint
    @app.get("/api/v1/lifecycle/config", tags=["lifecycle"])
    async def get_lifecycle_config():
        """
        Get lifecycle constraint configuration.

        Returns the complete constraint ruleset for frontend validation.
        This endpoint serves the same config as config/lifecycle_config.yaml.
        """
        return load_lifecycle_config()