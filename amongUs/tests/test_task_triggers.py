"""Walking up to a task and pressing SPACE.

Eleven places in draw() did the same six things: measure the distance to a
fixed point, check SPACE, check the task is not already done, check the player
is not the imposter, play a sound, and open the window. Six of them are uniform
enough to be a table; the other five have quirks that a table field would only
disguise, so they stay explicit functions.

`fire` takes `keys` as a parameter, which is both what makes these tests
possible without a keyboard and what fixes a real bug: six of the eleven
triggers read a `keys` local that the *wifi* trigger happened to leave behind
in draw()'s frame. Extracting any of them without passing it explicitly would
have raised NameError.
"""

from collections import defaultdict
from types import SimpleNamespace

import pygame as pg
import pytest

from conftest import Recorder
from core.task_triggers import (FUEL_ENGINE_ANCHOR, GAS_CAN_ANCHOR, TRIGGERS,
                                fire, fire_all, fuel_engine_trigger,
                                gas_can_trigger)

IDS = [trigger.once_guard for trigger in TRIGGERS]


def keys_with(*pressed):
    return defaultdict(bool, {key: True for key in pressed})


def task_game(trigger, at=None, imposter=False, armed=1, done=1):
    """A game standing exactly on the trigger's anchor unless told otherwise."""
    position = trigger.anchor if at is None else at
    game = SimpleNamespace(
        player=SimpleNamespace(pos=SimpleNamespace(x=position[0], y=position[1]),
                               imposter=imposter, alive_status=True),
        isdoingTask=False,
        effect_sounds=defaultdict(Recorder),
    )
    setattr(game, trigger.arm_guard, armed)
    setattr(game, trigger.once_guard, done)
    for flag in trigger.sets:
        setattr(game, flag, False)
    return game


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_standing_far_away_does_nothing(trigger):
    game = task_game(trigger, at=(99999, 99999))

    assert fire(game, keys_with(pg.K_SPACE), trigger) is False
    assert game.isdoingTask is False


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_standing_close_without_pressing_space_does_nothing(trigger):
    game = task_game(trigger)

    assert fire(game, keys_with(), trigger) is False
    assert game.isdoingTask is False


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_space_in_range_opens_every_widget_the_task_owns(trigger):
    game = task_game(trigger)

    assert fire(game, keys_with(pg.K_SPACE), trigger) is True
    assert game.isdoingTask is True
    for flag in trigger.sets:
        assert getattr(game, flag) is True, flag


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_the_trigger_disarms_itself(trigger):
    """Holding SPACE must not reopen the window every frame."""
    game = task_game(trigger)

    fire(game, keys_with(pg.K_SPACE), trigger)

    assert getattr(game, trigger.arm_guard) == 0
    assert fire(game, keys_with(pg.K_SPACE), trigger) is False


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_a_completed_task_cannot_be_reopened(trigger):
    game = task_game(trigger, done=0)

    assert fire(game, keys_with(pg.K_SPACE), trigger) is False


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_an_imposter_cannot_do_tasks(trigger):
    game = task_game(trigger, imposter=True)

    assert fire(game, keys_with(pg.K_SPACE), trigger) is False


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_opening_a_task_plays_its_sounds(trigger):
    game = task_game(trigger)

    fire(game, keys_with(pg.K_SPACE), trigger)

    for sound in trigger.sounds:
        name = sound[0] if isinstance(sound, tuple) else sound
        assert game.effect_sounds[name].plays == 1


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_just_inside_the_radius_still_fires(trigger):
    edge = (trigger.anchor[0] + trigger.radius - 1, trigger.anchor[1])
    game = task_game(trigger, at=edge)

    assert fire(game, keys_with(pg.K_SPACE), trigger) is True


@pytest.mark.parametrize("trigger", TRIGGERS, ids=IDS)
def test_just_outside_the_radius_does_not(trigger):
    beyond = (trigger.anchor[0] + trigger.radius + 1, trigger.anchor[1])
    game = task_game(trigger, at=beyond)

    assert fire(game, keys_with(pg.K_SPACE), trigger) is False


def test_fire_all_opens_only_the_task_you_are_standing_on():
    first, second = TRIGGERS[0], TRIGGERS[1]
    game = task_game(first)
    setattr(game, second.arm_guard, 1)
    setattr(game, second.once_guard, 1)
    for flag in second.sets:
        setattr(game, flag, False)

    fire_all(game, keys_with(pg.K_SPACE))

    assert all(getattr(game, flag) for flag in first.sets)
    assert not any(getattr(game, flag) for flag in second.sets)


def fuel_game(at, picked=False, imposter=False, **over):
    state = dict(
        player=SimpleNamespace(pos=SimpleNamespace(x=at[0], y=at[1]),
                               imposter=imposter, alive_status=True),
        isdoingTask=False, is_gas_can_picked=picked,
        gas_can_not_picked_text_visible_status=False,
        gas_can_picking_count=1, gas_can_picking_sound_play_count=1,
        fuel_engine_task_play_count=1, fuel_engine_sound_play_count=1,
        fuel_engine_window_status=False, fuel_engine_fill_btn_status=False,
        fuel_engine_close_btn_status=False,
        effect_sounds=defaultdict(Recorder),
    )
    state.update(over)
    return SimpleNamespace(**state)


def test_picking_up_the_gas_can():
    game = fuel_game(GAS_CAN_ANCHOR)

    assert gas_can_trigger(game, keys_with(pg.K_SPACE)) is True
    assert game.is_gas_can_picked is True


def test_the_gas_can_opens_no_window():
    """It is not a task window: no isdoingTask, nothing to close."""
    game = fuel_game(GAS_CAN_ANCHOR)

    gas_can_trigger(game, keys_with(pg.K_SPACE))

    assert game.isdoingTask is False


def test_the_gas_can_can_only_be_picked_up_once():
    game = fuel_game(GAS_CAN_ANCHOR)
    gas_can_trigger(game, keys_with(pg.K_SPACE))

    assert gas_can_trigger(game, keys_with(pg.K_SPACE)) is False


def test_the_gas_can_is_guarded_by_the_engines_completion_flag():
    """Its own quirk: it reads the *fuel engine's* counter, not one of its own."""
    game = fuel_game(GAS_CAN_ANCHOR, fuel_engine_task_play_count=0)

    assert gas_can_trigger(game, keys_with(pg.K_SPACE)) is False


def test_an_imposter_does_not_pick_up_the_can():
    game = fuel_game(GAS_CAN_ANCHOR, imposter=True)

    assert gas_can_trigger(game, keys_with(pg.K_SPACE)) is False


def test_fuelling_the_engine_with_the_can():
    game = fuel_game(FUEL_ENGINE_ANCHOR, picked=True)

    assert fuel_engine_trigger(game, keys_with(pg.K_SPACE)) is True
    assert game.fuel_engine_window_status is True
    assert game.isdoingTask is True


def test_reaching_the_engine_without_the_can_says_so():
    """The branch that makes this not a table row."""
    game = fuel_game(FUEL_ENGINE_ANCHOR, picked=False)

    assert fuel_engine_trigger(game, keys_with(pg.K_SPACE)) is False
    assert game.gas_can_not_picked_text_visible_status is True
    assert game.fuel_engine_window_status is False
    # still counts as doing a task, so the message has somewhere to be drawn
    assert game.isdoingTask is True


def test_being_told_you_need_the_can_does_not_consume_the_trigger():
    game = fuel_game(FUEL_ENGINE_ANCHOR, picked=False)
    fuel_engine_trigger(game, keys_with(pg.K_SPACE))

    game.is_gas_can_picked = True

    assert fuel_engine_trigger(game, keys_with(pg.K_SPACE)) is True


def test_standing_nowhere_near_the_engine_does_nothing():
    game = fuel_game((0, 0), picked=True)

    assert fuel_engine_trigger(game, keys_with(pg.K_SPACE)) is False
    assert game.gas_can_not_picked_text_visible_status is False


def test_every_task_has_its_own_anchor():
    assert len({trigger.anchor for trigger in TRIGGERS}) == len(TRIGGERS)


def test_every_once_guard_is_a_name_gamefunctions_reads():
    """Renaming a task flag silently kills the glow highlights.

    core/gamefunctions.py decides which map objects to light up by reading
    these counters by name. Nothing else would notice a typo in the table --
    the effect is purely visual, so no smoke test sees it either.
    """
    from os import path
    source = open(path.join(path.dirname(path.dirname(path.abspath(__file__))),
                            "src", "core", "gamefunctions.py"),
                  encoding="utf-8").read()

    for trigger in TRIGGERS:
        assert trigger.once_guard in source, trigger.once_guard
