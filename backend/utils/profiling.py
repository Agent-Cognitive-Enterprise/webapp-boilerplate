# /backend/utils/profiling.py

import functools
import inspect
import logging
import time
from typing import (
    Any,
    Callable,
    Optional,
)


def measure_time(
    __func: Optional[Callable[..., Any]] = None,
    name: Optional[str] = None,
    *,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    warn_over_seconds: Optional[float] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
    """
    Decorator to log execution duration of sync or async functions.

    Supports both usages:
    - `@measure_time`
    - `@measure_time(name, logger=..., level=..., warn_over_seconds=...)`

    - `name`: optional label; defaults to `module.qualname`.
    - `logger`: optional logger; defaults to module logger.
    - `level`: default log level when below a threshold.
    - `warn_over_seconds`: if set and duration >= a threshold, log at WARNING.
    """

    def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        log = logger or logging.getLogger(func.__module__)
        label = name or f"{func.__module__}.{func.__qualname__}"

        def _emit(elapsed: float) -> None:
            human = f"{elapsed*1000:.3f} ms" if elapsed < 1 else f"{elapsed:.3f} s"
            lvl = (
                logging.WARNING
                if (warn_over_seconds and elapsed >= warn_over_seconds)
                else level
            )
            log.log(lvl, "%s took %s", label, human)

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    _emit(time.perf_counter() - start)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                _emit(time.perf_counter() - start)

        return sync_wrapper

    # Handle decorator being used with or without parentheses
    if __func is not None:
        if callable(__func):
            # Used as @measure_time
            return _decorator(__func)
        # Used as @measure_time("label") where the first positional is the name
        if isinstance(__func, str) and name is None:
            name = __func  # bind label for the closure
        return _decorator

    # Used as @measure_time(...)
    return _decorator