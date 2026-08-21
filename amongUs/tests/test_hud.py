"""The task checklist in the corner of the screen.

Nine rows, each rendered green while outstanding and white once done, and each
written out longhand as its own six-line if/else. Two of the nine do not follow
the pattern the other seven do, which is exactly why the colour decision is
pulled out as a value rather than folded into the blitting.
"""

from types import SimpleNamespace

import pytest

from core.hud import MISSION_ROWS, mission_row_colours
from core.settings import GREEN, WHITE


def hud_game(**over):
    titles = SimpleNamespace(**{row.title: row.title for row in MISSION_ROWS})
    state = {row.guard: 0 for row in MISSION_ROWS}
    state["night"] = False
    state["tasks"] = titles
    state.update(over)
    return SimpleNamespace(**state)


def colour_of(game, guard):
    for row, (_text, colour, _y) in zip(MISSION_ROWS, mission_row_colours(game)):
        if row.guard == guard:
            return colour
    raise AssertionError("no row guarded by %s" % guard)


COUNT_ROWS = [row.guard for row in MISSION_ROWS if row.guard != "night"]


@pytest.mark.parametrize("guard", COUNT_ROWS)
def test_an_outstanding_task_is_green(guard):
    # The counter starts at 1 and is spent when the task completes, so 1 means
    # "not done yet".
    assert colour_of(hud_game(**{guard: 0}), guard) == GREEN


@pytest.mark.parametrize("guard", COUNT_ROWS)
def test_a_completed_task_is_white(guard):
    assert colour_of(hud_game(**{guard: 1}), guard) == WHITE


def test_the_lights_row_is_green_while_the_lights_are_on():
    """Row 0 is the odd one: a boolean, read the other way round.

    Every other row asks "has this counter been spent"; this one asks "is it
    dark". Normalising it into the same shape as the rest would invert the
    lights indicator and nothing else would notice.
    """
    assert colour_of(hud_game(night=False), "night") == GREEN


def test_the_lights_row_is_white_while_the_lights_are_out():
    assert colour_of(hud_game(night=True), "night") == WHITE


def test_the_garbage_row_reads_the_lever_count_not_the_task_count():
    """The other odd one: it is guarded by a sel_count, unlike its neighbours.

    Inconsistent with the seven task_play_count rows around it, and preserved.
    """
    row = next(r for r in MISSION_ROWS if "garbage" in r.title)

    assert row.guard == "garbage_liver_Up_sel_count"


def test_there_are_nine_rows():
    assert len(MISSION_ROWS) == 9


def test_every_row_has_a_title_a_colour_and_a_position():
    rows = mission_row_colours(hud_game())

    assert len(rows) == 9
    for text, colour, y in rows:
        assert isinstance(text, str) and text
        assert colour in (GREEN, WHITE)
        assert isinstance(y, int)


def test_the_rows_are_evenly_spaced_down_the_box():
    ys = [y for _text, _colour, y in mission_row_colours(hud_game())]

    assert ys == sorted(ys)
    assert len(set(ys)) == len(ys)


def test_every_title_exists_on_the_task_object():
    """The titles are attribute names on core/tasks.py's Task."""
    from core.tasks import Task

    task = Task(SimpleNamespace())
    for row in MISSION_ROWS:
        assert hasattr(task, row.title), row.title
