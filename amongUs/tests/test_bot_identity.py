"""Each bot name marks exactly one object on the map.

The ten bot-kill blocks in update() checked `hit.type == 'botN'` and then acted
on `self.botN`. Collapsing them into one loop that acts on `hit` is only
faithful while those are the same object -- which holds because new() binds
self.botN to the sprite built from the tmx object named botN, and each name
appears once.

That last part is a property of the *map data*, not of any Python file. Someone
opening the map in Tiled and duplicating a spawn would break the collapsed
version silently, so it is checked against the .tmx itself.
"""

import xml.etree.ElementTree as ET
from os import path

import pytest

from core.paths import asset

MAPS = ["Assets/Maps/map.tmx", "Assets/Maps/map2.tmx"]
BOT_NAMES = [f"bot{n}" for n in range(1, 11)]


def object_names(tmx):
    tree = ET.parse(asset(tmx))
    return [obj.get("name") for obj in tree.iter("object")]


@pytest.mark.parametrize("tmx", MAPS)
@pytest.mark.parametrize("name", BOT_NAMES)
def test_each_bot_name_marks_exactly_one_object(tmx, name):
    assert object_names(tmx).count(name) == 1


@pytest.mark.parametrize("tmx", MAPS)
def test_the_map_still_has_ten_bots(tmx):
    names = object_names(tmx)

    assert sorted(n for n in names if n in BOT_NAMES) == sorted(BOT_NAMES)
