import os


def get_datasource_dir():
  return get_meta_dir('datasources')


def get_dataset_dir():
  return get_meta_dir('datasets')


def get_analytic_dir():
  return get_meta_dir('analytics')


def get_meta_dir(sub_folder: str = None):
  base_dir = os.getenv('STREAMINGHUB_META_DIR')
  if sub_folder is not None:
    base_dir = os.path.join(base_dir, sub_folder)
  if os.path.exists(base_dir):
    return base_dir
  else:
    return None


def get_data_dir():
  base_dir = os.getenv('STREAMINGHUB_DATA_DIR')
  if os.path.exists(base_dir):
    return base_dir
  else:
    return None
