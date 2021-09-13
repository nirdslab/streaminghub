#!/usr/bin/env python3
import logging
import sys
import unittest

from datamux.replay import dataset_attrs_and_data
from dfs import get_dataset_spec, create_outlet

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


class TestReplay(unittest.TestCase):

  def setUp(self) -> None:
    super().setUp()
    self.dataset_name = 'adhd_sin'

  def test_load_dataset_spec(self):
    """
    Test if the correct dataset spec is loaded for the given arguments
    """
    # load the dataset spec
    dataset_spec = get_dataset_spec(self.dataset_name)
    # assertion
    self.assertEqual(dataset_spec.info.checksum, '010203040506070809000A0B0C0D0E0F')

  def test_load_dataset_data(self):
    """
    Test if the correct data is returned via the dataset spec+resolver (TODO)
    """
    # ground truth
    source_id = '003ADHD_AV_01.csv'
    # load the dataset spec
    dataset_spec = get_dataset_spec(self.dataset_name)
    # load data via the dataset spec
    for attrs, data_stream in dataset_attrs_and_data(dataset_spec, self.dataset_name):
      # create outlet for every nested attr, and create hierarchy
      outlet = create_outlet  # (source_id, source.device, stream_info, attrs)
    # assertion
    self.assertEqual(False, False)

  def test_create_data_sources(self):
    """
    Test if the correct data sources are generated from a meta-file (TODO)
    """
    test_meta_file_format = 'json'
    # load the meta-file
    dataset_spec = get_dataset_spec(self.dataset_name)
    for attrs, data_stream in dataset_attrs_and_data(dataset_spec, self.dataset_name):
      pass
      # self.assertEqual(len(meta_streams), len(dataset_spec.sources.sources))
      # for i in range(len(meta_streams)):
      #   self.assertEqual(meta_streams[i].device, dataset_spec.sources.sources[i].device)
      #   self.assertEqual(meta_streams[i].fields, dataset_spec.fields)
      #   self.assertEqual(meta_streams[i].streams, dataset_spec.sources.sources[i].streams)
      #   # info
      #   self.assertEqual(meta_streams[i].info.version, dataset_spec.info.version)
      #   self.assertEqual(meta_streams[i].info.checksum, dataset_spec.info.checksum)

  def test_create_streaming_task(self):
    """
    Test if the streaming tasks are correctly generated (TODO)
    """
    self.assertEqual(False, False)

  def test_emit_empty_data(self):
    """
    Test if the emit function completes gracefully when data is empty (TODO)
    """
    self.assertEqual(False, False)

  def test_emit_consumed_all_data(self):
    """
    Test if the emit function completes gracefully when a file is completely consumed (TODO)
    """
    self.assertEqual(False, False)

  def test_simulator_consumer_detach(self):
    """
    Test if the simulator stops sending data when all consumers are detached (TODO)
    """
    self.assertEqual(False, False)

  def test_simulator_consumer_attach(self):
    """
    Test if the simulator starts sending data when a consumer is attached (TODO)
    """
    self.assertEqual(False, False)


if __name__ == '__main__':
  unittest.main()
