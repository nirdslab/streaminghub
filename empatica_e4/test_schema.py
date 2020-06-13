import pprint

from core.io import get_meta_stream

if __name__ == '__main__':
    print('test XML schema parsing')
    meta = get_meta_stream('empatica_e4/spec.xml', 'xml')
    pprint.pprint(meta)

    print('test JSON schema parsing')
    meta = get_meta_stream('empatica_e4/spec.json', 'json')
    pprint.pprint(meta)
