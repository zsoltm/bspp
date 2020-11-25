#!/usr/bin/env python3

import json
import os
import re
import struct
from typing import List, Dict, Callable, IO, Iterable, Tuple, Union, Optional
from zipfile import ZipFile, ZipInfo

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
    print(f"BSP size: {bsp_size}")
    if bytes(bsp_data_view[0:4]) != bsp_head:
        raise Exception("Invalid BSP header")
    if bytes(bsp_data_view[4:8]) != bsp_version:
        raise Exception("Invalid BSP version")
    dir_entry_ofs = 8 + index * 8
    (offset, length) = struct.unpack(
        '<2i', bytes(bsp_data_view[dir_entry_ofs:dir_entry_ofs + 8]))  # index 0 lump: entites
    print(f"Entities lump is at offset {offset} with size {length}")
    if length < 0 or offset < 0x90 or offset + length > bsp_size:
        raise Exception("Invalid direntry offsets")
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
                    print(f"WARN: empty object at line {line_no}")
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
                print(f"WARN: Duplicate key: {key} at {line_no}")
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
        print(f"Processing PK3 {file_name}")
        yield from process_pk3_file(file_name)
    elif bsp_file_exp.search(file_name):
        print(f"Processing BSP {file_name}")
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
    print("Maps:", ", ".join(name_list))
    for bsp_file_name in name_list:
        print(f"Processing pk3 map: {bsp_file_name}")
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
    "item_flight": "Flgiht",

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


def plain_text(files_entities_list: Dict[str, List[Dict[str, str]]]):
    items_filtered = {'item_botroam'}

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

    class_name_pad = longest_value(_weapon_to_name, _item_to_name, flag_to_name)

    def aggregate_by_classname(objects: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        by_classname = {}
        for obj in objects:
            classname = obj["classname"]
            by_classname.setdefault(classname, []).append(obj)
        return by_classname

    def print_class_counts(class_to_name: Dict[str, str], filter_spec: Union[str, Callable[[str], bool]],
                           objects: Dict[str, List[any]]) -> None:
        filter_l = (lambda n: n.startswith(filter_spec)) if type(filter_spec) == str else filter_spec
        for class_name, elements in objects.items():
            if filter_l(class_name):
                name = class_to_name.get(class_name, None)
                count = len(elements)
                if not name:
                    print(f"WARN: Unknown class: {class_name}")
                    continue
                print(name.ljust(class_name_pad, '.'), ": ×%d" % count)

    def print_flag(flag: bool, dict_key: str) -> None:
        if flag:
            name = flag_to_name.get(dict_key)
            print(name.ljust(class_name_pad, '.'), ": Yes")

    def check_ctf_capable(objects: Dict[str, any]) -> bool:
        return "team_CTF_blueflag" in objects and "team_CTF_blueflag" in objects

    def check_1f_ctf_capable(objects: Dict[str, any]) -> bool:
        return "team_CTF_neutralflag" in objects

    def check_overload_capable(objects: Dict[str, any]) -> bool:
        return "team_redobelisk" in objects and "team_blueobelisk" in objects

    def check_harvester_capable(objects: Dict[str, any]) -> bool:
        return "team_neutralobelisk" in objects

    def has_any_key(objects: Dict[str, any], key_list: Iterable[str]) -> bool:
        haystack_keyset = set(objects.keys())
        return any([x in haystack_keyset for x in key_list])

    def item_filter(item):
        return item.startswith("ammo_") or item.startswith("holdable_") or (
                    item.startswith("item_") and item not in items_filtered)

    def section_title(title: str):
        print(title)
        print("-" * len(title))
        print()

    for map_name, object_list in files_entities_list.items():
        try:
            aggregated_objects = aggregate_by_classname(object_list)
            world_spawns = aggregated_objects.get("worldspawn", None)
            if not world_spawns:
                raise Exception(f"No worldspawn for {map_name}")
            world_spawn = world_spawns.pop()
            map_title = world_spawn.get("message", None)
            if not map_title:
                map_title = map_name
                print(f"WARN: No message for worldspawn for {map_name}")

            ctf_capable = check_ctf_capable(aggregated_objects)
            overload_capable = check_overload_capable(aggregated_objects)
            harvester_capable = check_harvester_capable(aggregated_objects)
            ctf_1f_capable = check_1f_ctf_capable(aggregated_objects)
        except:
            print(f"ERROR: unexpected error while generating text output for {map_name}, skipping")
            continue

        print(map_title)
        print("=" * len(map_title))
        print()
        print("Map name...:", map_name)
        print()
        section_title("Items")
        print_class_counts(_item_to_name, item_filter, aggregated_objects)
        print()
        section_title("Weapons")
        print_class_counts(_weapon_to_name, "weapon_", aggregated_objects)
        print()

        requires_ta = overload_capable or harvester_capable or ctf_1f_capable or has_any_key(aggregated_objects, [
            "item_guard",
            "item_doubler",
            "item_scout",
            "item_ammoregen",
            "weapon_chaingun",
            "weapon_prox_launcher",
            "weapon_nailgun",
            "ammo_belt",
            "ammo_mines",
            "ammo_nails",
            "holdable_kamikaze",
        ])

        if ctf_capable or overload_capable or harvester_capable or ctf_1f_capable or requires_ta:
            section_title("Properties")
            print_flag(requires_ta, "requires_ta")
            print_flag(ctf_capable, "ctf_capable")
            print_flag(ctf_1f_capable, "ctf_1f_capable")
            print_flag(overload_capable, "overload_capable")
            print_flag(harvester_capable, "harvester_capable")
            print()

        # print(aggregated_objects.keys())


def json_formatted(files_entities_list: Dict[str, List[Dict[str, str]]]):
    print(json.dumps(files_entities_list, indent=True))


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='BSP info tool')
    parser.add_argument('-j', dest='output', action='store_const', default=plain_text, const=json_formatted,
                        help='JSON output')
    parser.add_argument('files', metavar='F', nargs='+', help="a .bsp or pk3 or file or folder to be processed")
    parsed = parser.parse_args(sys.argv)

    if len(parsed.files) < 2:
        print("WARN: no files specified")

    parsed.output(map_dict(process(parsed.files[1:])))
