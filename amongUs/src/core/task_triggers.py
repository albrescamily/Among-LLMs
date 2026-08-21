"""Walking up to a task and pressing SPACE to start it.

Eleven places in draw() did the same six things: measure the distance to a
fixed point on the map, check SPACE, check the task is not already done, check
the player is not the imposter, play a sound, and open the window.

Six of them are uniform enough to be rows in a table. The other five are not,
and they stay explicit functions in this module rather than growing optional
fields on the table -- a field only one row uses is a function in disguise:

    cafeteria      no completion guard, a literal radius, Freeplay only, and it
                   deliberately has no imposter check because it *is* the
                   imposter toggle
    gas can        no window and no isdoingTask, decrements two counters, and
                   guards on a different task's completion flag
    fuel           branches: with the can it opens the window, without it shows
                   a "you need the can" line instead
    asteroids      starts a mini-game rather than opening a window
    admin monitor  two anchors, never completes, and needs the player alive

`keys` is a parameter, not a call to pg.key.get_pressed() in here. That is
deliberate twice over: it makes every one of these testable without a keyboard,
and it fixes a real bug. Six of the eleven triggers used to read a `keys` local
that the *wifi* trigger left behind in draw()'s frame -- so any of them moved
out on its own would have raised NameError.
"""

from collections import namedtuple

import pygame
import pygame as pg

from core.settings import (ALIGN_ENGINE_OUTPUT, DIVERT_POWER_TOP_REACTOR_RADIUS,
                           EMPTY_GARBAGE_RADIUS, FIX_ELECTRICITY_WIRES_RADIUS,
                           FUEL_ENGINE, PICK_STORAGE_GAS_CAN_RADIUS,
                           REBOOT_WIFI_RADIUS, STABILIZE_NAV_RADIUS)

Trigger = namedtuple("Trigger", "anchor radius arm_guard once_guard sounds sets")

TRIGGERS = (
    Trigger(
        anchor=(5610, 1290), radius=STABILIZE_NAV_RADIUS,
        arm_guard="stablize_sound_play_count",
        once_guard="stabilize_task_play_count",
        sounds=("selected", ("stabilize_nav_BG", -1)),
        sets=("stabilize_steering_button_status", "stabilize_steering_window_status",
              "stabilize_target_btn1_status", "stabilize_close_btn_status")),

    Trigger(
        anchor=(3940, 321), radius=EMPTY_GARBAGE_RADIUS,
        arm_guard="empty_garbage_sound_play_count",
        once_guard="empty_garbage_task_play_count",
        sounds=("selected", ("emtpy_garbage_BG", -1)),
        sets=("empty_garbage_window_status", "garbage_liver_Up_status",
              "empty_garbage_close_btn_status")),

    Trigger(
        anchor=(3700, 1554), radius=REBOOT_WIFI_RADIUS,
        arm_guard="reboot_wifi_sound_play_count",
        once_guard="reboot_wifi_task_play_count",
        sounds=("selected", ("reboot_wifi_BG", -1)),
        sets=("reboot_wifi_window_status", "reboot_wifi_liver_up_status")),

    Trigger(
        anchor=(3166, 1846), radius=FIX_ELECTRICITY_WIRES_RADIUS,
        arm_guard="electricity_wire_sound_play_count",
        once_guard="electricity_wire_task_play_count",
        sounds=("selected", ("fix_electric_wires_BG", -1)),
        sets=("electricity_wire_window_status", "electricity_wire_close_btn_status",
              "electricity_wire_btns_visible")),

    Trigger(
        anchor=(1031, 1216), radius=DIVERT_POWER_TOP_REACTOR_RADIUS,
        arm_guard="divert_power_to_reactor_sound_play_count",
        once_guard="divert_power_to_reactor_task_play_count",
        sounds=("selected", ("fix_electric_wires_BG", -1)),
        sets=("divert_power_to_reactor_window_status",
              "divert_power_to_reactor_livers_btn_status",
              "divert_power_to_reactor_close_btn_status")),

    Trigger(
        anchor=(1117, 837), radius=ALIGN_ENGINE_OUTPUT,
        arm_guard="align_engine_output_sound_play_count",
        once_guard="align_engine_output_task_play_count",
        sounds=("selected",),
        sets=("align_engine_output_window_status", "align_engine_liver_status",
              "align_engine_liver_pos_btn1_status", "align_engine_liver_pos_btn2_status",
              "align_engine_output_window2_status",
              "align_engine_output_close_btn_status")),
)


def in_range(game, anchor, radius):
    """Is the player standing close enough to this point on the map?"""
    here = pygame.Vector2(game.player.pos.x, game.player.pos.y)
    return pygame.Vector2(*anchor).distance_to(here) <= radius


def play(game, sounds):
    """Play a trigger's sounds; a tuple carries the loop count."""
    for sound in sounds:
        name, loops = sound if isinstance(sound, tuple) else (sound, 0)
        game.effect_sounds[name].play(loops)


def fire(game, keys, trigger):
    """Open one task if the player is on it and asking. True if it opened."""
    if not in_range(game, trigger.anchor, trigger.radius):
        return False
    if not keys[pg.K_SPACE]:
        return False
    if getattr(game, trigger.arm_guard) != 1:
        return False
    if getattr(game, trigger.once_guard) != 1:
        return False
    if game.player.imposter:
        return False

    play(game, trigger.sounds)
    for flag in trigger.sets:
        setattr(game, flag, True)
    game.isdoingTask = True

    # disarm, so holding SPACE does not reopen the window every frame
    setattr(game, trigger.arm_guard, getattr(game, trigger.arm_guard) - 1)
    return True


def fire_all(game, keys):
    """Offer every tabled task the chance to open."""
    for trigger in TRIGGERS:
        fire(game, keys, trigger)


# -- the ones that do not fit the table ------------------------------------

GAS_CAN_ANCHOR = (3056, 2443)
FUEL_ENGINE_ANCHOR = (1226, 2300)


def gas_can_trigger(game, keys):
    """Pick up the can the engine needs. True if picked up.

    Not a table row: it opens no window and sets no isdoingTask, it decrements
    two counters rather than one, and it guards on the *fuel engine's*
    completion flag rather than one of its own.
    """
    if not in_range(game, GAS_CAN_ANCHOR, PICK_STORAGE_GAS_CAN_RADIUS):
        return False
    if not keys[pg.K_SPACE]:
        return False
    if (game.fuel_engine_task_play_count != 1 or game.gas_can_picking_count != 1
            or game.gas_can_picking_sound_play_count != 1 or game.player.imposter):
        return False

    game.effect_sounds['pick_gas_can'].play()
    game.is_gas_can_picked = True
    game.gas_can_not_picked_text_visible_status = False
    game.gas_can_picking_count -= 1
    game.gas_can_picking_sound_play_count -= 1
    return True


def fuel_engine_trigger(game, keys):
    """Fuel the engine, or be told you need the can. True if the window opened.

    Not a table row: it branches. Without the can it opens nothing and shows a
    line of text instead -- but still sets isdoingTask, so the text has
    somewhere to be drawn.
    """
    if not in_range(game, FUEL_ENGINE_ANCHOR, FUEL_ENGINE):
        return False
    if not keys[pg.K_SPACE]:
        return False
    if (game.fuel_engine_sound_play_count != 1
            or game.fuel_engine_task_play_count != 1 or game.player.imposter):
        return False

    if not game.is_gas_can_picked:
        game.gas_can_not_picked_text_visible_status = True
        game.isdoingTask = True
        return False

    game.effect_sounds['selected'].play()
    game.fuel_engine_window_status = True
    game.fuel_engine_fill_btn_status = True
    game.fuel_engine_close_btn_status = True
    game.isdoingTask = True
    game.fuel_engine_sound_play_count -= 1
    return True
