from dataclasses import dataclass
from json import JSONEncoder
from typing import Dict, Any


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


class JSONEncodingAwareClassEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if callable(getattr(o, "to_json", None)):
            return o.to_json()
        return super().default(o)
