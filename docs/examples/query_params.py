import asyncio
import json
from _utils import print_response

import aiorequests


@asyncio.coroutine
def main():
    print('List of tuples')
    resp = yield from aiorequests.get('http://httpbin.org/get',
                                      params=[('foo', 'bar'), ('baz', 'bax')])
    content = yield from resp.text()
    print(content)

    print('Single value dictionary')
    resp = yield from aiorequests.get('http://httpbin.org/get',
                          params={'foo': 'bar', 'baz': 'bax'})
    content = yield from resp.text()
    print(content)

    print('Multi value dictionary')
    resp = yield from aiorequests.get('http://httpbin.org/get',
                          params={'foo': ['bar', 'baz', 'bax']})
    content = yield from resp.text()
    print(content)

    print('Mixed value dictionary')
    resp = yield from aiorequests.get('http://httpbin.org/get',
                          params={'foo': ['bar', 'baz'], 'bax': 'quux'})
    content = yield from resp.text()
    print(content)

    print('Preserved query parameters')
    resp = yield from aiorequests.get('http://httpbin.org/get?foo=bar',
                          params={'baz': 'bax'})
    content = yield from resp.text()
    print(content)

asyncio.get_event_loop().run_until_complete(main())
