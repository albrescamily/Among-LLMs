"""The agent's fake keyboard and its wandering.

Player.get_keys indexes pg.key.get_pressed() with pg.K_* constants, so the fake
has to answer that; the wanderer has to keep walking and turn when blocked.
"""

import random

import pygame as pg

from agents import agent_input
from agents.wander import Wanderer, DIRECTIONS, MAX_WALK_MS, STUCK_CHECK_MS


def test_installed_keys_answer_from_the_intent(monkeypatch):
    monkeypatch.setattr(pg.key, "get_pressed", pg.key.get_pressed)
    intent = agent_input.AgentIntent()
    agent_input.install(intent)

    intent.keys_down = {pg.K_LEFT}
    keys = pg.key.get_pressed()
    assert keys[pg.K_LEFT] and not keys[pg.K_RIGHT]

    intent.keys_down = set()
    assert not pg.key.get_pressed()[pg.K_LEFT]


def test_the_first_step_picks_a_direction():
    keys = Wanderer(random.Random(1)).step(0, (0, 0))
    assert keys in DIRECTIONS


def test_keeps_walking_while_it_is_moving():
    w = Wanderer(random.Random(1))
    first = set(w.step(0, (0, 0)))
    # moved well past the stuck threshold, and not yet time to turn
    assert w.step(STUCK_CHECK_MS, (50, 0)) == first


def test_turns_to_a_different_direction_when_blocked():
    w = Wanderer(random.Random(1))
    first = set(w.step(0, (0, 0)))
    assert w.step(STUCK_CHECK_MS, (0, 0)) != first


def test_turns_after_walking_too_long():
    w = Wanderer(random.Random(1))
    first = set(w.step(0, (0, 0)))
    # keep moving so it is never "blocked", only bored
    now, x = 0, 0
    while now <= MAX_WALK_MS:
        now += STUCK_CHECK_MS
        x += 50
        keys = w.step(now, (x, 0))
    assert keys != first
