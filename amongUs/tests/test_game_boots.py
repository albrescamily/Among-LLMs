"""Constructing a Game touches every asset the game owns.

Game.__init__ ends by calling load_data(), which loads the tilemap, walks every
image folder and builds every mixer Sound. So a bare Game() is, in effect, a
full asset-resolution integration test -- the broadest guard available for a
refactor that moves modules around underneath paths.ROOT.

It is also the only test that constructs a real Game, which makes it the only
thing standing between the package moves and a game that no longer starts.
"""

from os import path

from core.paths import ROOT


def test_constructing_the_game_loads_every_asset(display):
    from game import Game

    g = Game()

    # The folders game.py derives from ROOT (game.py:44-54).
    assert path.basename(g.game_folder) == 'amongUs'
    assert path.isdir(g.img_folder)
    assert path.isdir(g.map_folder)
    assert path.isdir(g.sound_folder)
    assert path.isdir(g.font_folder)
    assert g.game_folder == ROOT

    # Proof the tilemap actually loaded rather than silently degrading.
    assert g.map_img.get_width() > 0
    assert g.map_img.get_height() > 0
