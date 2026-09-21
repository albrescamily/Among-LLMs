"""Entry point for a headless agent: joins a LAN server without a window or a menu.

Like main.py this opens a real socket, so it is a launcher and not import-safe.
The menu is a set of blocking loops waiting for keys, so it is skipped: this sets
the few fields the menu would have set and calls the multiplayer loop directly.
"""

import argparse
import os

# these have to be set before pygame is imported
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg

from agents import agent_input
from agents.wander import Wanderer
from core import display

# The window opens at a fraction of the canvas for humans; a synthetic mouse
# position must not be scaled, so the agent's window matches the canvas 1:1.
display.INITIAL_SCALE = 1.0

from game import Game
from multiplayer import session

COLOURS = ("Red", "Blue", "Orange", "Yellow", "Green")
REPORT_EVERY_MS = 1000


def make_on_tick(name, intent):
    """A per-frame callback: wander, and report where the player is."""
    last_report = [0]
    wanderer = Wanderer()

    def on_tick(game):
        now = pg.time.get_ticks()
        pos = game.player.pos
        intent.keys_down = wanderer.step(now, (pos.x, pos.y))
        if now - last_report[0] >= REPORT_EVERY_MS:
            last_report[0] = now
            print("[agent %s] at (%d, %d)" % (name, game.player.pos.x, game.player.pos.y), flush=True)

    return on_tick


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="127.0.0.1")
    parser.add_argument("--colour", choices=COLOURS, default="Red")
    parser.add_argument("--name", default="agent")
    args = parser.parse_args()

    intent = agent_input.AgentIntent()
    agent_input.install(intent)

    game = Game()
    game.gamemode = "Multiplayer"
    game.player_colour = args.colour
    game.menu.word = args.name
    game.new()
    game.serveraddress = args.server
    session.run(game, on_tick=make_on_tick(args.name, intent))


if __name__ == "__main__":
    main()
