import asyncio
from _utils import print_response

import aiorequests

def main(*args):
    r = yield from aiorequests.get('http://httpbin.org/get')
    print((yield from r.text()))

asyncio.get_event_loop().run_until_complete(main())
