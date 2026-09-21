"""One frame, the same in both game modes.

Freeplay and multiplayer differ in what they do around the frame -- one talks
to a server, the other counts bots -- but the frame itself is identical, so
they share it.
"""

import pygame as pg

from core.settings import FPS


def tick(game):
    """Advance the game by a frame: input, world, picture, clocks.

    The six cooldown clocks all read the same instant. They used to be six
    separate get_ticks() calls a few microseconds apart, which no threshold in
    the game is anywhere near tight enough to notice.
    """
    game.dt = game.clock.tick(FPS) / 1000

    game.events()
    if game.paused == False:
        game.update()
    game.draw()

    now = pg.time.get_ticks()
    game.killcooldown = now
    game.sabotagecooldown = now
    game.sabotagecriticaltimer = now
    game.ventcooldown = now
    game.meetingcooldown = now
    game.timer = now
