"""
Middleware - Rate limiting and request processing
"""

from __future__ import annotations

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """
    Simple in-memory rate limiter
    
    In production, use Redis for distributed rate limiting
    """
    
    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_size: int = 20,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self._requests: Dict[str, list] = defaultdict(list)
        self._cleanup_interval = 300  # Cleanup every 5 minutes
        self._last_cleanup = time.time()
    
    def _get_key(self, request: Request) -> str:
        """Get rate limit key for a request"""
        # Use user ID if authenticated, otherwise use IP
        # For simplicity, use IP for now
        ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP") or
            request.client.host if request.client else "unknown"
        )
        return hashlib.md5(ip.encode()).hexdigest()[:16]
    
    def _cleanup_old_entries(self) -> None:
        """Remove expired entries"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff = now - 60  # Remove entries older than 1 minute
        for key in list(self._requests.keys()):
            self._requests[key] = [t for t in self._requests[key] if t > cutoff]
            if not self._requests[key]:
                del self._requests[key]
        
        self._last_cleanup = now
    
    def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, str]]:
        """
        Check if request is within rate limits
        
        Returns:
            (allowed, headers)
        """
        self._cleanup_old_entries()
        
        key = self._get_key(request)
        now = time.time()
        
        # Get recent requests (within last minute)
        recent = [t for t in self._requests[key] if now - t < 60]
        self._requests[key] = recent
        
        # Check limit
        if len(recent) >= self.requests_per_minute:
            oldest = min(recent) if recent else now
            retry_after = int(60 - (now - oldest))
            return False, {
                "Retry-After": str(max(1, retry_after)),
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(oldest + 60),
            }
        
        # Add current request
        self._requests[key].append(now)
        
        remaining = self.requests_per_minute - len(self._requests[key])
        return True, {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(int(now) + 60),
        }


class LoginRateLimiter:
    """
    Rate limiter specifically for login attempts
    
    Stricter limits to prevent brute force attacks
    """
    
    def __init__(
        self,
        attempts_per_minute: int = 5,
        lockout_duration_minutes: int = 15,
        max_attempts_before_lockout: int = 10,
    ):
        self.attempts_per_minute = attempts_per_minute
        self.lockout_duration = lockout_duration_minutes * 60
        self.max_attempts = max_attempts_before_lockout
        self._attempts: Dict[str, list] = defaultdict(list)
        self._lockouts: Dict[str, float] = {}
    
    def _get_key(self, request: Request) -> str:
        """Get key based on IP and username combo"""
        ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP") or
            request.client.host if request.client else "unknown"
        )
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    def check_login_attempt(self, request: Request) -> None:
        """
        Check if login attempt is allowed
        
        Raises HTTPException if rate limited or locked out
        """
        key = self._get_key(request)
        now = time.time()
        
        # Check lockout
        if key in self._lockouts:
            lockout_until = self._lockouts[key]
            if now < lockout_until:
                retry_after = int(lockout_until - now)
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many login attempts. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )
            else:
                # Lockout expired, reset
                del self._lockouts[key]
                self._attempts[key] = []
        
        # Get recent attempts
        recent = [t for t in self._attempts[key] if now - t < 60]
        self._attempts[key] = recent
        
        if len(recent) >= self.attempts_per_minute:
            oldest = min(recent)
            retry_after = int(60 - (now - oldest))
            raise HTTPException(
                status_code=429,
                detail=f"Too many login attempts. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )
        
        # Record this attempt
        self._attempts[key].append(now)
    
    def record_failed_attempt(self, request: Request) -> None:
        """Record a failed login attempt"""
        key = self._get_key(request)
        now = time.time()
        
        # Get recent attempts
        recent = [t for t in self._attempts[key] if now - t < 60]
        
        # If too many recent failures, activate lockout
        if len(recent) >= self.max_attempts:
            self._lockouts[key] = now + self.lockout_duration
            self._attempts[key] = []
    
    def record_success(self, request: Request) -> None:
        """Clear rate limit on successful login"""
        key = self._get_key(request)
        if key in self._attempts:
            del self._attempts[key]
        if key in self._lockouts:
            del self._lockouts[key]


# Global rate limiter instances
_auth_limiter = LoginRateLimiter()
_api_limiter = RateLimiter(requests_per_minute=100)


def setup_middleware(app):
    """Add middleware to FastAPI app"""
    from starlette.middleware.cors import CORSMiddleware
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_auth_limiter() -> LoginRateLimiter:
    return _auth_limiter


def get_api_limiter() -> RateLimiter:
    return _api_limiter
