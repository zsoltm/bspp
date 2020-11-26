import logging
from typing import Dict, List, Iterable, Union, Callable

from .model import Map, Flags, MapEntities

log = logging.getLogger(__name__)
items_filtered = {"item_botroam"}


def aggregate_by_classname(objects: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    by_classname = {}
    for obj in objects:
        classname = obj["classname"]
        by_classname.setdefault(classname, []).append(obj)
    return by_classname


def filter_aggregated(filter_spec: Union[str, Callable[[str], bool]], objects: Dict[str, List[any]]) -> Dict[str, int]:
    filter_l = (lambda n: n.startswith(filter_spec)) if isinstance(filter_spec, str) else filter_spec
    return {key: len(value) for (key, value) in objects.items() if filter_l(key)}


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
    return (
        item.startswith("ammo_")
        or item.startswith("holdable_")
        or (item.startswith("item_") and item not in items_filtered)
    )


def pp_map(m: MapEntities) -> Map:
    aggregated_objects = aggregate_by_classname(m.entities)
    world_spawns = aggregated_objects.get("worldspawn", None)
    if not world_spawns:
        raise Exception(f"No worldspawn for {m.map_name}")
    world_spawn = world_spawns.pop()
    map_title = world_spawn.get("message", None)
    if not map_title:
        map_title = m.map_name
        log.warning("No message for worldspawn for %s", m.map_name)

    ctf_capable = check_ctf_capable(aggregated_objects)
    overload_capable = check_overload_capable(aggregated_objects)
    harvester_capable = check_harvester_capable(aggregated_objects)
    ctf_1f_capable = check_1f_ctf_capable(aggregated_objects)
    requires_ta = (
        overload_capable
        or harvester_capable
        or ctf_1f_capable
        or has_any_key(
            aggregated_objects,
            [
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
            ],
        )
    )

    return Map(
        map_title,
        m.map_name,
        m.crc,
        filter_aggregated(item_filter, aggregated_objects),
        filter_aggregated("weapon_", aggregated_objects),
        Flags(ctf_capable, overload_capable, harvester_capable, ctf_1f_capable, requires_ta),
    )
