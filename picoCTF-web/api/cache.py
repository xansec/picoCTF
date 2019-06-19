"""Caching Library using redis."""

import logging
from functools import wraps

from flask import current_app
from walrus import Walrus

import api
import hashlib
import pickle
from api import PicoException

log = logging.getLogger(__name__)

__walrus = None
__cache = None


def get_conn():
    """Get a redis connection, reusing one if it exists."""
    global __walrus
    if not __walrus:
        conf = current_app.config
        try:
            __walrus = Walrus(host=conf["REDIS_ADDR"], port=conf["REDIS_PORT"],
                              password=conf["REDIS_PW"], db=conf["REDIS_DB_NUMBER"])
        except Exception as error:
            raise PicoException(
                'Internal server error. ' +
                'Please contact a system administrator.',
                data={'original_error': error})
    return __walrus


def get_cache():
    """Get a walrus cache, reusing one if it exists."""
    global __cache
    if not __cache:
        __cache = get_conn().cache(default_timeout=0)
    return __cache


def clear():
    global __cache
    if __cache:
        __cache.flush()


def memoize(_f=None, **cached_kwargs):
    """walrus.Cache.cached wrapper that reuses shared cache."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if kwargs.get("reset_cache", False):
                kwargs.pop("reset_cache", None)
                invalidate(f, *args, **kwargs)
            return get_cache().cached(**cached_kwargs)(f)(*args, **kwargs)
        return wrapper
    if _f is None:
        return decorator
    else:
        return decorator(_f)


def _hash_key(a, k):
    return hashlib.md5(pickle.dumps((a, k))).hexdigest()


def invalidate(f, *args, **kwargs):
    """
    Clunky way to replicate busting behavior due to awkward wrapping of walrus cached decorator
    """
    cache = get_cache()
    key = '%s:%s' % (f.__name__, _hash_key(args, kwargs))
    cache.delete(key)
