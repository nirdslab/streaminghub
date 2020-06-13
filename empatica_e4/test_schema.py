import sys

from core.errors import DoesNotMatchSchemaError
from core.io import get_meta_stream

if __name__ == '__main__':
    print('\n[Test]\nXML schema parsing\n')
    try:
        meta = get_meta_stream('empatica_e4/spec.xml', 'xml')
        print(meta)
    except DoesNotMatchSchemaError as e:
        print('ERROR - does not match schema', file=sys.stderr)

    print('\n[Test]\nJSON schema parsing\n')
    try:
        meta = get_meta_stream('empatica_e4/spec.json', 'json')
        print(meta)
    except DoesNotMatchSchemaError as e:
        print('ERROR - does not match schema', file=sys.stderr)
