"""
PermissionChecker - Pure permission logic operating on primitives.

No ORM, no storage. Takes PermissionContext (strings/primitives) and
returns permission decisions. Used by FileService at the service layer.

Architecture:
  services/FileService  →  PermissionChecker  →  engine/StorageEngine
       (domain)               (pure logic)           (filesystem I/O)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# =============================================================================
# Domain Types
# =============================================================================

class Operation:
    LIST = "list"
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE = "manage"

    ALL = {LIST, READ, WRITE, DELETE, MANAGE}


@dataclass
class PermissionDecision:
    allowed: bool
    reason: str
    matched_rule: Optional[str] = None


# =============================================================================
# PermissionChecker
# =============================================================================

class PermissionChecker:
    """
    Stateless permission checker operating on primitive types.

    Algorithm:
      1. Admin role always gets full access.
      2. Find all rules matching the requested path (glob pattern).
      3. Pick the highest-priority matching rule.
      4. Check if the operation is allowed by that rule's permissions.
    """

    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root).resolve()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def check(
        self,
        operation: str,
        path: str,
        ctx: "PermissionContext",  # Forward ref to avoid circular
    ) -> PermissionDecision:
        """
        Main entry point. Returns a PermissionDecision.
        """
        # Admin bypass
        if ctx.role_name == "admin":
            return PermissionDecision(
                allowed=True,
                reason="Admin role",
                matched_rule="admin_bypass",
            )

        if not ctx.permission_rules:
            return PermissionDecision(
                allowed=False,
                reason=f"No permission rules for user '{ctx.username}'",
            )

        normalized = self._normalize_path(path)
        matching = self._find_matching_rules(ctx.permission_rules, normalized)

        if not matching:
            return PermissionDecision(
                allowed=False,
                reason=f"No rule matches path '{path}' for user '{ctx.username}'",
            )

        # Pick highest priority
        best = max(matching, key=lambda r: r.priority)

        allowed_ops = best.operations
        if operation in allowed_ops or Operation.MANAGE in allowed_ops:
            return PermissionDecision(
                allowed=True,
                reason=f"Allowed by rule '{best.path_pattern}' (priority {best.priority})",
                matched_rule=best.path_pattern,
            )

        return PermissionDecision(
            allowed=False,
            reason=f"Operation '{operation}' not permitted by rule '{best.path_pattern}'",
            matched_rule=best.path_pattern,
        )

    # -------------------------------------------------------------------------
    # Rule Matching
    # -------------------------------------------------------------------------

    def _find_matching_rules(
        self,
        rules: List["RulePrimitive"],
        normalized_path: str,
    ) -> List["RulePrimitive"]:
        """Return all rules whose glob pattern matches the path."""
        matched = []
        for rule in rules:
            if self._glob_match(rule.path_pattern, normalized_path):
                matched.append(rule)
        return matched

    def _glob_match(self, pattern: str, path: str) -> bool:
        """
        Match path against a glob pattern.
        Supports: ** (any subdirectory), * (any chars in segment), ?
        """
        # Normalize pattern
        pat = pattern.strip()
        # Remove leading slash consistency
        if not pat.startswith("/"):
            pat = "/" + pat

        # Convert glob to regex
        regex = self._glob_to_regex(pat)
        return bool(regex.match(path))

    def _glob_to_regex(self, pattern: str) -> re.Pattern:
        """Convert a glob pattern to a compiled regex (cached)."""
        cache_key = pattern
        # Simple cache (in production use lru_cache)
        if not hasattr(self, "_cache"):
            self._cache: dict = {}

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Escape special regex chars except glob wildcards
        result = ""
        i = 0
        while i < len(pattern):
            c = pattern[i]
            if c == "*":
                if i + 1 < len(pattern) and pattern[i + 1] == "*":
                    # ** matches everything including /
                    result += ".*"
                    i += 2
                else:
                    # * matches anything except /
                    result += "[^/]*"
                    i += 1
            elif c == "?":
                result += "[^/]"
                i += 1
            elif c in r"\.+^${}|()[]\\":
                result += "\\" + c
                i += 1
            else:
                result += c
                i += 1

        # Anchor: path must start with /
        regex = re.compile(f"^{result}$")
        self._cache[cache_key] = regex
        return regex

    # -------------------------------------------------------------------------
    # Path normalization
    # -------------------------------------------------------------------------

    def _normalize_path(self, path: str) -> str:
        """Sanitize and normalize a path."""
        p = path.strip().strip("/")
        return "/" + p if p else "/"


# =============================================================================
# Rule Primitive (parsed from PermissionRule.to_primitive())
# =============================================================================

@dataclass
class RulePrimitive:
    """
    Parsed representation of a permission rule.
    Created from PermissionRule.to_primitive() string.
    """
    operations: List[str]  # ["read", "write"]
    path_pattern: str       # "/projects/**"
    priority: int = 0

    @classmethod
    def parse(cls, raw: str, priority: int = 0) -> "RulePrimitive":
        """
        Parse a string like 'read,write:/projects/**'
        into an RulePrimitive.
        """
        if ":" in raw:
            perms_str, path = raw.split(":", 1)
            operations = [p.strip() for p in perms_str.split(",") if p.strip()]
        else:
            # No permissions prefix = read-only
            operations = ["read"]
            path = raw
        return cls(operations=operations, path_pattern=path.strip(), priority=priority)


# Import at bottom to avoid circular reference
from .permission_context import PermissionContext
