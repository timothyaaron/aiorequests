import asyncio
import unittest

import os, tempfile

from io import StringIO

import mock

import aiohttp

from aiorequests.test.util import with_clock

from aiorequests.client import (
    HTTPClient, _BodyBufferingProtocol, _BufferedResponse
)


def async_test(f):
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
    return wrapper

class HTTPClientTests(unittest.TestCase):
    def setUp(self):
        f = asyncio.Future()
        f.set_result(mock.MagicMock())
        aiohttp.request = mock.MagicMock()
        aiohttp.request.return_value = f
        asyncio.coroutines.iscoroutine = mock.MagicMock()
        asyncio.coroutines.iscoroutine.return_value = True

        self.client = HTTPClient()

    def mktemp(self):
        """Returns a unique name that may be used as either a temporary
        directory or filename.

        @note: you must call os.mkdir on the value returned from this
               method if you wish to use it as a directory!
        """
        MAX_FILENAME = 32 # some platforms limit lengths of filenames
        base = os.path.join(self.__class__.__module__[:MAX_FILENAME],
                            self.__class__.__name__[:MAX_FILENAME],
                            self._testMethodName[:MAX_FILENAME])
        if not os.path.exists(base):
            os.makedirs(base)
        dirname = tempfile.mkdtemp('', '', base)
        return os.path.join(dirname, 'temp')

    def assertBody(self, expected):
        body = self.FileBodyProducer.mock_calls[0][1][0]
        self.assertEqual(body.read(), expected)

    @async_test
    def test_request_with_auth(self):
        yield from self.client.request('GET', 'http://example.com/',
                                              auth=('a', 'b'))
        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/',
            headers={'accept-encoding': 'gzip'},
            auth=aiohttp.helpers.BasicAuth('a', 'b')
        )

    @async_test
    def test_request_case_insensitive_methods(self):
        yield from self.client.request('gEt', 'http://example.com/')
        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/',
            headers={'accept-encoding': 'gzip'})

    @async_test
    def test_request_query_params(self):
        yield from self.client.request('GET', 'http://example.com/',
                            params={'foo': 'bar'})

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?foo=bar',
            headers={'accept-encoding': 'gzip'})

    @async_test
    def test_request_merge_query_params(self):
        yield from self.client.request('GET', 'http://example.com/?baz=bax',
                                       params={'foo': ['bar', 'baz']})

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?baz=bax&foo%5B%5D=bar&foo%5B%5D=baz',
            headers={'accept-encoding': 'gzip'})

    @async_test
    def test_request_merge_tuple_query_params(self):
        yield from self.client.request('GET',
                                       'http://example.com/?baz=bax',
                                       params=[('foo', 'bar')])

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?baz=bax&foo=bar',
            headers={'accept-encoding': 'gzip'})

    @async_test
    def test_request_dict_single_value_query_params(self):
        yield from self.client.request('GET', 'http://example.com/',
                                       params={'foo': 'bar'})

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?foo=bar',
            headers={'accept-encoding': 'gzip'})

    @async_test
    def test_request_data_dict(self):
        yield from self.client.request('POST', 'http://example.com/',
                            data={'foo': ['bar', 'baz']})

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={'Content-Type': ['application/x-www-form-urlencoded'],
                     'accept-encoding': 'gzip'}, data='foo=bar&foo=baz')

    @async_test
    def test_request_data_single_dict(self):
        yield from self.client.request('POST', 'http://example.com/',
                            data={'foo': 'bar'})

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={'Content-Type': 'application/x-www-form-urlencoded',
                     'accept-encoding': 'gzip'},
            data='foo=bar')

    @async_test
    def test_request_data_tuple(self):
        yield from self.client.request('POST', 'http://example.com/',
                                       data=[('foo', 'bar')])

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={'Content-Type': 'application/x-www-form-urlencoded',
                     'accept-encoding': 'gzip'},
            data='foo=bar')

    @async_test
    def test_request_data_file(self):
        temp_fn = self.mktemp()

        with open(temp_fn, "w") as temp_file:
            temp_file.write('hello')
        file = open(temp_fn)
        yield from self.client.request('POST', 'http://example.com/', data=file)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={'accept-encoding': 'gzip'},
            data=file)

    @mock.patch('aiorequests.client.uuid.uuid4',
                mock.Mock(return_value="heyDavid"))
    def test_request_no_name_attachment(self):
        f1 = StringIO("hello")
        file = {"name": f1}
        self.client.request(
            'POST', 'http://example.com/', files=file)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={
                'accept-encoding': ['gzip'],
                'Content-Type': ['multipart/form-data; boundary=heyDavid']},
            data=[('name', (None, 'application/octet-stream', f1))])

    @mock.patch('aiorequests.client.uuid.uuid4',
                mock.Mock(return_value="heyDavid"))
    def test_request_named_attachment(self):
        f1 = StringIO("hello")
        data = {"name": ('image.jpg', f1)}
        self.client.request(
            'POST', 'http://example.com/', files=data)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={
                'accept-encoding': ['gzip'],
                'Content-Type': ['multipart/form-data; boundary=heyDavid']},
            data=[('name', ('image.jpg', 'image/jpeg', f1))])

    @mock.patch('aiorequests.client.uuid.uuid4',
                mock.Mock(return_value="heyDavid"))
    def test_request_named_attachment_and_ctype(self):
        f1 = StringIO("hello")
        data = {"name": ('image.jpg', 'text/plain', f1)}
        self.client.request(
            'POST', 'http://example.com/', files=data)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={
                'accept-encoding': ['gzip'],
                'Content-Type': ['multipart/form-data; boundary=heyDavid']},
            data=[('name', ('image.jpg', 'text/plain', f1))])

    @mock.patch('aiorequests.client.uuid.uuid4',
                mock.Mock(return_value="heyDavid"))
    def test_request_mixed_params(self):

        class NamedFile(StringIO):
            def __init__(self, val):
                StringIO.__init__(self, val)
                self.name = "image.png"

        f1 = StringIO("hello")
        f2 = NamedFile("yo")
        files = [
            ("file1", ('image.jpg', f1)),
            ("file2", f2)
                ]
        self.client.request(
            'POST', 'http://example.com/',
            data=[("a", "b"), ("key", "val")],
            files=files)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={
                'accept-encoding': ['gzip'],
                'Content-Type': ['multipart/form-data; boundary=heyDavid']},
            data=[('a', 'b'), ('key', 'val'), ('file1', ('image.jpg',
                                                         'image/jpeg', f1)),
                  ('file2', ('image.png', 'image/png', f2))])

    @mock.patch('aiorequests.client.uuid.uuid4',
                mock.Mock(return_value="heyDavid"))
    def test_request_mixed_params_dict(self):
        parameters = {"key": "a", "key2": "b"}
        files = {"file1": StringIO("hey")}
        self.client.request(
            'POST', 'http://example.com/',
            data=parameters,
            files=files)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={
                'accept-encoding': ['gzip'],
                'Content-Type': ['multipart/form-data; boundary=heyDavid']},
            data=[('key', 'a'), ('key2', 'b')]+list({'file1': (
                None,
                'application/octet-stream', files['file1'])}.items()))

    def test_request_unsupported_params_combination(self):
        self.assertRaises(ValueError,
                          self.client.request,
                          'POST', 'http://example.com/',
                          data=StringIO("yo"),
                          files={"file1": StringIO("hey")})

    def test_request_dict_headers(self):
        self.client.request('GET', 'http://example.com/', headers={
            'User-Agent': 'treq/0.1dev',
            'Accept': ['application/json', 'text/plain']
        })

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/',
            headers={'User-Agent': ['treq/0.1dev'],
                     'accept-encoding': ['gzip'],
                     'Accept': ['application/json', 'text/plain']},
            data=None)

    @with_clock
    def test_request_timeout_fired(self, clock):
        """
        Verify the request is cancelled if a response is not received
        within specified timeout period.
        """
        aiohttp.request.return_value = f = mock.MagicMock()
        self.client.request('GET', 'http://example.com', timeout=2)

        # simulate we haven't gotten a response within timeout seconds
        clock.advance(3)

        # a deferred should have been cancelled
        # MUST assert exception
        f.cancel.assert_called_with()

    @with_clock
    def test_request_timeout_cancelled(self, clock):
        """
        Verify timeout is cancelled if a response is received before
        timeout period elapses.
        """
        aiohttp.request.return_value = f = mock.MagicMock()
        self.client.request('GET', 'http://example.com', timeout=2)

        # simulate a response
        f.set_result(mock.Mock(code=200, headers={}))

        # now advance the clock but since we already got a result,
        # a cancellation timer should have been cancelled

        self.assertFalse(f.called)

    @unittest.skip('Buffering not yet understood')
    def test_response_is_buffered(self):
        response = mock.Mock(deliverBody=mock.Mock(),
                             headers={})

        aiohttp.request.return_value = response

        d = self.client.get('http://www.example.com')

        result = self.successResultOf(d)

        protocol = mock.Mock(Protocol)
        result.deliverBody(protocol)
        self.assertEqual(response.deliverBody.call_count, 1)

        result.deliverBody(protocol)
        self.assertEqual(response.deliverBody.call_count, 1)

    @unittest.skip('Buffering not yet understood')
    def test_response_buffering_is_disabled_with_unbufferred_arg(self):
        response = mock.Mock(headers={})

        aiohttp.request.return_value = response

        d = self.client.get('http://www.example.com', unbuffered=True)

        # YOLO public attribute.
        self.assertEqual(self.successResultOf(d).original, response)


class BodyBufferingProtocolTests(unittest.TestCase):
    def test_buffers_data(self):
        buffer = []
        protocol = _BodyBufferingProtocol(
            mock.Mock(Protocol),
            buffer,
            None
        )

        protocol.dataReceived("foo")
        self.assertEqual(buffer, ["foo"])

        protocol.dataReceived("bar")
        self.assertEqual(buffer, ["foo", "bar"])

    def test_propagates_data_to_destination(self):
        destination = mock.Mock(Protocol)
        protocol = _BodyBufferingProtocol(
            destination,
            [],
            None
        )

        protocol.dataReceived("foo")
        destination.dataReceived.assert_called_once_with("foo")

        protocol.dataReceived("bar")
        destination.dataReceived.assert_called_with("bar")

    def test_fires_finished_deferred(self):
        finished = Deferred()
        protocol = _BodyBufferingProtocol(
            mock.Mock(Protocol),
            [],
            finished
        )

        class TestResponseDone(object):
            pass

        protocol.connectionLost(TestResponseDone())

        self.failureResultOf(finished, TestResponseDone)

    def test_propogates_connectionLost_reason(self):
        destination = mock.Mock(Protocol)
        protocol = _BodyBufferingProtocol(
            destination,
            [],
            Deferred().addErrback(lambda ign: None)
        )

        class TestResponseDone(object):
            pass

        reason = TestResponseDone()
        protocol.connectionLost(reason)
        destination.connectionLost.assert_called_once_with(reason)


class BufferedResponseTests(unittest.TestCase):
    def test_wraps_protocol(self):
        wrappers = []
        wrapped = mock.Mock(Protocol)
        response = mock.Mock(deliverBody=mock.Mock(wraps=wrappers.append))

        br = _BufferedResponse(response)

        br.deliverBody(wrapped)
        response.deliverBody.assert_called_once_with(wrappers[0])
        self.assertNotEqual(wrapped, wrappers[0])

    def test_concurrent_receivers(self):
        wrappers = []
        wrapped = mock.Mock(Protocol)
        unwrapped = mock.Mock(Protocol)
        response = mock.Mock(deliverBody=mock.Mock(wraps=wrappers.append))

        br = _BufferedResponse(response)

        br.deliverBody(wrapped)
        br.deliverBody(unwrapped)
        response.deliverBody.assert_called_once_with(wrappers[0])

        wrappers[0].dataReceived("foo")
        wrapped.dataReceived.assert_called_once_with("foo")

        self.assertEqual(unwrapped.dataReceived.call_count, 0)

        class TestResponseDone(Exception):
            pass

        done = Failure(TestResponseDone())

        wrappers[0].connectionLost(done)
        wrapped.connectionLost.assert_called_once_with(done)
        unwrapped.dataReceived.assert_called_once_with("foo")
        unwrapped.connectionLost.assert_called_once_with(done)

    def test_receiver_after_finished(self):
        wrappers = []
        finished = mock.Mock(Protocol)

        response = mock.Mock(deliverBody=mock.Mock(wraps=wrappers.append))

        br = _BufferedResponse(response)
        br.deliverBody(mock.Mock(Protocol))
        wrappers[0].dataReceived("foo")

        class TestResponseDone(Exception):
            pass

        done = Failure(TestResponseDone())

        wrappers[0].connectionLost(done)

        br.deliverBody(finished)

        finished.dataReceived.assert_called_once_with("foo")
        finished.connectionLost.assert_called_once_with(done)


if __name__ == '__main__':
    unittest.main()
