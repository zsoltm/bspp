#!/usr/bin/env python3

import json
import logging
import os
import re
import struct
from typing import List, Dict, IO, Iterable, Tuple, Optional
from zipfile import ZipFile, ZipInfo

from bspp.postprocess import pp

log = logging.getLogger(__name__)

pk3_file_exp = re.compile(r"\.pk3$", re.I)
bsp_file_exp = re.compile(r"\.bsp$", re.I)
pk3_bsp_file = re.compile(r"^maps/[^.]+.bsp$", re.I)
bsp_head = b"IBSP"
bsp_version = b"\x2e\0\0\0"


def is_pk3_bsp(pk3_zip_entry: str):
    return pk3_bsp_file.match(pk3_zip_entry)


def is_pk3(dir_file: str) -> bool:
    return len(dir_file) > 4 and dir_file[-4:].lower() == ".pk3"


def get_lump(bsp_file: IO, index: int) -> bytes:
    bsp_data = bsp_file.read()
    bsp_data_view = memoryview(bsp_data)
    bsp_size = len(bsp_data)
    log.debug(f"BSP size: {bsp_size}")
    if bytes(bsp_data_view[0:4]) != bsp_head:
        raise Exception("Invalid BSP header")
    if bytes(bsp_data_view[4:8]) != bsp_version:
        raise Exception("Invalid BSP version")
    dir_entry_ofs = 8 + index * 8
    (offset, length) = struct.unpack(
        '<2i', bytes(bsp_data_view[dir_entry_ofs:dir_entry_ofs + 8]))  # index 0 lump: entities
    log.debug(f"Entities lump is at offset {offset} with size {length}")
    if length < 0 or offset < 0x90 or offset + length > bsp_size:
        raise Exception("Invalid dir entry offsets")
    return bytes(bsp_data_view[offset:offset + length - 1])


obj_beg_exp = re.compile(r"\s*{\s*")
obj_end_exp = re.compile(r"\s*}\s*")
obj_string_exp = re.compile(r'\s*"([^"]*)"\s*')


def parse_entity_obj(lines: Iterable[str]) -> List[Dict[str, str]]:
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
        else:
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


def process_entities(bsp_file: IO):
    return list(parse_entity_obj(str(get_lump(bsp_file, 0), encoding='ascii').splitlines()))


def process(files: Iterable[str]) -> Iterable[Tuple[str, List[Dict[str, str]]]]:
    for file_name in files:
        if os.path.isdir(file_name):
            for root, dirs, files in os.walk(file_name):
                pk3_files = [dir_file for dir_file in files if is_pk3(dir_file)]
                for pk3_file in pk3_files:
                    yield from process_file(os.path.join(root, pk3_file))
        else:
            yield from process_file(file_name)


def process_file(file_name: str) -> Iterable[Tuple[str, List[Dict[str, str]]]]:
    if pk3_file_exp.search(file_name):
        log.info("Processing PK3 %s", file_name)
        yield from process_pk3_file(file_name)
    elif bsp_file_exp.search(file_name):
        log.info("Processing BSP %s", file_name)
        with open(file_name, 'rb') as bsp_file:
            yield file_name[0:-len(".bsp")], process_entities(bsp_file)
    else:
        raise ValueError(f"Unknown file type: {file_name}")


def process_pk3_file(file_name: str) -> Iterable[Tuple[str, List[Dict[str, str]]]]:
    with ZipFile(file_name, 'r') as pk3_zip:
        bsp_file_names = list(filter(is_pk3_bsp, pk3_zip.namelist()))
        yield from process_pk3_zip(pk3_zip, bsp_file_names)


def process_pk3_zip(
        pk3_zip: ZipFile, name_list: Optional[List[str]] = None, info_list: Optional[List[ZipInfo]] = None) \
        -> Iterable[Tuple[str, List[Dict[str, str]]]]:
    if not (name_list is None or info_list is None):
        raise ValueError("One of name_list or info_list should be specified")
    if not name_list:
        name_list = []
    if info_list:
        name_list.extend([i.filename for i in info_list])
    if log.isEnabledFor(logging.DEBUG):
        log.debug("Maps: %s", ", ".join(name_list))
    for bsp_file_name in name_list:
        log.info("Processing pk3 map: %s", bsp_file_name)
        with pk3_zip.open(bsp_file_name, 'r') as bsp_file:
            entities = process_entities(bsp_file)
        yield bsp_file_name[len("maps/"):-len(".bsp")], entities


def map_dict(map_objects: Iterable[Tuple[str, List[Dict[str, str]]]]) -> Dict[str, List[Dict[str, str]]]:
    maps = {}
    for map_name, objects in map_objects:
        maps[map_name] = objects
    return maps


_weapon_to_name = {
    "weapon_rocketlauncher": "Rocket launcher",
    "weapon_grenadelauncher": "Grenade launcher",
    "weapon_lightning": "Lightning gun",
    "weapon_plasmagun": "Plasma gun",
    "weapon_shotgun": "Shotgun",
    "weapon_railgun": "Railgun",
    "weapon_bfg": "BFG",
    "weapon_chaingun": "Chaingun",  # ta
    "weapon_prox_launcher": "Proximity Launcher",  # ta
    "weapon_nailgun": "Nailgun",  # ta
}


def weapon_to_name(weapon_id: str) -> Optional[str]:
    return _weapon_to_name.get(weapon_id, None)


_item_to_name = {
    "item_armor_shard": "Armor shard",
    "item_health_small": "Small health (green)",
    "item_health": "Health (yellow)",
    "item_health_large": "Large health (orange)",
    "item_armor_body": "Body armor (yellow)",
    "item_armor_combat": "Combat armor (red)",
    "item_armor_jacket": "Armor jacket (green)",
    "item_health_mega": "Megahealth",
    "item_quad": "Quad damage",
    "item_regen": "Regeneration",
    "item_invis": "Invisibility",
    "item_enviro": "Battle Suit",
    "item_haste": "Haste",
    "item_flight": "Flight",

    # ammo:
    "ammo_bullets": "Bullets",
    "ammo_shells": "Shotgun shells",
    "ammo_grenades": "Grenades",
    "ammo_rockets": "Rockets",
    "ammo_cells": "Plasma cells",
    "ammo_lightning": "Lightning charge",
    "ammo_slugs": "Slugs",
    "ammo_belt": "Chaingun ammo",  # ta
    "ammo_nails": "Nails",  # ta
    "ammo_mines": "Proximity mines",  # ta
    "ammo_bfg": "BFG Ammo",

    "item_guard": "Guard",  # ta
    "item_doubler": "Doubler",  # ta
    "item_scout": "Scout",  # ta
    "item_ammoregen": "Ammo regen",  # ta

    "holdable_kamikaze": "Kamikaze",  # ta
    "holdable_medkit": "Medkit",
    "holdable_teleporter": "Teleporter",
}


def item_to_name(item_id: str) -> Optional[str]:
    return _item_to_name.get(item_id, None)


def translate_names(class_to_name: Dict[str, str], objects: Dict[str, int]) -> Iterable[Tuple[str, int]]:
    for class_name, count in objects.items():
        name = class_to_name.get(class_name, None)
        if not name:
            log.warning("Unknown class: %s", class_name)
            continue
        yield name, count


def post_process_entities():
    pass


def plain_text(entities_by_map: Dict[str, List[Dict[str, str]]]):
    flag_to_name = {
        "ctf_capable": "CTF capable",
        "requires_ta": "Requires team arena",
        "ctf_1f_capable": "One flag CTF capable",
        "overload_capable": "Overload capable",
        "harvester_capable": "Harvester capable",
    }

    def longest_value(*dicts: Dict[any, str]) -> int:
        max_v_len = 0
        for d in dicts:
            for v in d.values():
                max_v_len = max(max_v_len, len(v))
        return max_v_len

    def print_class_counts(justification: int, entries: Iterable[Tuple[str, int]]) -> None:
        for name, count in entries:
            print(name.ljust(justification, '.'), ": ×%d" % count)

    def print_flag(flag: bool, dict_key: str) -> None:
        if flag:
            name = flag_to_name.get(dict_key)
            print(name.ljust(class_name_pad, '.'), ": Yes")

    def section_title(title: str):
        print(title)
        print("-" * len(title))
        print()

    class_name_pad = longest_value(_weapon_to_name, _item_to_name, flag_to_name)

    for ppp in pp(entities_by_map):
        print(ppp.map_title)
        print("=" * len(ppp.map_title))
        print()
        print("Map name:", ppp.map_name)
        print()

        section_title("Items")
        print_class_counts(class_name_pad, translate_names(_item_to_name, ppp.aggregated_items))
        print()

        section_title("Weapons")
        print_class_counts(class_name_pad, translate_names(_weapon_to_name, ppp.aggregated_weapons))
        print()

        f = ppp.flags

        if f.ctf_capable or f.overload_capable or f.harvester_capable or f.ctf_1f_capable or f.requires_ta:
            section_title("Properties")
            print_flag(f.requires_ta, "requires_ta")
            print_flag(f.ctf_capable, "ctf_capable")
            print_flag(f.ctf_1f_capable, "ctf_1f_capable")
            print_flag(f.overload_capable, "overload_capable")
            print_flag(f.harvester_capable, "harvester_capable")
            print()


def json_formatted(files_entities_list: Dict[str, List[Dict[str, str]]]):
    print(json.dumps(files_entities_list, indent=True))


if __name__ == '__main__':
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='BSP info tool')
    parser.add_argument('-j', dest='output', action='store_const', default=plain_text, const=json_formatted,
                        help='JSON output')
    parser.add_argument('files', metavar='F', nargs='+', help="a .bsp or pk3 or file or folder to be processed")
    parsed = parser.parse_args(sys.argv)

    if len(parsed.files) < 2:
        log.warning("No files specified")

    parsed.output(map_dict(process(parsed.files[1:])))
