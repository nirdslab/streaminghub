import logging
import multiprocessing

from .proxy import PupilCoreProxy as Proxy


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
    queue = multiprocessing.Queue()
    proxy.attach(node.id, stream.name, queue)

    while True:
        item = queue.get()
        print(item)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]")
    test()
