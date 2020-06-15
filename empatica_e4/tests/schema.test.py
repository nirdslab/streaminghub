import os
import sys

from core.errors import DoesNotMatchSchemaError
from core.io import get_meta_stream

if __name__ == '__main__':
    print('\n[Test]\nXML schema parsing\n')
    try:
        meta = get_meta_stream(f'{os.path.dirname(__file__)}/../spec.xml', 'xml')
        print(meta)
    except DoesNotMatchSchemaError as e:
        print('ERROR - does not match schema', file=sys.stderr)

    print('\n[Test]\nJSON schema parsing\n')
    try:
        meta = get_meta_stream(f'{os.path.dirname(__file__)}/../spec.json', 'json')
        print(meta)
    except DoesNotMatchSchemaError as e:
        print('ERROR - does not match schema', file=sys.stderr)
