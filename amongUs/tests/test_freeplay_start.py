"""Setting up a freeplay round.

Everything that happens before the first frame: the local player is created as
the imposter, the bot wearing the player's colour is removed so there are not
two of it on the map, and every cooldown clock is seeded.

This is its own function mainly so the frame-test fixture can call it. A
fixture that hand-rolled this setup would drift from what the game actually
does, and then every test built on it would be testing a state that never
occurs in a real round.
"""

import pygame as pg

from singleplayer import freeplay

COOLDOWN_CLOCKS = ["timer_start", "killcooldown_start", "sabotagecooldown_start",
                   "sabotagecriticaltimer_start", "ventcooldown_start",
                   "meetingcooldown_start", "start_ticks"]


def test_start_round_creates_the_local_player(booted_game):
    assert booted_game.player is not None
    assert booted_game.player.player_islocal is True


def test_the_local_player_is_the_imposter(booted_game):
    # Freeplay is one human imposter against the bots, always.
    assert booted_game.player.imposter is True


def test_start_round_seeds_every_cooldown_clock(booted_game):
    for clock in COOLDOWN_CLOCKS:
        assert isinstance(getattr(booted_game, clock), int)


def test_the_bot_wearing_the_players_colour_is_removed(booted_game):
    # new() spawns ten bots covering ten colours; the player takes one of them,
    # so that bot has to go or the map shows two of the same colour.
    colours = [bot.bot_colour for bot in booted_game.bots]

    assert booted_game.player_colour not in colours


def test_the_round_starts_playing(booted_game):
    assert booted_game.playing is True
