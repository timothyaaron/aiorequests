from requests.cookies import cookiejar_from_dict

from aiorequests.content import content, json_content, text_content


# TODO: almost deprecated with the aiohttp native response
class _Response(object):
    def __init__(self, original, cookiejar):
        self.original = original
        self._cookiejar = cookiejar

        self.url = self.original.url
        self.status_code = self.original.status
        self.version = self.original.version
        self.reason = self.original.reason
        self.headers = self.original.headers
        self._encoding = None

    def _get_encoding(self):
        if self._encoding:
            return self._encoding
        return self.original._get_encoding('utf-8')

    def _set_encoding(self, encoding):
        self._encoding = encoding

    encoding = property(_get_encoding, _set_encoding)

    def content(self):
        return (yield from self.original.read())

    def json(self, *args, **kwargs):
        if 'encoding' not in kwargs:
            kwargs['encoding'] = self.encoding
        return (yield from self.original.json(*args, **kwargs))

    def text(self, *args, **kwargs):
        if 'encoding' not in kwargs:
            kwargs['encoding'] = self.encoding
        return (yield from self.original.text(*args, **kwargs))

    def history(self):
        response = self
        history = []

        while response.previousResponse is not None:
            history.append(_Response(response.previousResponse,
                                     self._cookiejar))
            response = response.previousResponse

        history.reverse()
        return history

    def cookies(self):
        jar = cookiejar_from_dict({})

        if self._cookiejar is not None:
            for cookie in self._cookiejar:
                jar.set_cookie(cookie)

        return jar
