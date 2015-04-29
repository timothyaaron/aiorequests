Handling Streaming Responses
----------------------------


Query Parameters
----------------

:py:func:`aiorequests.request` supports a ``params`` keyword argument
which will be urlencoded and added to the ``url`` argument in addition
to any query parameters that may already exist.

The ``params`` argument may be either a ``dict`` or a ``list`` of
``(key, value)`` tuples.

If it is a ``dict`` then the values in the dict may either be a ``str`` value
or a ``list`` of ``str`` values.

.. literalinclude:: examples/query_params.py
    :linenos:
    :lines: 7-37

Full example: :download:`query_params.py <examples/query_params.py>`

Auth
----

HTTP Basic authentication as specified in `RFC 2617`_ is easily supported by
passing an ``auth`` keyword argument to any of the request functions.

The ``auth`` argument should be a tuple of the form ``('username', 'password')``.

.. literalinclude:: examples/basic_auth.py
    :linenos:
    :lines: 7-13

Full example: :download:`basic_auth.py <examples/basic_auth.py>`

.. _RFC 2617: http://www.ietf.org/rfc/rfc2617.txt

Redirects
---------

aiorquests handles redirects by default.

The following will print a 200 OK response.

.. literalinclude:: examples/redirects.py
    :linenos:
    :lines: 7-13

Full example: :download:`redirects.py <examples/redirects.py>`

You can easily disable redirects by simply passing `allow_redirects=False` to
any of the request methods.

.. literalinclude:: examples/disable_redirects.py
    :linenos:
    :lines: 7-13

Full example: :download:`disable_redirects.py <examples/disable_redirects.py>`

Cookies
-------

Cookies can be set by passing a ``dict`` or ``cookielib.CookieJar`` instance
via the ``cookies`` keyword argument.  Later cookies set by the server can be
retrieved using the :py:func:`treq.cookies` function.

The the object returned by :py:func:`treq.cookies` supports the same key/value
access as `requests cookies <http://requests.readthedocs.org/en/latest/user/quickstart/#cookies>`_

.. literalinclude:: examples/using_cookies.py
    :linenos:
    :lines: 7-20

Full example: :download:`using_cookies.py <examples/using_cookies.py>`
