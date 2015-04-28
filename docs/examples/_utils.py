import aiorequests


def print_response(response):
    print(response.code, response.phrase)
    print(response.headers)

    print((yield from aiorequests.text_content(response)))
