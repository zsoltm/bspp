#!/usr/bin/env python3

import json
import logging
import os
import re
import struct
from typing import List, Dict, Iterable, Union
from zipfile import ZipFile

from bspp.hash import pk3_hash_info, bsp_hash
from bspp.model import MapEntities, PK3Entity, PK3, JSONEncodingAwareClassEncoder
from bspp.postprocess import pp_map

log = logging.getLogger(__name__)
pk3_file_exp = re.compile(r".+\.pk3$", re.I)
bsp_file_exp = re.compile(r".+\.bsp$", re.I)
pk3_bsp_file = re.compile(r"^maps/[^.]+.bsp$", re.I)
bsp_head = b"IBSP"
bsp_version = b"\x2e\0\0\0"
obj_beg_exp = re.compile(r"\s*{\s*")
obj_end_exp = re.compile(r"\s*}\s*")
obj_string_exp = re.compile(r'\s*"([^"]*)"\s*')


def is_pk3_bsp(pk3_zip_entry: str):
    return pk3_bsp_file.match(pk3_zip_entry)


def is_pk3(dir_file: str) -> bool:
    return len(dir_file) > 4 and dir_file[-4:].lower() == ".pk3"


def get_lump(bsp_bytes: bytes, index: int) -> bytes:
    bsp_data_view = memoryview(bsp_bytes)
    bsp_size = len(bsp_bytes)
    log.debug("BSP size: %d", bsp_size)
    if bytes(bsp_data_view[0:4]) != bsp_head:
        raise Exception("Invalid BSP header")
    if bytes(bsp_data_view[4:8]) != bsp_version:
        raise Exception("Invalid BSP version")
    dir_entry_ofs = 8 + index * 8
    (offset, length) = struct.unpack(
        "<2i", bytes(bsp_data_view[dir_entry_ofs : dir_entry_ofs + 8])
    )  # index 0 lump: entities
    log.debug("Entities lump is at offset %d with size %d", offset, length)
    if length < 0 or offset < 0x90 or offset + length > bsp_size:
        raise Exception("Invalid dir entry offsets")
    return bytes(bsp_data_view[offset : offset + length - 1])


def parse_entity_obj(lines: Iterable[str]) -> Iterable[Dict[str, str]]:
    in_obj = False
    entity_obj: Dict[str, str] = {}
    line_no = 0
    for line in lines:
        line_no += 1
        if line == "\0":
            continue
        if not in_obj:
            if obj_beg_exp.match(line):
                if not in_obj:
                    in_obj = True
                    entity_obj = {}
                continue
            raise Exception(f"Expected object open curly at {line_no}")

        if obj_end_exp.match(line):
            in_obj = False
            if len(entity_obj) == 0 or "classname" not in entity_obj:
                log.warning("Empty object at line %d", line_no)
                continue
            yield entity_obj
            continue
        m = obj_string_exp.match(line)
        if not m or m.start() > 0:
            raise Exception(f"Expected string literal key at {line_no}")
        key = m[1]
        m = obj_string_exp.match(line, m.end())
        if not m or m.end() < len(line):
            raise Exception(f"Expected string literal value at {line_no}")
        value = m[1]
        if key in entity_obj:
            log.warning("Duplicate key: %s at %d", key, line_no)
        entity_obj[key] = value


def process_entities(bsp_data: bytes) -> List[Dict[str, str]]:
    return list(parse_entity_obj(str(get_lump(bsp_data, 0), encoding="ascii").splitlines()))


def process(files: Iterable[str]) -> Iterable[Union[PK3Entity, MapEntities]]:
    for file_name in files:
        if os.path.isdir(file_name):
            for root, _, w_files in os.walk(file_name):
                pk3_files = [dir_file for dir_file in w_files if is_pk3(dir_file)]
                for pk3_file in pk3_files:
                    yield process_file(os.path.join(root, pk3_file))
        else:
            yield process_file(file_name)


def process_file(file_name: str) -> Union[PK3Entity, MapEntities]:
    if pk3_file_exp.match(file_name):
        log.info("Processing PK3 %s", file_name)
        return process_pk3_file(file_name)
    elif bsp_file_exp.match(file_name):
        log.info("Processing BSP %s", file_name)
        return process_map_file(file_name)
    else:
        raise ValueError(f"Unknown file type: {file_name}")


def process_map_file(file_name: str) -> MapEntities:
    with open(file_name, "rb") as bsp_file:
        bsp_data = bsp_file.read()
        return MapEntities(file_name, bsp_hash(bsp_data), process_entities(bsp_data))


def process_pk3_file(file_name: str) -> PK3Entity:
    with ZipFile(file_name, "r") as pk3_zip:
        return process_pk3_zip(pk3_zip)


def process_pk3_zip(pk3_zip: ZipFile) -> PK3Entity:
    zip_info_list = pk3_zip.infolist()
    bsp_name_list = list(filter(is_pk3_bsp, map(lambda entry: entry.filename, zip_info_list)))
    if log.isEnabledFor(logging.DEBUG):
        log.debug("Maps: %s", ", ".join(bsp_name_list))
    return PK3Entity(
        str(pk3_zip.filename), pk3_hash_info(zip_info_list), list(_process_pk3_zip_maps(pk3_zip, bsp_name_list))
    )


def _process_pk3_zip_maps(pk3_zip: ZipFile, bsp_name_list: Iterable[str]) -> Iterable[MapEntities]:
    for bsp_file_name in bsp_name_list:
        log.info("Processing pk3 map: %s", bsp_file_name)
        with pk3_zip.open(bsp_file_name, "r") as bsp_file:
            bsp_data = bsp_file.read()
        entities = process_entities(bsp_data)
        yield MapEntities(bsp_file_name[len("maps/") : -len(".bsp")], bsp_hash(bsp_data), entities)


def json_formatted(entity_containers: Iterable[Union[MapEntities, PK3Entity]]):
    processed = [
        pp_map(x) if isinstance(x, MapEntities) else PK3(x.pk3_name, x.crc, [pp_map(me) for me in x.map_entities])
        for x in entity_containers
    ]
    print(json.dumps(processed, indent=True, cls=JSONEncodingAwareClassEncoder))


if __name__ == "__main__":
    import argparse
    from bspp.out_plain_text import plain_text

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="BSP info tool")
    parser.add_argument("files", metavar="F", nargs="+", help="a .bsp or pk3 or file or folder to be processed")
    parser.add_argument(
        "-j", dest="output", action="store_const", default=plain_text, const=json_formatted, help="JSON output"
    )
    parsed = parser.parse_args()

    if len(parsed.files) < 1:
        log.warning("No files specified")

    parsed.output(process(parsed.files))
