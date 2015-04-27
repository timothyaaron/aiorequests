import unittest
import asyncio

import mock

from aiorequests._utils import default_loop, default_pool, set_global_pool


class DefaultReactorTests(unittest.TestCase):
    def test_passes_reactor(self):
        mock_loop = mock.Mock()

        self.assertEqual(default_loop(mock_loop), mock_loop)

    def test_uses_default_loop(self):
        loop = asyncio.get_event_loop()
        self.assertEqual(default_loop(None), loop)


class DefaultPoolTests(unittest.TestCase):
    def setUp(self):
        set_global_pool(None)

        pool_patcher = mock.patch('aiorequests._utils.ClientSession')

        self.HTTPConnectionPool = pool_patcher.start()
        self.addCleanup(pool_patcher.stop)

        self.reactor = mock.Mock()

    @unittest.skip('Must skip until persistence is checked')
    def test_persistent_false(self):
        self.assertEqual(
            default_pool(self.reactor, None, False),
            self.HTTPConnectionPool.return_value
        )

        self.HTTPConnectionPool.assert_called_once_with(
            self.reactor, persistent=False
        )

    @unittest.skip('Must skip until persistence is checked')
    def test_pool_none_persistent_none(self):
        self.assertEqual(
            default_pool(self.reactor, None, None),
            self.HTTPConnectionPool.return_value
        )

        self.HTTPConnectionPool.assert_called_once_with(
            self.reactor, persistent=True
        )

    @unittest.skip('Must skip until persistence is checked')
    def test_pool_none_persistent_true(self):
        self.assertEqual(
            default_pool(self.reactor, None, True),
            self.HTTPConnectionPool.return_value
        )

        self.HTTPConnectionPool.assert_called_once_with(
            self.reactor, persistent=True
        )

    def test_cached_global_pool(self):
        pool1 = default_pool(self.reactor, None, None)

        self.HTTPConnectionPool.return_value = mock.Mock()

        pool2 = default_pool(self.reactor, None, True)

        self.assertEqual(pool1, pool2)

    def test_specified_pool(self):
        pool = mock.Mock()

        self.assertEqual(
            default_pool(self.reactor, pool, None),
            pool
        )

        self.HTTPConnectionPool.assert_not_called()
