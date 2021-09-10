#!/usr/bin/env python3
import asyncio
import logging
import sys
import unittest

from datamux.proxy_websocket import ERROR_BAD_REQUEST, consume

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


class TestProxyWebsocket(unittest.TestCase):

  def test_consumer_search_command(self):
    """
    Test if a search command is processed as expected
    """
    response = asyncio.get_event_loop().run_until_complete(consume({"command": "search"}))
    self.assertEqual(response["command"], "search")
    self.assertNotEqual(response["data"], None)
    self.assertEqual(response["error"], None)

  def test_consumer_invalid_command(self):
    """
    Test if an unknown command is processed as expected
    """
    response = asyncio.get_event_loop().run_until_complete(consume({"command": "foo"}))
    self.assertEqual(response["command"], None)
    self.assertEqual(response["data"], None)
    self.assertEqual(response["error"], ERROR_BAD_REQUEST)

  def test_consumer_subscribe_command(self):
    """
    Test if a subscribe command will start receiving data
    """
    # TODO
    self.assertEqual(True, True)


if __name__ == '__main__':
  unittest.main()
