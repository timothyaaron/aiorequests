import asyncio
import json
from _utils import print_response

import aiorequests

def main(*args):
    resp = yield from aiorequests.get('http://httpbin.org/redirect/1')
    print(resp.original.status)

asyncio.get_event_loop().run_until_complete(main())
