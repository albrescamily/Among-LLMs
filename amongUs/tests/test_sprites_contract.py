"""The multiplayer concept that lives inside a core sprite.

Player.__init__ puts every *remote* player into game.players_server as well as
game.all_sprites. That group is a multiplayer idea, but it sits in core/ and
the game creates it in new() for both modes -- in freeplay it just stays empty.

Which makes it look like dead code worth deleting. It isn't: deleting it breaks
multiplayer only, and only at the point where a second player joins, which no
other test exercises. So pin it here.
"""

from types import SimpleNamespace

import pygame as pg

from core.sprites import Player


def make_host():
    """Just the two sprite groups Player.__init__ reaches for."""
    return SimpleNamespace(
        all_sprites=pg.sprite.LayeredUpdates(),
        players_server=pg.sprite.Group(),
    )


def test_the_local_player_stays_out_of_the_server_group():
    host = make_host()
    me = Player(host, (100, 100), 0, True, "Red")
    assert me in host.all_sprites
    assert me not in host.players_server


def test_a_remote_player_joins_the_server_group():
    host = make_host()
    them = Player(host, (100, 100), 5, False, "Blue")
    assert them in host.all_sprites
    assert them in host.players_server


def test_freeplay_leaves_the_server_group_empty():
    # A local-only game never populates it, which is why it looks removable.
    host = make_host()
    Player(host, (100, 100), 0, True, "Red")
    assert len(host.players_server) == 0
