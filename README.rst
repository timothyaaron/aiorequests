aiorequests
===========

|build|_

``aiorequests`` is an HTTP library inspired by
`requests <http://www.python-requests.org>`_ but written on top of
`asyncio <http://www.twistedmatrix.com>`_'s

aiorequests is based on `treq <http://github.com/dred/treq>` , the
requests API for twisted.

It provides a simple, higher level API for making HTTP requests when
using Twisted.

.. code-block:: python

    >>> from aiorequests import get

    >>> def main():
    ...     resp = yield from get("http://www.github.com")
    ...     resp.status
    ...     reactor.stop()

    >>>

    >>> from aysncio import get_event_loop
    >>> get_event_loop().run_until_complete(main())
    200

For more info `read the docs <http://treq.readthedocs.org>`_.

Contribute
==========

``aiorequests`` is hosted on `GitHub <http://github.com/jsandovalc/aiorequests>`_.

Feel free to fork and send contributions over.
