"""One frame of the game, shared by both modes.

Freeplay and multiplayer each had their own copy of this: same clock tick, same
events/update/draw, same six timestamps. The only real difference was what the
mode did afterwards, which is why the frame itself can be shared.
"""

from types import SimpleNamespace

import pytest

from core.loop import tick

COOLDOWNS = ["killcooldown", "sabotagecooldown", "sabotagecriticaltimer",
             "ventcooldown", "meetingcooldown", "timer"]


@pytest.fixture
def game():
    calls = []
    instance = SimpleNamespace(
        clock=SimpleNamespace(tick=lambda fps: 1000),
        paused=False,
        events=lambda: calls.append("events"),
        update=lambda: calls.append("update"),
        draw=lambda: calls.append("draw"),
        calls=calls,
    )
    return instance


def test_a_frame_handles_input_then_updates_then_draws(game):
    # Order matters: drawing before updating shows the previous frame's world.
    tick(game)

    assert game.calls == ["events", "update", "draw"]


def test_the_frame_time_is_in_seconds(game):
    # clock.tick returns milliseconds; everything downstream multiplies by dt.
    tick(game)

    assert game.dt == 1.0


def test_a_paused_game_still_draws_but_does_not_update(game):
    # The pause menu is drawn over the world, so drawing has to keep running.
    game.paused = True

    tick(game)

    assert game.calls == ["events", "draw"]


@pytest.mark.parametrize("cooldown", COOLDOWNS)
def test_every_cooldown_clock_is_advanced(game, cooldown):
    tick(game)

    assert getattr(game, cooldown) > 0


def test_the_cooldown_clocks_all_read_the_same_instant(game):
    # They used to be six separate get_ticks() calls a few microseconds apart.
    tick(game)

    assert len({getattr(game, name) for name in COOLDOWNS}) == 1
