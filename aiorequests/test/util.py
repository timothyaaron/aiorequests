import os
import asyncio
import platform

import mock

import aiorequests

# TODO: Change later
DEBUG = os.getenv("TREQ_DEBUG", False) == "true"

is_pypy = platform.python_implementation() == 'PyPy'

def with_clock(fn):
    def wrapper(*args, **kwargs):
        clock = Clock()
        with mock.patch.object(asyncio.get_event_loop(), 'call_later',
                               clock.call_later):
            return fn(*(args + (clock,)), **kwargs)
    return wrapper


class Clock(object):
    right_now = 0.0
    def __init__(self):
        self.calls = []

    def _sort_calls(self):
        self.calls.sort(key=lambda a: a.time)

    def call_later(self, when, what, *a, **kw):
        self.calls.append((what, a))
        return mock.MagicMock()

    def call_at(self, when, callback, *args):
        pass

    def time(self):
        return self.right_now

    def advance(self, amount):
        """Right now, it executes the next task. The amount is ignored.

        """
        call, args = self.calls.pop(0)
        call(*args)

        self.right_now += amount

    def pump(self, timings):
        pass
