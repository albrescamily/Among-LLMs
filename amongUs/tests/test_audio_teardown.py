"""Silencing everything when a round ends.

The same twelve lines appeared seven times in game.py -- once per way a round
can end, in both game modes. Seven copies means seven chances for a new sound
collection to be added to six of them, and the symptom is footsteps still
playing under the victory screen.
"""

from types import SimpleNamespace

import pygame as pg
import pytest

from conftest import Recorder
from core.audio import stop_all_audio


@pytest.fixture
def game():
    return SimpleNamespace(
        foot_sounds={'footsteps': [Recorder(), Recorder()]},
        effect_sounds={'victory_crew': Recorder(), 'game_left': Recorder()},
        electric_shock_sounds={'electric_shock': [Recorder()]},
        comms_radio_sounds={'comms_radio': [Recorder(), Recorder()]},
        ambient_sounds={'cafeteria': Recorder(), 'reactor': Recorder()},
    )


def every_sound(game):
    yield from game.foot_sounds['footsteps']
    yield from game.effect_sounds.values()
    yield from game.electric_shock_sounds['electric_shock']
    yield from game.comms_radio_sounds['comms_radio']
    yield from game.ambient_sounds.values()


@pytest.fixture
def mixer(monkeypatch):
    """Stands in for the two things that are not per-game collections."""
    music, channel = Recorder(), Recorder()
    monkeypatch.setattr(pg.mixer, "music", SimpleNamespace(stop=music.stop))
    monkeypatch.setattr(pg.mixer, "Channel", lambda number: channel)
    return music, channel


def test_the_background_music_and_the_effects_channel_both_stop(game, mixer):
    music, channel = mixer

    stop_all_audio(game)

    assert music.stops == 1
    assert channel.stops == 1


def test_every_loaded_sound_is_silenced(game, mixer):
    stop_all_audio(game)

    assert all(sound.stops == 1 for sound in every_sound(game))


def test_nothing_is_stopped_twice(game, mixer):
    # A sound stopped twice is harmless; a test that would not notice a
    # collection being iterated twice is not.
    stop_all_audio(game)

    # 2 footsteps + 2 effects + 1 shock + 2 comms + 2 ambient
    assert [sound.stops for sound in every_sound(game)] == [1] * 9
