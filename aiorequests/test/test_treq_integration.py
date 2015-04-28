import unittest

from StringIO import StringIO

import aiorequests

HTTPBIN_URL = "http://httpbin.org"
HTTPSBIN_URL = "https://httpbin.org"


def todo_relative_redirect(test_method):
    expected_version = Version('twisted', 13, 1, 0)
    if current_version < expected_version:
        test_method.todo = (
            "Relative Redirects are not supported in Twisted versions "
            "prior to: {0}").format(expected_version.short())

    return test_method


@asyncio.coroutine
def print_response(response):
    if DEBUG:
        print()
        print('---')
        print(response.code)
        print(response.headers)
        text = yield from aiorequests.text_content(response)
        print(text)
        print('---')


def with_baseurl(method):
    def _request(self, url, *args, **kwargs):
        return method(self.baseurl + url, *args, pool=self.pool, **kwargs)

    return _request


class AiorequestsIntegrationTests(unittest.TestCase):
    baseurl = HTTPBIN_URL
    get = with_baseurl(aiorequests.get)
    head = with_baseurl(aiorequests.head)
    post = with_baseurl(aiorequests.post)
    put = with_baseurl(aiorequests.put)
    patch = with_baseurl(aiorequests.patch)
    delete = with_baseurl(aiorequests.delete)

    def setUp(self):
        self.pool = HTTPConnectionPool(reactor, False)

    def tearDown(self):
        def _check_fds(_):
            # This appears to only be necessary for HTTPS tests.
            # For the normal HTTP tests then closeCachedConnections is
            # sufficient.
            fds = set(reactor.getReaders() + reactor.getReaders())
            if not [fd for fd in fds if isinstance(fd, Client)]:
                return

            return deferLater(reactor, 0, _check_fds, None)

        return self.pool.closeCachedConnections().addBoth(_check_fds)

    @asyncio.coroutine
    def assert_data(self, response, expected_data):
        body = yield from aiorequests.json_content(response)
        self.assertIn('data', body)
        self.assertEqual(body['data'], expected_data)

    @asyncio.coroutine
    def assert_sent_header(self, response, header, expected_value):
        body = yield from aiorequests.json_content(response)
        self.assertIn(header, body['headers'])
        self.assertEqual(body['headers'][header], expected_value)

    @asyncio.coroutine
    def test_get(self):
        response = yield from self.get('/get')
        self.assertEqual(response.code, 200)
        yield from print_response(response)

    @asyncio.coroutine
    def test_get_headers(self):
        response = yield from self.get('/get', {'X-Blah': ['Foo', 'Bar']})
        self.assertEqual(response.code, 200)
        yield from self.assert_sent_header(response, 'X-Blah', 'Foo,Bar')
        yield from print_response(response)

    @asyncio.coroutine
    def test_get_302_absolute_redirect(self):
        response = yield from self.get(
            '/redirect-to?url={0}/get'.format(self.baseurl))
        self.assertEqual(response.code, 200)
        yield from print_response(response)

    @todo_relative_redirect
    @asyncio.coroutine
    def test_get_302_relative_redirect(self):
        response = yield from self.get('/relative-redirect/1')
        self.assertEqual(response.code, 200)
        yield from print_response(response)

    @asyncio.coroutine
    def test_get_302_redirect_disallowed(self):
        response = yield from self.get('/redirect/1', allow_redirects=False)
        self.assertEqual(response.code, 302)
        yield from print_response(response)

    @asyncio.coroutine
    def test_head(self):
        response = yield from self.head('/get')
        body = yield from aiorequests.content(response)
        self.assertEqual('', body)
        yield from print_response(response)

    @asyncio.coroutine
    def test_head_302_absolute_redirect(self):
        response = yield from self.head(
            '/redirect-to?url={0}/get'.format(self.baseurl))
        self.assertEqual(response.code, 200)
        yield from print_response(response)

    @todo_relative_redirect
    @asyncio.coroutine
    def test_head_302_relative_redirect(self):
        response = yield from self.head('/relative-redirect/1')
        self.assertEqual(response.code, 200)
        yield from print_response(response)

    @asyncio.coroutine
    def test_head_302_redirect_disallowed(self):
        response = yield from self.head('/redirect/1', allow_redirects=False)
        self.assertEqual(response.code, 302)
        yield from print_response(response)

    @asyncio.coroutine
    def test_post(self):
        response = yield from self.post('/post', 'Hello!')
        self.assertEqual(response.code, 200)
        yield from self.assert_data(response, 'Hello!')
        yield from print_response(response)

    @asyncio.coroutine
    def test_multipart_post(self):
        class FileLikeObject(StringIO):
            def __init__(self, val):
                StringIO.__init__(self, val)
                self.name = "david.png"

            def read(*args, **kwargs):
                return StringIO.read(*args, **kwargs)

        response = yield from self.post(
            '/post',
            data={"a": "b"},
            files={"file1": FileLikeObject("file")})
        self.assertEqual(response.code, 200)

        body = yield from aiorequests.json_content(response)
        self.assertEqual('b', body['form']['a'])
        self.assertEqual('file', body['files']['file1'])
        yield from print_response(response)

    @asyncio.coroutine
    def test_post_headers(self):
        response = yield from self.post(
            '/post',
            '{msg: "Hello!"}',
            headers={'Content-Type': ['application/json']}
        )

        self.assertEqual(response.code, 200)
        yield from self.assert_sent_header(
            response, 'Content-Type', 'application/json')
        yield from self.assert_data(response, '{msg: "Hello!"}')
        yield from print_response(response)

    @asyncio.coroutine
    def test_put(self):
        response = yield from self.put('/put', data='Hello!')
        yield from print_response(response)

    @asyncio.coroutine
    def test_patch(self):
        response = yield from self.patch('/patch', data='Hello!')
        self.assertEqual(response.code, 200)
        yield from self.assert_data(response, 'Hello!')
        yield from print_response(response)

    @asyncio.coroutine
    def test_delete(self):
        response = yield from self.delete('/delete')
        self.assertEqual(response.code, 200)
        yield from print_response(response)

    @asyncio.coroutine
    def test_gzip(self):
        response = yield from self.get('/gzip')
        self.assertEqual(response.code, 200)
        yield from print_response(response)
        json = yield from aiorequests.json_content(response)
        self.assertTrue(json['gzipped'])

    @asyncio.coroutine
    def test_basic_auth(self):
        response = yield from self.get('/basic-auth/treq/treq',
                                  auth=('treq', 'treq'))
        self.assertEqual(response.code, 200)
        yield from print_response(response)
        json = yield from aiorequests.json_content(response)
        self.assertTrue(json['authenticated'])
        self.assertEqual(json['user'], 'treq')

    @asyncio.coroutine
    def test_failed_basic_auth(self):
        response = yield from self.get('/basic-auth/treq/treq',
                                  auth=('not-treq', 'not-treq'))
        self.assertEqual(response.code, 401)
        yield from print_response(response)

    @asyncio.coroutine
    def test_timeout(self):
        """
        Verify a timeout fires if a request takes too long.
        """
        yield from self.assertFailure(self.get('/delay/2', timeout=1),
                                 CancelledError,
                                 ResponseFailed)

    @asyncio.coroutine
    def test_cookie(self):
        response = yield from self.get('/cookies', cookies={'hello': 'there'})
        self.assertEqual(response.code, 200)
        yield from print_response(response)
        json = yield from aiorequests.json_content(response)
        self.assertEqual(json['cookies']['hello'], 'there')

    @asyncio.coroutine
    def test_set_cookie(self):
        response = yield from self.get('/cookies/set',
                                  allow_redirects=False,
                                  params={'hello': 'there'})
        #self.assertEqual(response.code, 200)
        yield from print_response(response)
        self.assertEqual(response.cookies()['hello'], 'there')


class HTTPSAiorequestsIntegrationTests(AiorequestsIntegrationTests):
    baseurl = HTTPSBIN_URL
