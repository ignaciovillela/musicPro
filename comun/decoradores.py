from functools import wraps

from cachetools.func import ttl_cache
from result import Err, Ok, Result


def music_ttl_cache(maxsize=128, ttl=300):
    def decorator(func):
        @wraps(func)
        @ttl_cache(maxsize=maxsize, ttl=ttl)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, (Err, Ok)) and result.is_err():
                wrapper.cache.pop(args, None)
            return result
        return wrapper
    return decorator
