from requests.cookies import cookiejar_from_dict

from aiorequests.content import content, json_content, text_content


# TODO: almost deprecated with the aiohttp native response
class _Response(object):
    def __init__(self, original, cookiejar):
        self.original = original
        self._cookiejar = cookiejar

        self.url = self.original.url

        self._encoding = None

    def _get_encoding(self):
        if self._encoding:
            return self._encoding
        self.original._get_encoding()

    encoding = property(_get_encoding)

    def content(self):
        return content(self.original)

    def json(self, *args, **kwargs):
        return (yield from self.original.json())

    def text(self, *args, **kwargs):
        return (yield from self.original.text())

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
