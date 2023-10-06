import logging
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import parse
from flask import Response, request
from hurry.filesize import size

from config import Config

Chunk = tuple[bytes, int, int, int]

logger = logging.getLogger(__name__)


def get_chunk(full_path: Path, start_byte: int, end_byte: int | None = None) -> Chunk:
    """ """
    file_size = full_path.stat().st_size
    if end_byte:
        length = end_byte + 1 - start_byte
    else:
        length = file_size - start_byte
    with open(full_path, "rb") as f:
        f.seek(start_byte)
        chunk = f.read(length)
    return chunk, start_byte, length, file_size


def send_media(file_path: Path, mimetype: str) -> Response:
    """ """
    range_header = request.headers.get("Range", None)
    start_byte, end_byte = 0, None
    if range_header:
        match = re.search(r"(\d+)-(\d*)", range_header)
        assert match
        groups = match.groups()
        if groups[0]:
            start_byte = int(groups[0])
        if groups[1]:
            end_byte = int(groups[1])

    chunk, start, length, file_size = get_chunk(file_path, start_byte, end_byte)
    resp = Response(chunk, 206, mimetype=f"video/{mimetype}", content_type=mimetype, direct_passthrough=True)
    resp.headers.add("Content-Range", "bytes {0}-{1}/{2}".format(start, start + length - 1, file_size))
    return resp


def get_file_extension(fp: Path) -> str:
    """ """
    return fp.suffix.lower()


def is_media(fp: Path, config: Config) -> tuple[bool, str, str]:
    """ """
    tp = "other"
    ext = get_file_extension(fp)
    if ext in config.ext_dict:
        tp = config.ext_dict[ext][0]
    return tp in ["audio", "video"], tp, ext


def get_icon(fp: Path, config: Config) -> str:
    if fp.is_dir():
        return "/static/icons/folder.png"
    if fp.is_file():
        ext = get_file_extension(fp)
        if ext in config.ext_dict:
            return config.ext_dict[ext][1]
    return "/static/icons/file.png"


def zip_directory(dest_path: Path, source_dir: Path) -> None:
    assert source_dir.is_dir()
    relroot = source_dir.parent.resolve()
    with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            rel = os.path.relpath(root, relroot)
            zip.write(root, rel)
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename):  # regular files only
                    arcname = os.path.join(rel, file)
                    zip.write(filename, arcname)


def is_hidden(path: Path, config: Config) -> bool:
    if path.is_dir():
        return path.parts[-1] in config.hidden_list
    if path.is_file():
        return path.name.startswith(".") or path.name in config.hidden_list
    return False


def get_filepath(path: str, config: Config) -> Path:
    fp = config.base_dir
    if path:
        fp /= Path(unquote(path))
    return fp


def dir_exists(path: str, config: Config) -> bool:
    fp = get_filepath(path, config)
    return fp.exists()


def path_to_dict(i: Path, config: Config):
    f_name = i.name
    f_url = i.relative_to(config.base_dir).as_posix()
    image = get_icon(i, config)
    try:
        stat = i.stat()
        dtc = datetime.utcfromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        dtm = datetime.utcfromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        sz = "---" if i.is_dir() else size(stat.st_size)
    except:
        dtc = "---"
        dtm = "---"
        sz = "---"
    target = dict(f_name=f_name, f_url=f_url, image=image, dtc=dtc, dtm=dtm, size=sz)
    return target


def uri_to_dict(var: str, config: Config):
    i = get_filepath(var, config)
    f_name = i.name
    f_url = i.relative_to(config.base_dir).as_posix()
    image = get_icon(i, config)
    metadata = {}
    try:
        stat = i.stat()
        dtc = datetime.utcfromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        dtm = datetime.utcfromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        sz = "---" if i.is_dir() else size(stat.st_size)
    except:
        dtc = "---"
        dtm = "---"
        sz = "---"
    target = dict(f_name=f_name, f_url=f_url, image=image, dtc=dtc, dtm=dtm, size=sz, metadata=metadata)
    return target


def get_dir_listing(path: Path, config: Config):
    assert path.is_dir()
    itemList = sorted(path.iterdir(), key=lambda x: [not x.is_dir(), x])
    dir_list_dict: dict[str, dict] = {}
    file_list_dict: dict[str, dict] = {}

    for i in itemList:
        target = dir_list_dict if i.is_dir() else file_list_dict
        if not is_hidden(i, config):
            f_url = i.relative_to(config.base_dir).as_posix()
            target[f_url] = path_to_dict(i, config)

    return dir_list_dict, file_list_dict


def run_pattern(path: str, pattern: str, mode: str, config: Config) -> dict[str, str]:
    assert mode in ["name_pattern", "path_pattern"]
    parser = parse.compile(pattern)
    path_obj = get_filepath(path, config)
    if mode == "path_pattern":
        arg = path_obj.parent.as_posix()
        logger.info(arg)
    elif mode == "name_pattern":
        arg = path_obj.name
    else:
        raise ValueError()
    try:
        result = parser.parse(arg)
        assert isinstance(result, parse.Result)
        metadata: dict[str, str] = dict(result.named)
    except Exception as e:
        logging.error([pattern, arg])
        metadata = {}
    return metadata
