"""Keys an agent 'presses', in place of a keyboard.

Player.get_keys and the task triggers read the keyboard by calling
pg.key.get_pressed() and indexing the result with a pg.K_* constant. Rather than
thread an extra parameter through every one of those call sites, the agent
process swaps that one function for another that answers from an AgentIntent.
That is safe here because each agent is its own OS process: no other pygame
state is shared with a human's game.
"""

import pygame as pg


class AgentIntent:
    """What the agent wants held down this frame."""

    def __init__(self):
        self.keys_down = set()


class AgentKeys:
    """Looks like the sequence pg.key.get_pressed() returns: keys[pg.K_a] -> bool."""

    def __init__(self, intent):
        self._intent = intent

    def __getitem__(self, key):
        return key in self._intent.keys_down


def install(intent):
    """Make this process read its keys from intent from now on."""
    pg.key.get_pressed = lambda: AgentKeys(intent)
