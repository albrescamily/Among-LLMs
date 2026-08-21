"""The imposter kills a bot.

One rule, which update() used to state ten times -- once per bot, with the
index changed and, in one of the ten, two extra lines. Ten copies of a rule is
ten places for it to drift, and it had already started to.

The guards, in the order the code checks them: the bot must not already be
dead, the imposter must not be hiding in a vent, only the imposter kills, and
the 15-second cooldown must have elapsed.
"""

from collections import defaultdict
from types import SimpleNamespace

import pygame as pg
import pytest

from conftest import Recorder
from core.kills import COOLDOWN_MS, apply_bot_kills, bot_kill

BOT_TYPES = [f"bot{n}" for n in range(1, 11)]


def keys_with(*pressed):
    """A keyboard state, without a keyboard."""
    return defaultdict(bool, {key: True for key in pressed})


def fake_bot(bot_type="bot1", alive=True, killed=0):
    return SimpleNamespace(type=bot_type, alive_status=alive,
                           play_kill_count=killed, image="alive-sprite",
                           dead_player_img="dead-sprite")


def kill_game(imposter=True, invisible=0, since_last_kill=COOLDOWN_MS + 1, **over):
    """Just enough Game for the kill rule."""
    state = dict(
        player=SimpleNamespace(imposter=imposter),
        invisible_play_count=invisible,
        bot_killed=0, bot_count=9,
        killcooldown=since_last_kill, killcooldown_start=0,
        kill_timer_icon_status=False, time_left_to_kill=0,
        kill_timer_event=pg.USEREVENT + 1,
        effect_sounds={"imposter_kill_sound": Recorder(),
                       "imposter_kill_cooldown_sound": Recorder()},
    )
    state.update(over)
    return SimpleNamespace(**state)


def test_a_kill_marks_the_bot_dead_and_swaps_its_sprite():
    game, bot = kill_game(), fake_bot()

    assert bot_kill(game, bot, keys_with(pg.K_RETURN)) is True
    assert bot.alive_status is False
    assert bot.image == "dead-sprite"


def test_a_kill_scores():
    game, bot = kill_game(), fake_bot()

    bot_kill(game, bot, keys_with(pg.K_RETURN))

    assert game.bot_killed == 1
    assert game.bot_count == 8


def test_a_kill_plays_the_kill_sound():
    game, bot = kill_game(), fake_bot()

    bot_kill(game, bot, keys_with(pg.K_RETURN))

    assert game.effect_sounds["imposter_kill_sound"].plays == 1


def test_a_kill_arms_the_cooldown():
    game, bot = kill_game(since_last_kill=99999), fake_bot()

    bot_kill(game, bot, keys_with(pg.K_RETURN))

    assert game.time_left_to_kill == 15
    assert game.killcooldown_start == game.killcooldown


def test_nothing_happens_without_the_kill_key():
    game, bot = kill_game(), fake_bot()

    assert bot_kill(game, bot, keys_with()) is False
    assert bot.alive_status is True


def test_a_kill_is_refused_inside_the_cooldown():
    game, bot = kill_game(since_last_kill=COOLDOWN_MS - 1), fake_bot()

    assert bot_kill(game, bot, keys_with(pg.K_RETURN)) is False
    assert bot.alive_status is True
    assert game.effect_sounds["imposter_kill_cooldown_sound"].plays == 1


def test_a_bot_can_only_be_killed_once():
    game, bot = kill_game(), fake_bot(killed=1)

    assert bot_kill(game, bot, keys_with(pg.K_RETURN)) is False
    assert game.bot_killed == 0


def test_an_already_dead_bot_cannot_be_killed_again():
    game, bot = kill_game(), fake_bot(alive=False)

    assert bot_kill(game, bot, keys_with(pg.K_RETURN)) is False


def test_a_crewmate_cannot_kill():
    game, bot = kill_game(imposter=False), fake_bot()

    assert bot_kill(game, bot, keys_with(pg.K_RETURN)) is False
    assert bot.alive_status is True


def test_an_imposter_hiding_in_a_vent_cannot_kill():
    game, bot = kill_game(invisible=1), fake_bot()

    assert bot_kill(game, bot, keys_with(pg.K_RETURN)) is False


@pytest.mark.parametrize("bot_type", BOT_TYPES)
def test_the_rule_is_identical_for_every_bot(bot_type):
    """The whole point of the collapse: ten bots, one rule."""
    game, bot = kill_game(), fake_bot(bot_type)

    assert bot_kill(game, bot, keys_with(pg.K_RETURN)) is True
    assert bot.alive_status is False
    assert game.bot_killed == 1


def test_apply_bot_kills_only_touches_bots_that_are_touching_the_player(monkeypatch):
    game = kill_game()
    near, far = fake_bot("bot1"), fake_bot("bot2")
    game.player.pos = None
    game.bots = [near, far]
    monkeypatch.setattr(pg.sprite, "spritecollide", lambda *a, **k: [near])

    apply_bot_kills(game, keys_with(pg.K_RETURN))

    assert near.alive_status is False
    assert far.alive_status is True
