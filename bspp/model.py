from dataclasses import dataclass
from typing import Dict


@dataclass
class Flags:
    ctf_capable: bool
    overload_capable: bool
    harvester_capable: bool
    ctf_1f_capable: bool
    requires_ta: bool


@dataclass
class Map:
    map_title: str
    map_name: str
    aggregated_items: Dict[str, int]
    aggregated_weapons: Dict[str, int]
    flags: Flags
