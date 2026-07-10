"""Graceful fallback decorator for agent tool calls (fallout handling)."""

import functools
import time
from typing import Any


def coalesce(mapping: dict, key: str, default: Any) -> Any:
    """Return mapping[key] unless the value is missing or None."""
    value = mapping.get(key, default)
    return default if value is None else value


def with_fallout(
    fallback_value=None,
    max_retries: int = 0,
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = max_retries + 1
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt < attempts - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return fallback_value
            return fallback_value

        return wrapper

    return decorator
