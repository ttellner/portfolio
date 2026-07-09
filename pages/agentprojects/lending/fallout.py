"""Graceful fallback decorator for agent tool calls (fallout handling)."""

import functools
import time


def with_fallout(fallback_value=None, max_retries: int = 0, chapter_ref: str = ""):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = max_retries + 1
            ref = f" ({chapter_ref})" if chapter_ref else ""
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempt < attempts - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return fallback_value
            return fallback_value

        return wrapper

    return decorator
