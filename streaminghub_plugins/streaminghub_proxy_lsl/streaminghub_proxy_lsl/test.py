import streaminghub_datamux as dm

from .proxy import LSLProxy as Proxy


def test():
    proxy = Proxy()
    proxy.setup()
    nodes = proxy.list_sources()
    assert len(nodes) > 0
    print(nodes)
    node = nodes[0]
    streams = proxy.list_streams(node.id)
    assert len(streams) > 0
    print(streams)
    stream = streams[0]
    queue = dm.Queue()
    flag = dm.create_flag()
    proxy.attach(node.id, stream.name, stream.attrs, queue, dm.identity, flag)

    while True:
        item = queue.get()
        print(item)


if __name__ == "__main__":
    test()
