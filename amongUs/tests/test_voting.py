"""Clicking a colour on the voting screen.

Five checkboxes, and the rule for each was written out longhand: set my tick
True and the other four False. Five restatements of one invariant, each of them
a chance to leave a stale tick behind.
"""

from types import SimpleNamespace

import pytest

from conftest import Recorder
from core.meeting import VOTE_CHECKBOXES, handle_vote_click

COLOURS = [colour for _button, colour, _tick in VOTE_CHECKBOXES]


class Checkbox:
    """A vote button that answers to one position."""

    def __init__(self, hits=False):
        self.hits = hits

    def click(self, pos):
        return self.hits


def voting_game(hit_colour=None, voted=None):
    game = SimpleNamespace(
        player=SimpleNamespace(voted=voted),
        effect_sounds={"vote_sound": Recorder()},
    )
    for button, colour, tick in VOTE_CHECKBOXES:
        setattr(game, button, Checkbox(hits=(colour == hit_colour)))
        setattr(game, tick, False)
    return game


def ticks(game):
    return {colour: getattr(game, tick)
            for _button, colour, tick in VOTE_CHECKBOXES}


@pytest.mark.parametrize("colour", COLOURS)
def test_voting_records_the_colour(colour):
    game = voting_game(hit_colour=colour)

    assert handle_vote_click(game, (0, 0)) is True
    assert game.player.voted == colour


@pytest.mark.parametrize("colour", COLOURS)
def test_voting_ticks_that_colour_and_no_other(colour):
    """The invariant the five hand-written blocks each restated."""
    game = voting_game(hit_colour=colour)

    handle_vote_click(game, (0, 0))

    assert ticks(game) == {c: (c == colour) for c in COLOURS}


@pytest.mark.parametrize("colour", COLOURS)
def test_a_second_vote_is_ignored(colour):
    game = voting_game(hit_colour=colour, voted="Green")

    handle_vote_click(game, (0, 0))

    assert game.player.voted == "Green"
    assert ticks(game) == {c: False for c in COLOURS}


def test_clicking_no_checkbox_records_nothing():
    game = voting_game(hit_colour=None)

    assert handle_vote_click(game, (0, 0)) is False
    assert game.player.voted is None


def test_the_vote_sound_plays_even_when_no_checkbox_was_hit():
    """Quirk preserved: the sound is on the click, not on the vote."""
    game = voting_game(hit_colour=None)

    handle_vote_click(game, (0, 0))

    assert game.effect_sounds["vote_sound"].plays == 1


def test_the_vote_sound_plays_on_a_successful_vote():
    game = voting_game(hit_colour="Red")

    handle_vote_click(game, (0, 0))

    assert game.effect_sounds["vote_sound"].plays == 1


def test_only_one_checkbox_is_consulted_per_click():
    """The original chained on elif, so the first hit wins."""
    game = voting_game()
    for button, _colour, _tick in VOTE_CHECKBOXES:
        getattr(game, button).hits = True

    handle_vote_click(game, (0, 0))

    assert game.player.voted == COLOURS[0]


def test_the_table_covers_every_colour_the_meeting_resets():
    """VOTE_CHECKBOXES and the meeting's reset list must not drift apart."""
    from core.meeting import VOTE_TICKS

    assert {tick for _b, _c, tick in VOTE_CHECKBOXES} == set(VOTE_TICKS)
