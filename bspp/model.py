from dataclasses import dataclass
from json import JSONEncoder
from typing import Dict, Any, List


@dataclass
class MapEntities:
    map_name: str
    entities: List[Dict[str, str]]


@dataclass
class PK3Entity:
    pk3_name: str
    crc: bytes
    map_entities: List[MapEntities]


@dataclass
class Flags:
    ctf_capable: bool
    overload_capable: bool
    harvester_capable: bool
    ctf_1f_capable: bool
    requires_ta: bool

    def to_json(self):
        return dict(
            ctf_capable=self.ctf_capable,
            overload_capable=self.overload_capable,
            harvester_capable=self.harvester_capable,
            ctf_1f_capable=self.ctf_1f_capable,
            requires_ta=self.requires_ta)


@dataclass
class Map:
    map_title: str
    map_name: str
    aggregated_items: Dict[str, int]
    aggregated_weapons: Dict[str, int]
    flags: Flags

    def to_json(self):
        return dict(
            map_title=self.map_title,
            map_name=self.map_name,
            aggregated_items=self.aggregated_items,
            aggregated_weapons=self.aggregated_weapons,
            flags=self.flags.to_json())


@dataclass
class PK3:
    pk3_name: str
    crc: bytes
    maps: List[Map]

    def to_json(self):
        return dict(
            pk3_name=self.pk3_name,
            crc=self.crc.hex(),
            maps=[m.to_json() for m in self.maps])


class JSONEncodingAwareClassEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if callable(getattr(o, "to_json", None)):
            return o.to_json()
        return super().default(o)
