import asyncio
import json
from _utils import print_response

import aiorequests


def main(*args):
    r = yield from aiorequests.get(
        'http://httpbin.org/redirect/1', allow_redirects=False)
    print(r.original.status)

asyncio.get_event_loop().run_until_complete(main())
