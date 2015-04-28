"""
Strictly internal utilities.
"""

import asyncio

from aiohttp import ClientSession

# TODO: Are these functions needed? asyncio implementes something similar
def default_loop(loop):
    """
    Return the specified loop or the default.
    """
    if not loop:
        return asyncio.get_event_loop()
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
        return ClientSession()

    if get_global_pool() is None:
        set_global_pool(ClientSession())

    return get_global_pool()
