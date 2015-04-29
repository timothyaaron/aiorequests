.. aiorequests documentation master file, created by
   sphinx-quickstart on Mon Dec 10 22:32:11 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

aiorequests: High-level asyncio HTTP Client API
========================================

aiorequests depends on ``aiohttp``.

Why?
----

`requests`_ by `Kenneth Reitz`_ is a wonderful library.  I want the
same ease of use when writing asyncio applications.  aiorequests is
not of course a perfect clone of `requests`.  `aiorequests` is based
on `treq` and aims to implement the request API.

.. _requests: http://python-requests.org/
.. _Kenneth Reitz: https://www.gittip.com/kennethreitz/
.. _Twisted: http://twistedmatrix.com/
.. _treq: https://github.com/twisted/treq

Quick Start
-----------
Installation::

    pip install aiorequests

GET
+++

.. literalinclude:: examples/basic_get.py
    :linenos:
    :lines: 7-11

Full example: :download:`basic_get.py <examples/basic_get.py>`

POST
++++

.. literalinclude:: examples/basic_post.py
    :linenos:
    :lines: 9-14

Full example: :download:`basic_post.py <examples/basic_post.py>`


Why not 100% requests-alike?
----------------------------


Feature Parity w/ Requests
--------------------------

Howto
-----

.. toctree::
    :maxdepth: 3

    howto

API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
