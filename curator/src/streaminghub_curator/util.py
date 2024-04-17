from collections import defaultdict
import logging
import os
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import parse
from flask import Response, request
from hurry.filesize import size
from .typing import FileDescriptor

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


def is_media(fp: Path, ext_dict: dict) -> tuple[bool, str, str]:
    """ """
    tp = "other"
    ext = get_file_extension(fp)
    if ext in ext_dict:
        tp = ext_dict[ext][0]
    return tp in ["audio", "video"], tp, ext


def get_icon(fp: Path, ext_dict: dict) -> str:
    if fp.is_dir():
        return "/static/icons/folder.png"
    if fp.is_file():
        ext = get_file_extension(fp)
        if ext in ext_dict:
            return ext_dict[ext][1]
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


def is_hidden(path: Path, hidden_list: list) -> bool:
    if path.is_dir():
        return path.parts[-1] in hidden_list
    if path.is_file():
        return path.name.startswith(".") or path.name in hidden_list
    return False


def get_filepath(path: str, base_dir: Path) -> Path:
    fp = base_dir
    if path:
        fp /= Path(unquote(path))
    return fp


def dir_exists(path: str, base_dir: Path) -> bool:
    fp = get_filepath(path, base_dir)
    return fp.exists()


def path_to_dict(i: Path, base_dir: Path, ext_dict: dict) -> FileDescriptor:
    f_name = i.name
    f_url = i.relative_to(base_dir).as_posix()
    image = get_icon(i, ext_dict)
    try:
        stat = i.stat()
        dtc = datetime.fromtimestamp(stat.st_ctime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        dtm = datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sz = "---" if i.is_dir() else size(stat.st_size)
    except:
        dtc = "---"
        dtm = "---"
        sz = "---"
    return FileDescriptor(f_name=f_name, f_url=f_url, image=image, dtc=dtc, dtm=dtm, size=sz, metadata={})


def uri_to_dict(var: str, base_dir: Path, ext_dict: dict) -> FileDescriptor:
    i = get_filepath(var, base_dir)
    f_name = i.name
    f_url = i.relative_to(base_dir).as_posix()
    image = get_icon(i, ext_dict)
    metadata = {}
    try:
        stat = i.stat()
        dtc = datetime.fromtimestamp(stat.st_ctime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        dtm = datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sz = "---" if i.is_dir() else size(stat.st_size)
    except:
        dtc = "---"
        dtm = "---"
        sz = "---"
    return FileDescriptor(f_name=f_name, f_url=f_url, image=image, dtc=dtc, dtm=dtm, size=sz, metadata=metadata)


def get_dir_listing(path: Path, base_dir: Path, ext_dict: dict, hidden_list: list):
    assert path.is_dir()
    itemList = sorted(path.iterdir(), key=lambda x: [not x.is_dir(), x])
    dir_list_dict: dict[str, FileDescriptor] = {}
    file_list_dict: dict[str, FileDescriptor] = {}

    for i in itemList:
        target = dir_list_dict if i.is_dir() else file_list_dict
        if not is_hidden(i, hidden_list):
            f_url = i.relative_to(base_dir).as_posix()
            target[f_url] = path_to_dict(i, base_dir, ext_dict)

    return dir_list_dict, file_list_dict


def run_pattern(path: str, pattern: str, mode: str, base_dir: Path) -> dict[str, str]:
    assert mode in ["name_pattern", "path_pattern"]

    # define fallback response
    metadata = {}

    # define parsers
    parse_parser = regex_parser = None
    try:
        parse_parser = parse.compile(pattern)
    except Exception as e:
        logging.warn(f"invalid pattern for 'parse' library: {pattern}", e.args)
    try:
        regex_parser = re.compile(pattern)
    except Exception as e:
        logging.warn(f"invalid pattern for 're' library: {pattern}", e.args)
    assert (parse_parser or regex_parser) is not None

    # compute the arg to parse
    path_obj = get_filepath(path, base_dir)
    if mode == "path_pattern":
        arg = path_obj.relative_to(base_dir).parent.as_posix()
        logger.info(arg)
    elif mode == "name_pattern":
        arg = path_obj.name
    else:
        raise RuntimeError()  # should never happen

    # try parsing the arg
    arg_parsed = False
    if (not arg_parsed) and (parse_parser is not None):
        try:
            result = parse_parser.parse(arg, evaluate_result=True)
            if isinstance(result, parse.Result):
                arg_parsed = True
                metadata: dict[str, str] = dict(result.named)
                logging.warn("parse_parser.parse() worked")
            else:
                logging.warn("parse_parser.parse() did not work")
        except Exception as e:
            logging.error(f"error running parse_parser on string:", e.args)
    if (not arg_parsed) and (regex_parser is not None):
        try:
            result = regex_parser.match(arg)
            if result is not None:
                arg_parsed = True
                metadata: dict[str, str] = result.groupdict()
                logging.warn("regex_parser.match() worked")
            else:
                logging.warn("regex_parse.match() did not work")
        except Exception as e:
            logging.error(f"error running regex_parser on string:", e.args)

    # return parsed metadata
    return metadata


def find_unique_attributes(selection: dict[str, FileDescriptor]) -> dict[str, list[str]]:
    uniques = defaultdict(list)
    for file, descriptor in selection.items():
        for key, value in descriptor.metadata.items():
            uniques[key].append(value)
    return dict(uniques)

