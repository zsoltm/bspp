Quake 3 .PK3 map info and BSP Parser
====================================

Quake 3 BSP and PK3 map info extractor for Python 3 
with no external dependencies.

It can be used as a library within other projects 
or as a command line tool.

Installation
------------

```bash
$ pip install bspp
```

Command line usage
------------------

```bspp.py [-h] [-j] F [F ...]```

+ `-j` toggles JSON output - plain text by default
+ `F` files (.bsp or .pk3) or directories to process

Example 1: get all map info as plain text from a .pk3

```bash
$ python -m bspp.bspp /opt/quake3/baseq3/pak6.pk3

/opt/quake3/baseq3/pak6.pk3
---------------------------

CRC:  dd13d69b (sv_currentPak: -585902437)

  pro-q3dm13
  ==========

  Map name: Lost World II
  CRC: 7d11f295 (sv_mapChecksum 2098328213)

  Items
  -----

  Lightning charge..... : ×2
  Bullets.............. : ×1
  Small health (green). : ×6
  Combat armor (red)... : ×1
  Armor shard.......... : ×8
  Health (yellow)...... : ×6
  Large health (orange) : ×1
  Megahealth........... : ×1
  Rockets.............. : ×2
  Grenades............. : ×2
  Body armor (yellow).. : ×1

  Weapons
  -------

  Shotgun.............. : ×2
  Rocket launcher...... : ×1
  Lightning gun........ : ×1
  Grenade launcher..... : ×1

  pro-q3dm6
  =========

  Map name: The Campgrounds II
  CRC: c61b258e (sv_mapChecksum -971299442)

  Items
  -----

  Quad damage.......... : ×1
  Megahealth........... : ×1
  Large health (orange) : ×3
  Shotgun shells....... : ×2
  Rockets.............. : ×4
  Body armor (yellow).. : ×2
  Combat armor (red)... : ×2
  Lightning charge..... : ×2
  Health (yellow)...... : ×9
  Bullets.............. : ×4
  Slugs................ : ×3
  Plasma cells......... : ×2
  Grenades............. : ×1
  Armor shard.......... : ×5

  Weapons
  -------

  Shotgun.............. : ×4
  Grenade launcher..... : ×2
  Lightning gun........ : ×2
  Plasma gun........... : ×2
  Railgun.............. : ×2
  Rocket launcher...... : ×2

  pro-q3tourney2
  ==============

  Map name: The Proving Grounds II
  CRC: e58b1ebd (sv_mapChecksum -443867459)

  Items
  -----

  Body armor (yellow).. : ×1
  Bullets.............. : ×1
  Small health (green). : ×3
  Rockets.............. : ×2
  Health (yellow)...... : ×3
  Combat armor (red)... : ×1
  Shotgun shells....... : ×2
  Armor shard.......... : ×16
  Lightning charge..... : ×1
  Large health (orange) : ×1

  Weapons
  -------

  Rocket launcher...... : ×1
  Railgun.............. : ×1
  Lightning gun........ : ×1
  Shotgun.............. : ×1

  pro-q3tourney4
  ==============

  Map name: Vertical Vengeance II
  CRC: c143ed0e (sv_mapChecksum -1052513010)

  Items
  -----

  Plasma cells......... : ×1
  Combat armor (red)... : ×2
  Rockets.............. : ×1
  Armor shard.......... : ×6
  Health (yellow)...... : ×6
  Megahealth........... : ×1
  Bullets.............. : ×2
  Small health (green). : ×4
  Slugs................ : ×1
  Shotgun shells....... : ×1

  Weapons
  -------

  Plasma gun........... : ×1
  Shotgun.............. : ×1
  Railgun.............. : ×1
  Rocket launcher...... : ×1
```

Example 2: get all map info from .pk3 as JSON

```bash
$ python -m bspp.bspp /opt/quake3/baseq3/pak2.pk3
```

```json
[
 {
  "pk3_name": "/opt/quake3/baseq3/pak2.pk3",
  "crc": "18912474",
  "maps": [
   {
    "map_title": "Hero's Keep",
    "map_name": "q3dm9",
    "crc": "9c64ee6a",
    "aggregated_items": {
     "ammo_bullets": 3,
     "ammo_rockets": 4,
     "ammo_slugs": 3,
     "item_health_small": 6,
     "item_health_mega": 1,
     "item_health_large": 3,
     "ammo_shells": 3,
     "item_health": 8,
     "ammo_cells": 4,
     "item_armor_shard": 14,
     "item_armor_combat": 2,
     "item_armor_body": 1
    },
    "aggregated_weapons": {
     "weapon_shotgun": 3,
     "weapon_plasmagun": 3,
     "weapon_rocketlauncher": 1,
     "weapon_railgun": 1
    },
    "flags": {
     "ctf_capable": false,
     "overload_capable": false,
     "harvester_capable": false,
     "ctf_1f_capable": false,
     "requires_ta": false
    }
   },
   {
    "map_title": "Across Space",
    "map_name": "q3tourney6_ctf",
    "crc": "e45d877b",
    "aggregated_items": {
     "item_health_large": 4,
     "item_quad": 1,
     "item_armor_body": 1,
     "ammo_rockets": 2,
     "ammo_bullets": 2,
     "item_health": 2
    },
    "aggregated_weapons": {
     "weapon_rocketlauncher": 2,
     "weapon_railgun": 2,
     "weapon_bfg": 1
    },
    "flags": {
     "ctf_capable": true,
     "overload_capable": false,
     "harvester_capable": false,
     "ctf_1f_capable": false,
     "requires_ta": false
    }
   }
  ]
 }
]
```

API usage
---------

Open a .PK3 and extract all map info:

```pydocstring
>>> from bspp import bspp

>>> pk3 = bspp.process_pk3_file("/opt/quake3/baseq3/pak2.pk3")

>>> len(pk3.map_entities)
2

>>> maps = [bspp.pp_map(m) for m in pk3.map_entities]
[Map(map_title="Hero's Keep", map_name='q3dm9', crc=b'\x9cd\xeej', aggregated_items={'ammo_bullets': 3, 
'ammo_rockets': 4, 'ammo_slugs': 3, 'item_health_small': 6, 'item_health_mega': 1, 'item_health_large': 3, 
'ammo_shells': 3, 'item_health': 8, 'ammo_cells': 4, 'item_armor_shard': 14, 'item_armor_combat': 2, 
'item_armor_body': 1}, aggregated_weapons={'weapon_shotgun': 3, 'weapon_plasmagun': 3, 'weapon_rocketlauncher': 1, 
'weapon_railgun': 1}, flags=Flags(ctf_capable=False, overload_capable=False, harvester_capable=False, 
ctf_1f_capable=False, requires_ta=False)), Map(map_title='Across Space', map_name='q3tourney6_ctf', crc=b'\xe4]\x87{', 
aggregated_items={'item_health_large': 4, 'item_quad': 1, 'item_armor_body': 1, 'ammo_rockets': 2, 'ammo_bullets': 2, 
'item_health': 2}, aggregated_weapons={'weapon_rocketlauncher': 2, 'weapon_railgun': 2, 'weapon_bfg': 1}, 
flags=Flags(ctf_capable=True, overload_capable=False, harvester_capable=False, ctf_1f_capable=False, 
equires_ta=False))]
```
