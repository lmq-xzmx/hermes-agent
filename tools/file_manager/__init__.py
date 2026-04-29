"""
Hermes File Manager
-------------------

A team collaboration file management system with RBAC permissions.
Integrates with hermes-agent as a tool or runs as a standalone REST API server.

Usage:
    # As hermes-agent tool (auto-loaded when enabled)
    file_manager_login(username="alice", password="...")
    file_manager_list(path="/shared/projects")

    # As standalone server
    python -m file_manager.server

Environment Variables:
    HFM_API_URL       - API server URL (default: http://localhost:8080)
    HFM_API_KEY       - API key for hermes-agent integration
    HFM_STORAGE_ROOT  - Root directory for file storage
    HFM_DATABASE_URL  - Database connection URL
    HFM_JWT_SECRET    - JWT signing secret (change in production!)
    HFM_PORT          - Server port (default: 8080)
    HFM_HOST          - Server host (default: 0.0.0.0)
"""

__version__ = "1.0.0"
__all__ = [
    "engine",
    "api",
    "tools",
]
