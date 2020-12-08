#!/usr/bin/env python3
import unittest

from core.types import MetaStream


class TestSimulator(unittest.TestCase):

    def test_load_meta_file(self):
        """
        Test if the correct meta-file is loaded for the given arguments
        """
        # TODO
        self.assertEqual(False, False)

    def test_load_data_file(self):
        """
        Test if the correct data file is loaded for the given arguments
        """
        # TODO
        self.assertEqual(False, False)

    def test_create_meta_streams(self):
        """
        Test if the correct meta-streams are generated from a meta-file
        """
        # TODO
        self.assertEqual(False, False)

    def test_create_streaming_task(self):
        """
        Test if the streaming tasks are correctly generated
        """
        # TODO
        self.assertEqual(False, False)

    def test_emit_empty_data(self):
        """
        Test if the emit function completes gracefully when data is empty
        """
        # TODO
        self.assertEqual(False, False)

    def test_emit_consumed_all_data(self):
        """
        Test if the emit function completes gracefully when a file is completely consumed
        """
        # TODO
        self.assertEqual(False, False)

    def test_simulator_consumer_detach(self):
        """
        Test if the simulator stops sending data when all consumers are detached
        """
        # TODO
        self.assertEqual(False, False)

    def test_simulator_consumer_attach(self):
        """
        Test if the simulator starts sending data when a consumer is attached
        """
        # TODO
        self.assertEqual(False, False)


if __name__ == '__main__':
    unittest.main()
