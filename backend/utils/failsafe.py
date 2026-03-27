import functools
import logging
from typing import TypeVar, Callable, Any

logger = logging.getLogger("urbanmind.failsafe")

F = TypeVar("F", bound=Callable[..., Any])


def failsafe(default: Any = None, log_error: bool = True) -> Callable[[F], F]:
    """
    Decorator that catches all exceptions, logs them,
    and returns a default value instead of crashing.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        "Failsafe caught error in %s: %s", func.__name__, e
                    )
                return default

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        "Failsafe caught error in %s: %s", func.__name__, e
                    )
                return default

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert to int."""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
