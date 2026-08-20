"""Turning the sound off.

Ending a round means silencing five separate collections plus the music and the
effects channel. Every way a round can end needs all of it, so it lives in one
place rather than being copied per ending.
"""

import pygame as pg


def stop_all_audio(game):
    """Silence everything, ready for the victory sting to play over nothing."""
    pg.mixer.music.stop()
    pg.mixer.Channel(0).stop()

    for sound in game.foot_sounds['footsteps']:
        sound.stop()
    for sound in game.effect_sounds.values():
        sound.stop()
    for sound in game.electric_shock_sounds['electric_shock']:
        sound.stop()
    for sound in game.comms_radio_sounds['comms_radio']:
        sound.stop()
    for sound in game.ambient_sounds.values():
        sound.stop()
