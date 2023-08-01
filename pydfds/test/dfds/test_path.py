import logging

from dfds.url import PathOrURL

logging.basicConfig(level=logging.INFO)


def test_url_join():
    ptr1_uri = "/home/yasith/test_dir/base.json"
    ptr2_uri = "./file.json"
    target_uri = "/home/yasith/test_dir/file.json"

    print(ptr1_uri)
    ptr1 = PathOrURL(ptr1_uri)
    print(ptr1, "=>", ptr1.to_url())

    print(ptr2_uri)
    ptr2 = PathOrURL(ptr2_uri)
    print(ptr2, "=>", ptr2.to_url())

    print(target_uri)
    out = ptr1.join(ptr2)
    print(out, "=>", out.to_url())

    assert target_uri == out.to_url()


def test_windows_url():
    ptr_uri = "C:\\Users\\yasith\\Documents\\base.json"

    print(ptr_uri)
    ptr = PathOrURL(ptr_uri)
    print(ptr, "=>", ptr.to_url())

    assert ptr_uri == ptr.to_url()


def test_windows_url_join():
    ptr1_uri = "C:\\Users\\yasith\\Documents\\base.json"
    ptr2_uri = "./file.json"
    target_uri = "C:\\Users\\yasith\\Documents\\file.json"

    print(ptr1_uri)
    ptr1 = PathOrURL(ptr1_uri)
    print(ptr1, "=>", ptr1.to_url())

    print(ptr2_uri)
    ptr2 = PathOrURL(ptr2_uri)
    print(ptr2, "=>", ptr2.to_url())

    print(target_uri)
    out = ptr1.join(ptr2)
    print(out, "=>", out.to_url())

    assert target_uri == out.to_url()
