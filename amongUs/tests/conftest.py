"""Shared test setup.

The game is a pygame app, so the tests need a video/audio driver. Both are set
to SDL's dummy backends before pygame is imported, which lets the whole suite
run headless (no window, no sound card).

A display is still created because pygame refuses to convert_alpha() a surface
without one, and the chat scales the player sprites into avatars.

The game modules live in amongUs/src/ and load their artwork through
paths.asset(), which resolves against amongUs/, so the tests do not need to
run from any particular directory.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
from os import path

import pytest

# the game modules live in src/, not in tests/
sys.path.insert(0, path.join(path.dirname(path.dirname(path.abspath(__file__))), 'src'))

import pygame as pg

from core.settings import WIDTH, HEIGHT


@pytest.fixture(scope="session", autouse=True)
def display():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    yield screen
    pg.quit()


class FakePlayer:
    def __init__(self, alive=True, player_id=7):
        self.alive_status = alive
        self.player_id = player_id


class FakeMenu:
    def __init__(self, word="camily"):
        self.word = word


class FakeBot:
    def __init__(self, bot_name, bot_colour, alive=True):
        self.bot_name = bot_name
        self.bot_colour = bot_colour
        self.alive_status = alive


class FakeGame:
    """Just enough of Game for the chat to work against.

    Building a real Game would load every image, sound and the mixer, which is
    far too heavy (and fragile) for a unit test.
    """

    def __init__(self, alive=True, name="camily", colour="Red", bots=None):
        self.player = FakePlayer(alive)
        self.menu = FakeMenu(name)
        self.player_colour = colour
        self.bots = bots if bots is not None else [
            FakeBot("madara", "Green"),
            FakeBot("lalanga", "Orange"),
            FakeBot("Vmbatalha", "White"),
            FakeBot("pernilongo", "Yellow", alive=False),
        ]


@pytest.fixture
def fake_game():
    return FakeGame()


@pytest.fixture
def make_chat():
    """Builds an open chat over a custom FakeGame."""
    from core.chat import MeetingChat

    def factory(**kwargs):
        instance = MeetingChat(FakeGame(**kwargs))
        instance.open()
        instance.clear()    # drop the demo chatter so tests start from zero
        return instance

    return factory


@pytest.fixture
def chat(make_chat):
    """An open chat, which is the state every interaction test needs."""
    return make_chat()
