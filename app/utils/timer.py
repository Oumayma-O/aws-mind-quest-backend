import time
import functools
import logging
import inspect


def timer(logger: logging.Logger | None = None):
    """Decorator factory that returns a decorator which logs execution time.

    Supports both async and sync callables. Use like:

        @router.post("/path")
        @timer(logger=logger)
        async def endpoint(...):
            ...

    Note: apply the `timer` decorator *below* (closer to the function) the
    router decorator so FastAPI registers the wrapped function.
    """
    if logger is None:
        logger = logging.getLogger("app.timer")

    def _decorator(func):
        is_coro = inspect.iscoroutinefunction(func)

        if is_coro:
            @functools.wraps(func)
            async def _async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    logger.info(f"{func.__module__}.{func.__name__} executed in {elapsed_ms:.2f} ms")

            return _async_wrapper

        else:
            @functools.wraps(func)
            def _sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    logger.info(f"{func.__module__}.{func.__name__} executed in {elapsed_ms:.2f} ms")

            return _sync_wrapper

    return _decorator
