"""Pumping the event queue.

The six countdown timers are the testable part: each is a pygame user event
that fires once a second, decrements its own counter, and switches itself off
at zero. Six near-identical handlers, and a table of which counter belongs to
which event is exactly the thing that could be got wrong invisibly.

The other thing pinned here is the chat's first refusal. While the discussion
is up, the chat owns the keyboard, and the loop `continue`s past every other
handler. That must stay a `continue` in the loop -- a helper that returns early
would only skip its own body, and typing "p" during a meeting would pause the
game.
"""

from types import SimpleNamespace

import pygame as pg
import pytest

from core import input_events
from core.input_events import TIMERS, handle_timers

IDS = [timer.counter for timer in TIMERS]


def timer_game(**over):
    state = {}
    for index, timer in enumerate(TIMERS):
        state[timer.event] = pg.USEREVENT + 1 + index
        state[timer.counter] = 3
        state[timer.visible] = True
        if timer.on_zero:
            state[timer.on_zero] = False
    state.update(over)
    return SimpleNamespace(**state)


def tick(game, timer):
    return handle_timers(game, pg.event.Event(getattr(game, timer.event)))


@pytest.mark.parametrize("timer", TIMERS, ids=IDS)
def test_a_tick_decrements_its_own_counter(timer):
    game = timer_game()

    assert tick(game, timer) is True
    assert getattr(game, timer.counter) == 2


@pytest.mark.parametrize("timer", TIMERS, ids=IDS)
def test_a_tick_leaves_every_other_counter_alone(timer):
    """The cross-wiring test: six events, six counters, one pairing."""
    game = timer_game()

    tick(game, timer)

    for other in TIMERS:
        if other.counter != timer.counter:
            assert getattr(game, other.counter) == 3, other.counter


@pytest.mark.parametrize("timer", TIMERS, ids=IDS)
def test_a_hidden_timer_does_not_tick(timer):
    game = timer_game(**{timer.visible: False})

    tick(game, timer)

    assert getattr(game, timer.counter) == 3


@pytest.mark.parametrize("timer", TIMERS, ids=IDS)
def test_reaching_zero_stops_the_timer(timer, monkeypatch):
    stopped = []
    monkeypatch.setattr(pg.time, "set_timer",
                        lambda event, ms: stopped.append((event, ms)))
    game = timer_game(**{timer.counter: 1})

    tick(game, timer)

    assert stopped == [(getattr(game, timer.event), 0)]


@pytest.mark.parametrize("timer", [t for t in TIMERS if t.on_zero],
                         ids=[t.counter for t in TIMERS if t.on_zero])
def test_the_cooldown_timers_light_their_icon_at_zero(timer, monkeypatch):
    monkeypatch.setattr(pg.time, "set_timer", lambda *a: None)
    game = timer_game(**{timer.counter: 1})

    tick(game, timer)

    assert getattr(game, timer.on_zero) is True


def test_an_unrelated_event_is_not_consumed():
    game = timer_game()

    assert handle_timers(game, pg.event.Event(pg.MOUSEBUTTONDOWN)) is False


def test_every_timer_has_its_own_event_and_counter():
    assert len({t.event for t in TIMERS}) == len(TIMERS)
    assert len({t.counter for t in TIMERS}) == len(TIMERS)


# -- the chat's first refusal ---------------------------------------------

class Chat:
    def __init__(self, is_open=False, consumes=False):
        self.is_open = is_open
        self.consumes = consumes

    def handle_event(self, event):
        return self.consumes


def pumping_game(chat):
    reached = []
    game = timer_game()
    game.meeting_chat = chat
    game.quit = lambda: reached.append("quit")
    game.reached = reached
    return game


def test_a_key_typed_into_the_chat_never_reaches_the_game(monkeypatch):
    """The single most important assertion about events().

    If an extraction ever turns that `continue` into an early return, typing
    into the meeting chat starts triggering game actions -- "p" pauses, "h"
    toggles the debug overlay.
    """
    game = pumping_game(Chat(is_open=True, consumes=True))
    typed = pg.event.Event(pg.KEYDOWN, key=pg.K_p)
    monkeypatch.setattr(pg.event, "get", lambda: [typed])
    seen = []
    monkeypatch.setattr(input_events, "handle_keydown",
                        lambda g, e: seen.append(e) or True)

    input_events.pump(game)

    assert seen == []


def test_a_key_reaches_the_game_when_the_chat_is_closed(monkeypatch):
    game = pumping_game(Chat(is_open=False))
    typed = pg.event.Event(pg.KEYDOWN, key=pg.K_p)
    monkeypatch.setattr(pg.event, "get", lambda: [typed])
    seen = []
    monkeypatch.setattr(input_events, "handle_keydown",
                        lambda g, e: seen.append(e) or True)

    input_events.pump(game)

    assert seen == [typed]


def test_a_key_reaches_the_game_when_the_chat_declines_it(monkeypatch):
    # The chat is up but does not want this event -- an arrow key, say.
    game = pumping_game(Chat(is_open=True, consumes=False))
    typed = pg.event.Event(pg.KEYDOWN, key=pg.K_p)
    monkeypatch.setattr(pg.event, "get", lambda: [typed])
    seen = []
    monkeypatch.setattr(input_events, "handle_keydown",
                        lambda g, e: seen.append(e) or True)

    input_events.pump(game)

    assert seen == [typed]


def test_closing_the_window_quits(monkeypatch):
    game = pumping_game(Chat())
    monkeypatch.setattr(pg.event, "get", lambda: [pg.event.Event(pg.QUIT)])

    input_events.pump(game)

    assert game.reached == ["quit"]
