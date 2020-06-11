import urllib.request
from typing import IO

from lxml import etree as ET


class Validator:
    # Temporary file directory
    temp_dir = '/tmp'
    # XSD file names
    base_uri = 'https://raw.githubusercontent.com/nirdslab/dfs/master/schemas/xml'
    meta_stream_xsd = f'meta-stream.xsd'
    meta_file_xsd = 'meta-file.xsd'
    dfs_xsd = 'dfs.xsd'
    analytic_stream_xsd = 'analytic-stream.xsd'
    xsd_files = [dfs_xsd, meta_stream_xsd, analytic_stream_xsd, meta_file_xsd]
    # Loaded state
    loaded = False

    def load(self):
        for file in self.xsd_files:
            with urllib.request.urlopen(f'{self.base_uri}/{file}') as remote:
                remote: IO
                with open(f'{self.temp_dir}/{file}', 'w') as local:
                    local.buffer.write(remote.read())
        self.loaded = True

    def read(self, schema: ET.XMLSchema, url: str, validate=True) -> ET:
        if not self.loaded:
            self.load()
        with open(url) as metadata:
            tree = ET.parse(metadata)
            if validate:
                schema = ET.XMLSchema(file=f'{self.temp_dir}/{self.meta_file_xsd}')
                schema.assertValid(tree)
            return tree


def get_metadata():
    # Get schema and metadata
    validator = Validator()
    validator.validate_and_return('spec.xml')


if __name__ == '__main__':
    get_metadata()
