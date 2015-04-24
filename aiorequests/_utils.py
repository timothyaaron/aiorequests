"""
Strictly internal utilities.
"""

import asyncio

def default_loop(loop):
    """
    Return the specified loop or the default.
    """
    return loop


_global_pool = [None]


def get_global_pool():
    return _global_pool[0]


def set_global_pool(pool):
    _global_pool[0] = pool


def default_pool(loop, pool, persistent):
    """
    Return the specified pool or a a pool with the specified loop and
    persistence.
    """
    loop = default_loop(loop)

    if pool is not None:
        return pool

    if persistent is False:
        return HTTPConnectionPool(loop, persistent=persistent)

    if get_global_pool() is None:
        set_global_pool(HTTPConnectionPool(loop, persistent=True))

    return get_global_pool()
