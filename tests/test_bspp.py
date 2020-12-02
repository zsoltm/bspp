import os
from unittest import TestCase

from bspp import bspp


class TestBspp(TestCase):
    def test_j1_pk3_file(self):  # vq3
        pk3 = bspp.process_pk3_file(os.path.join("tests", "resources", "j-1.pk3"))
        self.__assert_pk3(pk3, "j-1.pk3", "1a2bb1ed", 1)
        self.__assert_map_ent(pk3.map_entities[0], "j-1", "3a040bcb", 28)

    def test_finkota4_pk3_file(self):  # team arena
        pk3 = bspp.process_pk3_file(os.path.join("tests", "resources", "finkota4.pk3"))
        self.__assert_pk3(pk3, "finkota4.pk3", "b2674135", 1)
        self.__assert_map_ent(pk3.map_entities[0], "finkota4", "d3fa8367", 105)

    def test_vrmpack_pk3_file(self):  # multi-map
        pk3 = bspp.process_pk3_file(os.path.join("tests", "resources", "vrmpack.pk3"))
        self.__assert_pk3(pk3, "vrmpack.pk3", "0466a99d", 2)
        self.__assert_map_ent(pk3.map_entities[0], "vrmdmm4", "42af48d6", 37)
        self.__assert_map_ent(pk3.map_entities[1], "vrmamphi", "c8e87ccc", 19)

    def test_pp_finkota4(self):
        pk3 = bspp.process_pk3_file(os.path.join("tests", "resources", "finkota4.pk3"))
        m = bspp.pp_map(pk3.map_entities[0])
        self.assertEqual(m.map_name, "finkota4")
        self.assertEqual(m.map_title, "SpineBender")
        self.assertEqual(m.crc.hex(), "d3fa8367")

        # items:
        items = m.aggregated_items
        self.assertEqual(items["item_quad"], 1)  # Quad damage
        self.assertEqual(items["item_armor_combat"], 1)  # Combat armor (red)
        self.assertEqual(items["ammo_shells"], 4)  # Shotgun shells
        self.assertEqual(items["ammo_bullets"], 2)  # Bullets
        self.assertEqual(items["ammo_belt"], 2)  # Chain gun ammo
        self.assertEqual(items["ammo_rockets"], 2)  # Rockets
        self.assertEqual(items["item_health_small"], 8)  # Small health (green)
        self.assertEqual(items["item_health_large"], 4)  # Large health (orange)
        self.assertEqual(items["item_doubler"], 2)  # Doubler
        self.assertEqual(items["item_guard"], 2)  # Guard

        # weapons:
        weapons = m.aggregated_weapons
        self.assertEqual(weapons["weapon_rocketlauncher"], 3)
        self.assertEqual(weapons["weapon_railgun"], 2)
        self.assertEqual(weapons["weapon_chaingun"], 1)
        self.assertEqual(weapons["weapon_shotgun"], 1)

        # flags:
        self.assertTrue(m.flags.requires_ta)
        self.assertTrue(m.flags.ctf_capable)
        self.assertTrue(m.flags.ctf_1f_capable)
        self.assertTrue(m.flags.overload_capable)
        self.assertTrue(m.flags.harvester_capable)

    def __assert_map_ent(self, j1map, map_name, crc, num_entities):
        self.assertEqual(j1map.map_name, map_name)
        self.assertEqual(j1map.crc.hex(), crc)
        self.assertEqual(len(j1map.entities), num_entities)

    def __assert_pk3(self, pk3, pk3_name: str, crc, map_num):
        self.assertTrue(pk3.pk3_name.endswith(pk3_name))
        self.assertEqual(pk3.crc.hex(), crc)
        self.assertEqual(len(pk3.map_entities), map_num)
