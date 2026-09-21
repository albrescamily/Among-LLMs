"""Ciclo 6 - every bot gets a nickname to show in the chat."""

import pygame as pg
import pytest

from core.chat import BOT_NAMES
from core.sprites import Bot


class NameSource:
    """Stand-in for Game: only what Bot touches while spawning."""

    def __init__(self):
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.bots = pg.sprite.Group()
        self.handed_out = []

    def take_bot_name(self):
        name = "bot%d" % len(self.handed_out)
        self.handed_out.append(name)
        return name


def test_bot_gets_a_name_when_it_spawns():
    game = NameSource()

    bot = Bot(game, 100, 100, "Left", "bot1", "Green")

    assert bot.bot_name == "bot0"
    assert bot.bot_colour == "Green"


def test_each_bot_gets_its_own_name():
    game = NameSource()

    names = [Bot(game, 0, 0, "Left", "bot%d" % i, colour).bot_name
             for i, colour in enumerate(["Red", "Blue", "Green"])]

    assert len(set(names)) == 3


def test_take_bot_name_hands_out_distinct_names():
    from game import Game

    stub = type("Stub", (), {})()
    stub.bot_names_pool = list(BOT_NAMES)

    names = [Game.take_bot_name(stub) for _ in range(len(BOT_NAMES))]

    assert sorted(names) == sorted(BOT_NAMES)
    assert stub.bot_names_pool == []


def test_take_bot_name_refills_an_empty_pool():
    from game import Game

    stub = type("Stub", (), {})()
    stub.bot_names_pool = []

    name = Game.take_bot_name(stub)

    assert name in BOT_NAMES
    assert len(stub.bot_names_pool) == len(BOT_NAMES) - 1
