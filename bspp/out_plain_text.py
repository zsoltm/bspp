import logging
import struct
from typing import Union, Iterable, Tuple, Dict, Optional

from bspp.model import PK3Entity, MapEntities, Map
from bspp.postprocess import pp_map

log = logging.getLogger(__name__)
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


def weapon_to_name(weapon_id: str) -> Optional[str]:
    return _weapon_to_name.get(weapon_id, None)


def item_to_name(item_id: str) -> Optional[str]:
    return _item_to_name.get(item_id, None)


def translate_names(class_to_name: Dict[str, str], objects: Dict[str, int]) -> Iterable[Tuple[str, int]]:
    for class_name, count in objects.items():
        name = class_to_name.get(class_name, None)
        if not name:
            log.warning("Unknown class: %s", class_name)
            continue
        yield name, count


def plain_text(entity_containers: Iterable[Union[MapEntities, PK3Entity]]) -> None:
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

    def print_class_counts(justification: int, entries: Iterable[Tuple[str, int]], indent: str = "") -> None:
        for name, count in entries:
            print(f"{indent}{name.ljust(justification, '.')}", ": ×%d" % count)

    def print_flag(flag: bool, dict_key: str, indent: str = "") -> None:
        if flag:
            name = flag_to_name.get(dict_key)
            print(f"{indent}{name.ljust(class_name_pad, '.')}", ": Yes")

    def section_title(title: str, indent: str = "", underline: str = '-'):
        print(f"{indent}{title}")
        print(f"{indent}{underline * len(title)}")
        print()

    class_name_pad = longest_value(_weapon_to_name, _item_to_name, flag_to_name)

    def print_map_entity(map_data: Map, indent: str = ""):
        section_title(map_data.map_name, indent, "=")
        print(f"{indent}Map name: {map_data.map_title}")
        print()

        section_title("Items", indent)
        print_class_counts(class_name_pad, translate_names(_item_to_name, map_data.aggregated_items), indent)
        print()

        section_title("Weapons", indent)
        print_class_counts(class_name_pad, translate_names(_weapon_to_name, map_data.aggregated_weapons), indent)
        print()

        f = map_data.flags

        if f.ctf_capable or f.overload_capable or f.harvester_capable or f.ctf_1f_capable or f.requires_ta:
            section_title("Properties", indent)
            print_flag(f.requires_ta, "requires_ta", indent)
            print_flag(f.ctf_capable, "ctf_capable", indent)
            print_flag(f.ctf_1f_capable, "ctf_1f_capable", indent)
            print_flag(f.overload_capable, "overload_capable", indent)
            print_flag(f.harvester_capable, "harvester_capable", indent)
            print()

    def print_pk3_entity(e: PK3Entity):
        section_title(e.pk3_name)
        print("CRC: ", e.crc.hex(), f"(sv_currentPak: {struct.unpack('<I', e.crc)[0]})")
        print()
        for map_entity in e.map_entities:
            print_map_entity(pp_map(map_entity), "  ")

    for entity_container in entity_containers:
        if type(entity_container) is MapEntities:
            print_map_entity(pp_map(entity_container))
        else:
            print_pk3_entity(entity_container)
