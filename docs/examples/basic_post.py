import asyncio
import json

from _utils import print_response

import aiorequests


def main(*args):
    r = yield from aiorequests.post(
        'http://httpbin.org/post',
        json.dumps({'msg': 'Hello'}),
        headers={'Content-Type': 'application/json'})
    print((yield from r.text()))

asyncio.get_event_loop().run_until_complete(main())
