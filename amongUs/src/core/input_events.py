"""Pumping the event queue.

The frame's input, in the order it has to happen:

    quit           closing the window
    the chat       while the discussion is up it owns the keyboard
    timers         the six one-second countdowns
    everything else

The chat's turn is not a formality. While a meeting is open, keystrokes are
being typed into a text box, and if they also reached the game then "p" would
pause it and "h" would flip the debug overlay. The loop `continue`s past every
remaining handler when the chat takes an event -- which is why the handlers
below *return* whether they consumed it and pump() does the skipping. A helper
that returned early on its own would only skip its own body.
"""

from collections import namedtuple

import pygame
import pygame as pg

# event      the attribute holding this timer's pygame user event
# counter    what it counts down
# visible    only ticks while this is set
# on_zero    a flag to raise when it reaches zero, if any
Timer = namedtuple("Timer", "event counter visible on_zero")

TIMERS = (
    Timer("light_timer_event", "time_left_to_light",
          "light_timer_visible_status", None),
    Timer("kill_timer_event", "time_left_to_kill",
          "kill_timer_visible_status", None),
    Timer("reactor_timer_cooldown_event", "time_left_to_boom_cooldown",
          "reactor_timer_cooldown_visible_status", "sabotage_timer_icon_status"),
    Timer("reactor_timer_event_client", "time_left_to_boom_client",
          "reactor_timer_visible_client_status", None),
    Timer("meeting_timer_event", "time_left_to_end_meeting",
          "meeting_timer_visible_status", None),
    Timer("meeting_timer_cooldown_event", "time_left_to_end_meeting_cooldown",
          "meeting_timer_cooldown_visible_status", "emergency_timer_icon_status"),
)


def handle_timers(game, event):
    """Tick whichever countdown this event belongs to. True if it was one."""
    for timer in TIMERS:
        if event.type != getattr(game, timer.event):
            continue
        if not getattr(game, timer.visible):
            return False

        setattr(game, timer.counter, getattr(game, timer.counter) - 1)
        if getattr(game, timer.counter) == 0:
            if timer.on_zero:
                setattr(game, timer.on_zero, True)
            pygame.time.set_timer(getattr(game, timer.event), 0)
        return True
    return False


def handle_keydown(game, event):
    """Placeholder until the keyboard handlers move here."""
    return False


def pump(game):
    """Drain the event queue for this frame."""
    for event in pg.event.get():
        if event.type == pg.QUIT:
            game.quit()

        # While the discussion chat is up it owns the keyboard and the clicks
        # on its panel, so typing does not trigger game actions.
        if game.meeting_chat.is_open and game.meeting_chat.handle_event(event):
            continue

        if handle_timers(game, event):
            continue

        handle_keydown(game, event)
