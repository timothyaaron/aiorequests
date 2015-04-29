Making Requests
===============

.. module:: aiorequests

.. autofunction:: request
.. autofunction:: get
.. autofunction:: head
.. autofunction:: post
.. autofunction:: put
.. autofunction:: patch
.. autofunction:: delete

Responses
=========

.. module:: aiorequests.response

.. class:: Response

    .. method:: collect(collector)

        Incrementally collect the body of the response.

        :param collector: A single argument callable that will be called
            with chunks of body data as it is received.

        :returns: A `Deferred` that fires when the entire body has been
            received.

    .. method:: content()

        Read the entire body all at once.

        :returns: A `Deferred` that fires with a `bytes` object when the entire
            body has been received.

    .. method:: text(encoding='ISO-8859-1')

        Read the entire body all at once as text.
        :param encoding: An encoding for the body, if none is given the
            encoding will be guessed, defaulting to this argument.

        :returns: A `Deferred` that fires with a `unicode` object when the
            entire body has been received.

    .. method:: json()

        Read the entire body all at once and decode it as JSON.

        :returns: A `Deferred` that fires with the result of `json.loads` on
            the body after it has been received.

    .. method:: history()

        Get a list of all responses that (such as intermediate redirects),
        that ultimately ended in the current response.

        :returns: A `list` of :class:`aiorquests.response.Response` objects.

    .. method:: cookies()

        :returns: A `CookieJar`.
