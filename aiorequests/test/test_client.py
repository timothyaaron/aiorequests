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


class HTTPClientTests(unittest.TestCase):
    def setUp(self):
        aiohttp.request = mock.Mock()
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

    def test_request_case_insensitive_methods(self):
        self.client.request('gEt', 'http://example.com/')
        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/',
            headers={'accept-encoding': ['gzip']}, data=None)

    def test_request_query_params(self):
        self.client.request('GET', 'http://example.com/',
                            params={'foo': ['bar']})

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?foo=bar',
            headers={'accept-encoding': ['gzip']}, data=None)

    def test_request_tuple_query_values(self):
        self.client.request('GET', 'http://example.com/',
                            params={'foo': ('bar',)})

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?foo=bar',
            headers={'accept-encoding': ['gzip']}, data=None)

    def test_request_merge_query_params(self):
        self.client.request('GET', 'http://example.com/?baz=bax',
                            params={'foo': ['bar', 'baz']})

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?baz=bax&foo=bar&foo=baz',
            headers={'accept-encoding': ['gzip']}, data=None)

    def test_request_merge_tuple_query_params(self):
        self.client.request('GET', 'http://example.com/?baz=bax',
                            params=[('foo', 'bar')])

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?baz=bax&foo=bar',
            headers={'accept-encoding': ['gzip']}, data=None)

    def test_request_dict_single_value_query_params(self):
        self.client.request('GET', 'http://example.com/',
                            params={'foo': 'bar'})

        aiohttp.request.assert_called_once_with(
            'GET', 'http://example.com/?foo=bar',
            headers={'accept-encoding': ['gzip']}, data=None)

    def test_request_data_dict(self):
        self.client.request('POST', 'http://example.com/',
                            data={'foo': ['bar', 'baz']})

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={'Content-Type': ['application/x-www-form-urlencoded'],
                     'accept-encoding': ['gzip']}, data='foo=bar&foo=baz')

    def test_request_data_single_dict(self):
        self.client.request('POST', 'http://example.com/',
                            data={'foo': 'bar'})

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={'Content-Type': ['application/x-www-form-urlencoded'],
                     'accept-encoding': ['gzip']},
            data='foo=bar')

    def test_request_data_tuple(self):
        self.client.request('POST', 'http://example.com/',
                            data=[('foo', 'bar')])

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={'Content-Type': ['application/x-www-form-urlencoded'],
                     'accept-encoding': ['gzip']},
            data='foo=bar')

    def test_request_data_file(self):
        temp_fn = self.mktemp()

        with open(temp_fn, "w") as temp_file:
            temp_file.write('hello')
        file = open(temp_fn)
        self.client.request('POST', 'http://example.com/', data=file)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={'accept-encoding': ['gzip']},
            data=file)

    @mock.patch('aiorequests.client.uuid.uuid4',
                mock.Mock(return_value="heyDavid"))
    def test_request_no_name_attachment(self):
        file = {"name": StringIO("hello")}
        self.client.request(
            'POST', 'http://example.com/', files=file)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={
                'accept-encoding': ['gzip'],
                'Content-Type': ['multipart/form-data; boundary=heyDavid']},
            data=file)

    @mock.patch('aiorequests.client.uuid.uuid4',
                mock.Mock(return_value="heyDavid"))
    def test_request_named_attachment(self):
        data = {"name": ('image.jpg', StringIO("hello"))}
        self.client.request(
            'POST', 'http://example.com/', files=data)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={
                'accept-encoding': ['gzip'],
                'Content-Type': ['multipart/form-data; boundary=heyDavid']},
            data=data)

    @mock.patch('aiorequests.client.uuid.uuid4',
                mock.Mock(return_value="heyDavid"))
    def test_request_named_attachment_and_ctype(self):
        data = {"name": ('image.jpg', 'text/plain', StringIO("hello"))}
        self.client.request(
            'POST', 'http://example.com/', files=data)

        aiohttp.request.assert_called_once_with(
            'POST', 'http://example.com/',
            headers={
                'accept-encoding': ['gzip'],
                'Content-Type': ['multipart/form-data; boundary=heyDavid']},
            data=data)

    @mock.patch('aiorequests.client.uuid.uuid4', mock.Mock(return_value="heyDavid"))
    def test_request_mixed_params(self):

        class NamedFile(StringIO):
            def __init__(self, val):
                StringIO.__init__(self, val)
                self.name = "image.png"

        files = [
            ("file1", ('image.jpg', StringIO("hello"))),
            ("file2", NamedFile("yo"))
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
            data=files)

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
        aiohttp.request.return_value = f = asyncio.Future()
        self.client.request('GET', 'http://example.com', timeout=2)

        # simulate we haven't gotten a response within timeout seconds
        clock.advance(3)

        # a deferred should have been cancelled
        # MUST assert exception
        f.assert_called_with()

    @with_clock
    def test_request_timeout_cancelled(self, clock):
        """
        Verify timeout is cancelled if a response is received before
        timeout period elapses.
        """
        aiohttp.request.return_value = d = Future()
        self.client.request('GET', 'http://example.com', timeout=2)

        # simulate a response
        d.callback(mock.Mock(code=200, headers=Headers({})))

        # now advance the clock but since we already got a result,
        # a cancellation timer should have been cancelled
        clock.advance(3)

        self.successResultOf(d)

    def test_response_is_buffered(self):
        response = mock.Mock(deliverBody=mock.Mock(),
                             headers=Headers({}))

        self.agent.request.return_value = succeed(response)

        d = self.client.get('http://www.example.com')

        result = self.successResultOf(d)

        protocol = mock.Mock(Protocol)
        result.deliverBody(protocol)
        self.assertEqual(response.deliverBody.call_count, 1)

        result.deliverBody(protocol)
        self.assertEqual(response.deliverBody.call_count, 1)

    def test_response_buffering_is_disabled_with_unbufferred_arg(self):
        response = mock.Mock(headers=Headers({}))

        self.agent.request.return_value = succeed(response)

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
