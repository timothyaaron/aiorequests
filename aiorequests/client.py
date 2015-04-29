import mimetypes
import uuid
import asyncio
import functools

from io import BytesIO, StringIO
from os import path

from urllib.parse import urlparse, urlunparse, urlencode

import aiohttp

from aiorequests._utils import default_loop
from aiorequests.auth import add_auth
from aiorequests.response import _Response

from http.cookiejar import CookieJar
from requests.cookies import cookiejar_from_dict, merge_cookies


class _BodyBufferingProtocol(object):
    def __init__(self, original, buffer, finished):
        self.original = original
        self.buffer = buffer
        self.finished = finished

    def dataReceived(self, data):
        self.buffer.append(data)
        self.original.dataReceived(data)

    def connectionLost(self, reason):
        self.original.connectionLost(reason)
        self.finished.errback(reason)


class _BufferedResponse(object):
    def __init__(self, original):
        self.original = original
        self._buffer = []
        self._waiters = []
        self._waiting = None
        self._finished = False
        self._reason = None

    def _deliverWaiting(self, reason):
        self._reason = reason
        self._finished = True
        for waiter in self._waiters:
            for segment in self._buffer:
                waiter.dataReceived(segment)
            waiter.connectionLost(reason)

    def deliverBody(self, protocol):
        if self._waiting is None and not self._finished:
            self._waiting = Deferred()
            self._waiting.addBoth(self._deliverWaiting)
            self.original.deliverBody(
                _BodyBufferingProtocol(
                    protocol,
                    self._buffer,
                    self._waiting
                )
            )
        elif self._finished:
            for segment in self._buffer:
                protocol.dataReceived(segment)
            protocol.connectionLost(self._reason)
        else:
            self._waiters.append(protocol)


class HTTPClient(object):
    def __init__(self, cookiejar=None):
        self._cookiejar = cookiejar or cookiejar_from_dict({})

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request('PUT', url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.request('PATCH', url, data=data, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.request('POST', url, data=data, **kwargs)

    def head(self, url, **kwargs):
        return self.request('HEAD', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)

    def options(self, url, **kwargs):
        return self.request('OPTIONS', url, **kwargs)

    def request(self, method, url, **kwargs):
        method = method.upper()

        # Join parameters provided in the URL
        # and the ones passed as argument.
        params = kwargs.get('params')
        if params:
            url = _combine_query_params(url, params)

        # Convert headers dictionary to
        # twisted raw headers format.
        headers = kwargs.get('headers')
        if headers:
            _headers = []
            for key, val in headers.items():
                if isinstance(val, list):
                    for v in val:
                        _headers.append((key, v))
                else:
                    _headers.append((key, val))
            headers = _headers
        else:
            headers = {}


        # Here we choose a right producer
        # based on the parameters passed in.
        data = kwargs.get('data')
        files = kwargs.get('files')
        if files:
            # If the files keyword is present we will issue a
            # multipart/form-data request as it suits better for cases
            # with files and/or large objects.

            # TODO: Must check multipart aiohttp support
            files = list(_convert_files(files))
            boundary = uuid.uuid4()
            headers['Content-Type'] = ['multipart/form-data; boundary=%s' %
                                       (boundary,)]
            if data:
                data = _convert_params(data)
            else:
                data = []
            data += files
        elif data:
            # Otherwise stick to x-www-form-urlencoded format
            # as it's generally faster for smaller requests.
            if isinstance(data, (dict, list, tuple)):
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                data = urlencode(data, doseq=True)

        cookies = kwargs.get('cookies', {})

        if not isinstance(cookies, CookieJar):
            cookies = cookiejar_from_dict(cookies)

        cookies = merge_cookies(self._cookiejar, cookies)
        allow_redirects = kwargs.get('allow_redirects', True)

        auth = kwargs.get('auth')
        if auth:
            auth = aiohttp.helpers.BasicAuth(*auth)
        else:
            auth = None

        if isinstance(headers, dict):
            headers['accept-encoding'] = 'gzip'
        else:
            headers.append(('accept-encoding', 'gzip'))
        loop = asyncio.get_event_loop()
        timeout = kwargs.get('timeout')

        request_args = {
            'auth': auth,
            'allow_redirects': allow_redirects if not allow_redirects else None,
            'headers': headers,
            'data': data,
            'cookies': cookies if cookies else None
        }

        for k in list(request_args.keys()):
            if not request_args[k]:
                request_args.pop(k)

        resp = yield from asyncio.wait_for(loop.create_task(aiohttp.request(
            method, url, **request_args)), timeout)


        return _Response(resp, cookies)

def _convert_params(params):
    if hasattr(params, "items"):
        return list(sorted(params.items()))
    elif isinstance(params, (tuple, list)):
        return list(params)
    else:
        raise ValueError("Unsupported format")

def _convert_files(files):
    """Files can be passed in a variety of formats:

        * {'file': open("bla.f")}
        * {'file': (name, open("bla.f"))}
        * {'file': (name, content-type, open("bla.f"))}
        * Anything that has iteritems method, e.g. MultiDict:
          MultiDict([(name, open()), (name, open())]

        Our goal is to standardize it to unified form of:

        * [(param, (file name, content type, producer))]
    """

    if hasattr(files, "items"):
        files = files.items()

    for param, val in files:
        file_name, content_type, fobj = (None, None, None)
        if isinstance(val, tuple):
            if len(val) == 2:
                file_name, fobj = val
            elif len(val) == 3:
                file_name, content_type, fobj = val
        else:
            fobj = val
            if hasattr(fobj, "name"):
                file_name = path.basename(fobj.name)

        if not content_type:
            content_type = _guess_content_type(file_name)

        yield (param, (file_name, content_type, fobj))


def _combine_query_params(url, params):
    parsed_url = urlparse(url)

    qs = []
    if parsed_url.query:
        qs.extend([parsed_url.query, '&'])

    qs.append(urlencode(params, doseq=True))

    return urlunparse((parsed_url[0], parsed_url[1],
                       parsed_url[2], parsed_url[3],
                       ''.join(qs), parsed_url[5]))


def _from_bytes(orig_bytes):
    return FileBodyProducer(StringIO(orig_bytes))


def _from_file(orig_file):
    return FileBodyProducer(orig_file)


def _guess_content_type(filename):
    if filename:
        guessed = mimetypes.guess_type(filename)[0]
    else:
        guessed = None
    return guessed or 'application/octet-stream'
