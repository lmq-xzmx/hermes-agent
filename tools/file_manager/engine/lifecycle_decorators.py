"""
Lifecycle constraint decorators.

Provides decorators for declarative constraint checking on service methods.
"""

from functools import wraps
from typing import Callable, Dict, Any, Optional

from .lifecycle_exception import get_lifecycle_engine, LifecycleViolation
from .lifecycle_engine import LifecycleEngine


def lifecycle_constraint(
    action: str,
    context_builder: Callable[..., Dict[str, Any]]
):
    """
    Decorator for lifecycle constraint checking.

    Checks constraints before executing the decorated function.
    If a constraint is violated, raises LifecycleViolation with user guidance.

    Usage:
        @lifecycle_constraint(
            action="delete_pool",
            context_builder=lambda pool_id: {
                "pool_id": pool_id,
                "team_count": get_engine().get_team_count_for_pool(pool_id, db),
            }
        )
        async def delete_pool(pool_id: str):
            ...

    Args:
        action: The action name for constraint lookup.
        context_builder: A callable that builds the context dict from function args.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = context_builder(*args, **kwargs)
            engine = get_lifecycle_engine()
            engine.raise_if_violated(action, context)
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = context_builder(*args, **kwargs)
            engine = get_lifecycle_engine()
            engine.raise_if_violated(action, context)
            return await func(*args, **kwargs)

        # Choose wrapper based on whether function is async
        try:
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
        except ImportError:
            pass

        return sync_wrapper

    return decorator


def pre_check(
    check_fn: Callable[[Dict[str, Any]], bool],
    error: LifecycleViolation
):
    """
    Decorator for simple pre-condition checking.

    Usage:
        @pre_check(
            check_fn=lambda ctx: ctx.get("is_member", False),
            error=LifecycleViolation.not_space_member()
        )
        def upload_file(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Build context from kwargs
            context = kwargs
            if not check_fn(context):
                raise error
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = kwargs
            if not check_fn(context):
                raise error
            return await func(*args, **kwargs)

        try:
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
        except ImportError:
            pass

        return sync_wrapper

    return decorator


def require_membership(space_id_kwarg: str = "space_id", user_id_kwarg: str = "user_id"):
    """
    Decorator that checks if user is a member of the space/team.

    Usage:
        @require_membership()
        def upload_file(user_id: str, space_id: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            engine = get_lifecycle_engine()
            user_id = kwargs.get(user_id_kwarg)
            space_id = kwargs.get(space_id_kwarg)

            if not user_id or not space_id:
                return func(*args, **kwargs)

            db_factory = kwargs.get("_db_factory")
            if db_factory and not engine.check_membership(user_id, space_id, db_factory):
                raise LifecycleViolation.not_space_member(user_id, space_id)

            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            engine = get_lifecycle_engine()
            user_id = kwargs.get(user_id_kwarg)
            space_id = kwargs.get(space_id_kwarg)

            if not user_id or not space_id:
                return await func(*args, **kwargs)

            db_factory = kwargs.get("_db_factory")
            if db_factory and not engine.check_membership(user_id, space_id, db_factory):
                raise LifecycleViolation.not_space_member(user_id, space_id)

            return await func(*args, **kwargs)

        try:
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
        except ImportError:
            pass

        return sync_wrapper

    return decorator


def require_owner(space_id_kwarg: str = "space_id", user_id_kwarg: str = "user_id"):
    """
    Decorator that checks if user is the owner of the space/team.

    Usage:
        @require_owner()
        def invite_member(user_id: str, space_id: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            engine = get_lifecycle_engine()
            user_id = kwargs.get(user_id_kwarg)
            space_id = kwargs.get(space_id_kwarg)

            if not user_id or not space_id:
                return func(*args, **kwargs)

            db_factory = kwargs.get("_db_factory")
            if db_factory and not engine.check_owner(user_id, space_id, db_factory):
                if "team" in space_id_kwarg.lower():
                    raise LifecycleViolation.not_team_owner()
                raise LifecycleViolation.not_space_owner()

            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            engine = get_lifecycle_engine()
            user_id = kwargs.get(user_id_kwarg)
            space_id = kwargs.get(space_id_kwarg)

            if not user_id or not space_id:
                return await func(*args, **kwargs)

            db_factory = kwargs.get("_db_factory")
            if db_factory and not engine.check_owner(user_id, space_id, db_factory):
                if "team" in space_id_kwarg.lower():
                    raise LifecycleViolation.not_team_owner()
                raise LifecycleViolation.not_space_owner()

            return await func(*args, **kwargs)

        try:
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
        except ImportError:
            pass

        return sync_wrapper

    return decorator