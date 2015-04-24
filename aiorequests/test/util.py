import os
import asyncio
import platform

import mock

import aiorequests

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
        self.calls.sort(key=lambda a: a.get_time())

    def call_later(self, when, what, *a, **kw):
        dc = asyncio.Handle(self.time() + when,
                          what, a, kw,
                          self.calls.remove,
                          lambda c: None,
                          self.time)
        self.calls.append(dc)
        self._sortCalls()
        return dc

    def call_at(self, when, callback, *args):
        pass

    def time(self):
        return self.right_now

    def advance(self, amount):
        self.right_now += amount
        self._sort_calls()
        while self.calls and self.calls[0].getTime

    def pump(self, timings):
        pass
