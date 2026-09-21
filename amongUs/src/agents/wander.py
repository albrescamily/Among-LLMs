"""The simplest movement: walk in a direction, pick another when blocked or bored.

No map knowledge, so it bumps into walls and turns away. Real navigation
(pathfinding to a task) replaces this later; until then it proves the agent can
move a player through the same input path a human's keyboard uses.
"""

import random

import pygame as pg

# the eight ways to walk, as the keys that produce them
DIRECTIONS = [
    {pg.K_LEFT},
    {pg.K_RIGHT},
    {pg.K_UP},
    {pg.K_DOWN},
    {pg.K_LEFT, pg.K_UP},
    {pg.K_LEFT, pg.K_DOWN},
    {pg.K_RIGHT, pg.K_UP},
    {pg.K_RIGHT, pg.K_DOWN},
]

MIN_WALK_MS = 800
MAX_WALK_MS = 3000
STUCK_CHECK_MS = 400
STUCK_DISTANCE = 4   # moved less than this many pixels in STUCK_CHECK_MS counts as blocked


class Wanderer:
    """Call step() once a frame; it returns the set of keys to hold."""

    def __init__(self, rng=random):
        self._rng = rng
        self.keys = set()
        self._turn_at = 0
        self._checked_at = 0
        self._checked_pos = None

    def _turn(self, now):
        # never pick the direction we are already walking: after a wall, that is the wrong one
        choices = [d for d in DIRECTIONS if d != self.keys] or DIRECTIONS
        self.keys = set(self._rng.choice(choices))
        self._turn_at = now + self._rng.randint(MIN_WALK_MS, MAX_WALK_MS)

    def step(self, now, pos):
        """now in milliseconds, pos an (x, y) pair."""
        blocked = False
        if self._checked_pos is None or now - self._checked_at >= STUCK_CHECK_MS:
            if self._checked_pos is not None:
                moved = abs(pos[0] - self._checked_pos[0]) + abs(pos[1] - self._checked_pos[1])
                blocked = moved < STUCK_DISTANCE
            self._checked_at = now
            self._checked_pos = pos

        if not self.keys or blocked or now >= self._turn_at:
            self._turn(now)
        return self.keys
