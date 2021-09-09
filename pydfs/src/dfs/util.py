import os


def get_meta_dir():
  return os.getenv('STREAMINGHUB_META_DIR')


def get_data_dir():
  return os.getenv('STREAMINGHUB_DATA_DIR')
