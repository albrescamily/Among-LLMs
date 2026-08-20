"""The star import in game.py is load-bearing, and this is why.

Three of the display helpers blit an image named by a *string* that a sprite
handed them:

    game.py     self.screen.blit(eval(self.emergency_img_sync), (0, 0))
    sprites.py  self.emergency_meeting_img_sync = "red_player_emergency_meeting"

eval() with no globals argument uses the globals of the module that calls it,
so those bare names only resolve because game.py does `from settings import *`.
Rewriting that to `from core import settings` would leave the game importable,
the suite green, and the emergency-meeting screen crashing with NameError the
first time anybody calls a meeting.

These tests fail the moment the star import goes away.
"""

import pygame as pg
import pytest

import game as game_module

COLOURS = ["red", "blue", "orange", "yellow", "green"]


@pytest.mark.parametrize("colour", COLOURS)
def test_emergency_meeting_image_name_resolves_in_game_globals(colour):
    # sprites.py assigns this string; game.display_meeting_alert() evals it.
    surface = eval(f"{colour}_player_emergency_meeting", vars(game_module))
    assert isinstance(surface, pg.Surface)


@pytest.mark.parametrize("colour", COLOURS)
def test_report_meeting_image_name_resolves_in_game_globals(colour):
    surface = eval(f"{colour}_player_emergency_meeting_report", vars(game_module))
    assert isinstance(surface, pg.Surface)


@pytest.mark.parametrize("colour", COLOURS)
def test_eject_image_name_resolves_in_game_globals(colour):
    # The eject animation indexes into the walk cycle: "red_player_imgs_right[9]".
    surface = eval(f"{colour}_player_imgs_right[9]", vars(game_module))
    assert isinstance(surface, pg.Surface)
