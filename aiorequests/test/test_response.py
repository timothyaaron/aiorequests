import unittest

from aiorequests.response import _Response


class FakeResponse(object):
    def __init__(self, code, headers={}):
        self.code = code
        self.headers = headers
        self.previousResponse = None
        self.url = ''

    def _get_encoding(self):
        return 'utf-8'

    def setPreviousResponse(self, response):
        self.previousResponse = response



class ResponseTests(unittest.TestCase):
    def test_get_encoding(self):
        original = FakeResponse(200)
        response = _Response(original, {})
        self.assertEqual(response.encoding, 'utf-8')

    def test_set_encoding(self):
        original = FakeResponse(200)
        response = _Response(original, {})
        response.encoding = 'iso-8891-1'
        self.assertEqual(response.encoding, 'iso-8891-1')


    @unittest.skip('Until history is migrated')
    def test_history(self):
        redirect1 = FakeResponse(
            301,
            headers={'location': ['http://example.com/']}
        )

        redirect2 = FakeResponse(
            302,
            headers={'location': ['https://example.com/']}
        )
        redirect2.setPreviousResponse(redirect1)

        final = FakeResponse(200, {})
        final.setPreviousResponse(redirect2)

        wrapper = _Response(final, None)

        history = wrapper.history()

        self.assertEqual(wrapper.code, 200)
        self.assertEqual(history[0].code, 301)
        self.assertEqual(history[1].code, 302)

    @unittest.skip('Until history is migrated')
    def test_no_history(self):
        wrapper = _Response(FakeResponse(200, {}), None)
        self.assertEqual(wrapper.history(), [])

    @unittest.skip('Until history is migrated')
    def test_history_notimplemented(self):
        wrapper = _Response(FakeResponse(200, {}), None)
        self.assertRaises(NotImplementedError, wrapper.history)
