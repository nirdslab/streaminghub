#!/usr/bin/env python3
import unittest

import logging
import sys
from tools.datasource_from_dataset import get_dataset_spec, get_data_stream

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


class TestSimulator(unittest.TestCase):
    test_dataset_name = 'adhd_sin'
    test_dataset_dir = './datasets'

    def test_load_meta_file(self):
        """
        Test if the correct meta-file is loaded for the given arguments
        """
        test_meta_file_format = 'json'
        test_meta_file_checksum = '010203040506070809000A0B0C0D0E0F'
        # load the meta-file
        meta_file = get_dataset_spec(self.test_dataset_dir, self.test_dataset_name, test_meta_file_format)
        # assertion
        self.assertEqual(meta_file.info.checksum, test_meta_file_checksum)

    def test_load_data_file(self):
        """
        Test if the correct data file is loaded for the given arguments
        """
        test_file_name = '003ADHD_AV_01.csv'
        test_file_size = 47232
        # load the data-file
        data_file = get_data_stream(self.test_dataset_dir, self.test_dataset_name, test_file_name)
        # assertion
        self.assertEqual(data_file.size, test_file_size)

    def test_create_meta_streams(self):
        """
        Test if the correct meta-streams are generated from a meta-file
        """
        test_meta_file_format = 'json'
        # load the meta-file
        meta_file = get_dataset_spec(self.test_dataset_dir, self.test_dataset_name, test_meta_file_format)
        meta_streams = create_data_sources(meta_file)
        self.assertEqual(len(meta_streams), len(meta_file.sources.sources))
        for i in range(len(meta_streams)):
            self.assertEqual(meta_streams[i].device, meta_file.sources.sources[i].device)
            self.assertEqual(meta_streams[i].fields, meta_file.fields)
            self.assertEqual(meta_streams[i].streams, meta_file.sources.sources[i].streams)
            # info
            self.assertEqual(meta_streams[i].info.version, meta_file.info.version)
            self.assertEqual(meta_streams[i].info.checksum, meta_file.info.checksum)

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
