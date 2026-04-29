"""
Permission Engine - RBAC + Path Rules
Core authorization logic for Hermes File Manager
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Set
from pathlib import Path
import os

from .models import User, Role, PermissionRule, Operation


@dataclass
class PermissionDecision:
    """Result of a permission check"""
    allowed: bool
    reason: str
    matched_rule: Optional[PermissionRule] = None
    required_permissions: Set[str] = field(default_factory=set)
    granted_permissions: Set[str] = field(default_factory=set)


@dataclass 
class PathMatch:
    """Result of path pattern matching"""
    matched: bool
    pattern: str
    matched_segments: int = 0
    total_segments: int = 0


class PermissionEngine:
    """
    Permission engine with RBAC + Path glob rules
    
    Algorithm:
    1. Collect all rules applicable to user's role(s)
    2. Filter to rules where path_pattern matches target path
    3. Sort by priority (descending)
    4. Return first matching rule's permissions
    5. If no match -> DENY
    """
    
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root).resolve()
        self._pattern_cache: dict = {}
    
    def check_permission(
        self,
        user: User,
        operation: Operation,
        path: str,
        role_rules: List[PermissionRule] = None,
    ) -> PermissionDecision:
        """
        Main permission check entry point
        
        Args:
            user: User making the request
            operation: The operation being attempted
            path: The file/directory path being accessed
            role_rules: List of PermissionRules from user's role(s)
        """
        # Admin bypass
        if user.role and user.role.name == "admin":
            return PermissionDecision(
                allowed=True,
                reason="Admin user has full access",
                required_permissions={operation.value},
                granted_permissions={"read", "write", "delete", "manage", "list"}
            )
        
        if role_rules is None:
            role_rules = []
        
        # Normalize path
        normalized = self._normalize_path(path)
        
        # Find matching rules
        matching_rules = self._find_matching_rules(role_rules, normalized)
        
        if not matching_rules:
            return PermissionDecision(
                allowed=False,
                reason=f"No rule matches path '{path}' for user '{user.username}'",
                required_permissions={operation.value},
                granted_permissions=set()
            )
        
        # Sort by priority (highest first)
        sorted_rules = sorted(matching_rules, key=lambda r: r.priority, reverse=True)
        best_rule = sorted_rules[0]
        
        # Check if operation is allowed
        allowed_ops = best_rule.get_permissions()
        if operation.value in allowed_ops or "manage" in allowed_ops:
            # 'manage' implies all operations
            return PermissionDecision(
                allowed=True,
                reason=f"Allowed by rule '{best_rule.path_pattern}' (priority {best_rule.priority})",
                matched_rule=best_rule,
                required_permissions={operation.value},
                granted_permissions=set(allowed_ops)
            )
        
        return PermissionDecision(
            allowed=False,
            reason=f"Operation '{operation.value}' not permitted by rule '{best_rule.path_pattern}'",
            matched_rule=best_rule,
            required_permissions={operation.value},
            granted_permissions=set(allowed_ops)
        )
    
    def check_path_access(
        self,
        user: User,
        path: str,
        role_rules: List[PermissionRule],
        require_write: bool = False
    ) -> PermissionDecision:
        """Convenience method for file operations"""
        op = Operation.WRITE if require_write else Operation.READ
        return self.check_permission(user, op, path, role_rules)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize and sanitize a path"""
        # Remove leading/trailing whitespace and slashes
        path = path.strip().strip("/")
        
        # Block dangerous parent-directory traversals
        if ".." in path:
            raise PermissionError(f"Path traversal not allowed: '{path}'")
        
        # Strip leading ./ — these are not path traversal attacks
        path = path.lstrip("./")
        
        # Split and filter . and empty parts
        parts = [p for p in path.split("/") if p and p != "."]
        
        return "/".join(parts)
    
    def _find_matching_rules(
        self,
        rules: List[PermissionRule],
        normalized_path: str
    ) -> List[PermissionRule]:
        """Find all rules that match the given path"""
        matches = []
        
        for rule in rules:
            if self._path_matches_pattern(normalized_path, rule.path_pattern):
                matches.append(rule)
        
        return matches
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if path matches glob pattern using Python's fnmatch translation.

        Supports:
            *     - matches anything except /
            **    - matches zero or more complete path segments
            ?     - matches single character
            [abc] - matches character class
        """
        # Normalize pattern
        pattern = pattern.strip().strip("/")

        # Use cached result if available
        cache_key = (pattern, path)
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]

        # Use fnmatch.translate to convert glob pattern to regex,
        # then fullmatch to ensure the entire path matches.
        # fnmatch's ** (as .* in translate) correctly matches across / boundaries.
        regex_pattern = fnmatch.translate(pattern)
        try:
            matched = re.fullmatch(regex_pattern, path) is not None
        except re.error:
            # Fallback for any edge-case regex errors
            matched = fnmatch.fnmatch(path, pattern)

        self._pattern_cache[cache_key] = matched
        return matched
    
    def _glob_to_regex(self, pattern: str) -> str:
        """
        Convert glob pattern (with *, **, ?, [...]) to a fullmatch regex string.

        ** matches zero or more complete path segments (i.e. any number of /<name> chunks).
        A segment must be non-empty and cannot cross a /.

        Strategy: split by ** (preserving the ** markers), process each
        non-** segment as a whole with _glob_part_to_regex, then join.
        """
        if "**" not in pattern:
            return "^" + self._glob_part_to_regex(pattern) + "$"

        # Split the pattern into literal parts and ** markers.
        # e.g. "shared/**/docs/**" -> ["shared", "", "docs", ""]
        # After split, we lost the ** markers — reconstruct from original pattern
        parts = pattern.split("**")
        # parts[0]="shared", parts[1]="", parts[2]="docs", parts[3]=""

        regex_parts = []
        for idx, part in enumerate(parts):
            # Strip trailing slash — it's an artifact of splitting by **,
            # not a real path separator we want to include in the regex.
            part_clean = part.rstrip("/")
            if part_clean:
                # Need separator if previous ** consumed a segment name
                # (prev part non-empty means "**" directly followed a path segment)
                if regex_parts and parts[idx - 1]:
                    regex_parts.append("/")
                regex_parts.append(self._glob_part_to_regex(part_clean))
            if idx < len(parts) - 1:
                # There is a ** after this part
                if not part:
                    # Leading ** (empty part): match zero or more complete path segments
                    # without requiring a leading / (fnmatch ** = .*. in regex)
                    regex_parts.append("(?:.+/)*")
                elif part.endswith("/"):
                    # Part ends with /: separator already accounted
                    regex_parts.append("(?:/[^/]+)*")
                else:
                    # Part is a segment name before ** (e.g. "shared**")
                    regex_parts.append("(?:/[^/]+)*")

        return "^" + "".join(regex_parts) + "$"
    
    def _glob_part_to_regex(self, part: str) -> str:
        """Convert a single glob part (no **) to regex"""
        result = []
        i = 0
        while i < len(part):
            char = part[i]
            if char == "*":
                # * matches anything except /
                result.append("[^/]*")
            elif char == "?":
                result.append("[^/]")
            elif char == "[":
                # Character class
                j = i + 1
                if j < len(part) and part[j] == "!":
                    j += 1
                while j < len(part) and part[j] != "]":
                    j += 1
                char_class = part[i:j+1]
                # Convert ! to ^ for negation
                if char_class.startswith("[!"):
                    char_class = "[^" + char_class[2:]
                result.append(char_class)
                i = j
            else:
                # Escape special regex characters
                if char in r"\^$.|+(){}":
                    result.append("\\" + char)
                else:
                    result.append(char)
            i += 1
        return "".join(result)
    
    def resolve_path(self, user_path: str, base_path: Optional[str] = None) -> Path:
        """
        Safely resolve a user path against storage root
        
        Raises:
            PermissionError: If path would escape storage root
        """
        import os
        base = Path(base_path) if base_path else self.storage_root
        
        # Normalize user path
        user_path = self._normalize_path(user_path)
        
        # Join paths then get absolute form (NOT .resolve() which follows symlinks
        # and can incorrectly expand ".." past the base directory on some OS layouts)
        joined = os.path.abspath(str(base / user_path))
        base_abs = os.path.abspath(str(base))
        
        # Ensure joined path is within base directory
        if not joined.startswith(base_abs + os.sep) and joined != base_abs:
            raise PermissionError(
                f"Path '{user_path}' would escape base directory '{base_abs}'"
            )
        
        return Path(joined)
    
    def list_accessible_paths(
        self,
        user: User,
        role_rules: List[PermissionRule],
        base_path: Optional[str] = None
    ) -> List[str]:
        """
        List all paths the user can potentially access
        
        Useful for UI to show accessible directories
        """
        accessible = []
        seen = set()
        
        for rule in role_rules:
            pattern = rule.path_pattern
            # Extract top-level paths from patterns
            if pattern.startswith("/"):
                pattern = pattern[1:]
            
            top_level = pattern.split("/")[0].split("**")[0]
            if top_level and top_level not in seen:
                # Only add if user has some permission
                if rule.get_permissions():
                    accessible.append(top_level)
                    seen.add(top_level)
        
        return sorted(accessible)


class RoleHierarchy:
    """
    Manages role hierarchies and inheritance
    
    Example:
        editor inherits from viewer
        admin inherits from editor
    """
    
    INHERITANCE_MAP = {
        "admin": ["editor", "viewer", "guest"],
        "editor": ["viewer", "guest"],
        "viewer": ["guest"],
        "guest": [],
    }
    
    @classmethod
    def get_all_permissions(cls, role_name: str) -> Set[str]:
        """Get all permissions including inherited ones"""
        permissions = set()
        
        # Direct permissions based on role
        if role_name == "admin":
            permissions = {"read", "write", "delete", "manage", "list"}
        elif role_name == "editor":
            permissions = {"read", "write", "list"}
        elif role_name == "viewer":
            permissions = {"read", "list"}
        elif role_name == "guest":
            permissions = {"read"}
        
        return permissions
    
    @classmethod
    def can_manage_role(cls, manager_role: str, target_role: str) -> bool:
        """Check if a role can manage another role"""
        if manager_role == "admin":
            return True
        # Editors can manage viewers/guests but not admins or other editors
        if manager_role == "editor" and target_role in ("viewer", "guest"):
            return True
        return False


def create_engine(storage_root: str) -> PermissionEngine:
    """Factory function to create a permission engine"""
    return PermissionEngine(storage_root)
