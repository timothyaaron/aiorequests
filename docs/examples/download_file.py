import asyncio
import json
from _utils import print_response

import aiorequests

def download_file(*args):
    url, destination_filename = 'http://httpbin.org/get', 'download.txt'
    destination = open(destination_filename, 'wb')
    r = yield from aiorequests.get(url)
    destination.write((yield from r.text()))
    destination.close()

asyncio.get_event_loop().run_until_complete(download_file())
