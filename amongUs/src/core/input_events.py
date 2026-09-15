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

from core.settings import *
from core import meeting
from minigames import asteroids

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


def dispatch(game, event):
    """Everything one event can do, in the order it used to happen.

    Returning ends this event's turn -- it was a `continue` in the loop,
    and means the same thing here: nothing further sees this event.
    """
    if event.type == pg.QUIT:
        game.quit()

    # While the discussion chat is up it owns the keyboard and the
    # clicks on its panel, so typing does not trigger game actions
    if game.meeting_chat.is_open and game.meeting_chat.handle_event(event):
        return

    # The six one-second countdowns
    if handle_timers(game, event):
        return



    if event.type == pg.KEYDOWN:
        # Create a toggle key for debugging collision
        # if key is H and game is not paused
        if event.key == pg.K_h and not game.paused:
            game.draw_debug = not game.draw_debug
        # Create a toggle key for night fog switch
        # if key is ctrl and game is not paused
        if (event.key == pg.K_LCTRL or event.key == pg.K_RCTRL) and not game.paused and game.emerg_meeting_button_status == 0:

            c = pygame.Vector2(2472, 1721)
            d = pygame.Vector2(game.player.pos.x, game.player.pos.y)
            if (game.sabotagecooldown - game.sabotagecooldown_start) > 15000 and game.night == False and game.night_reactor == False and game.player.imposter == True:
                game.night = True
                game.night_sync += 1
                game.light_bulb_timer_icon_status = False

            elif game.night == True and c.distance_to(d) <= DETECT_RADIUS_SABOTAGE_FIX:
                game.night = False

                # if player or imposter turn on the light then
                # reset the light timer and decrement light_timer_event
                game.time_left_to_light = 15
                pygame.time.set_timer(game.light_timer_event, 1000)
                game.light_bulb_timer_icon_status = True

                # if imposter or player turn on the light then
                # reset the ractor cooldown timer and decrement
                # reactor_timer_cooldown_event
                game.time_left_to_boom_cooldown = 15
                pg.time.set_timer(game.reactor_timer_cooldown_event, 1000)

                game.sabotagecooldown_start = game.sabotagecooldown
                game.night_sync += 1

            elif game.player.imposter == True:
                game.effect_sounds['imposter_kill_cooldown_sound'].play()

        if (event.key == pg.K_LSHIFT or event.key == pg.K_RSHIFT) and not game.paused and game.emerg_meeting_button_status == 0:
            c = pygame.Vector2(889, 999)
            d = pygame.Vector2(game.player.pos.x, game.player.pos.y)

            if (game.sabotagecooldown - game.sabotagecooldown_start) > 15000 and game.night_reactor == False and game.night == False and game.player.imposter == True:
                game.night_reactor = True
                game.night_reactor_sync += 1
                game.sabotagecritical = True

                # if sabotage_reactor is recharged and player presses K_shift in multiplayer mod then
                # show him meltdown_reactor timer of 20 secs and drecrement reactor_timer_event_client
                # by 1000 milliseconds
                if game.night_reactor and game.player.imposter and game.gamemode == "Multiplayer":
                    game.reactor_timer_visible_client_status = True
                    pg.time.set_timer(game.reactor_timer_event_client, 1000)
                if game.night_reactor and game.gamemode == "Freeplay":
                    game.reactor_timer_visible_client_status = True
                    pg.time.set_timer(game.reactor_timer_event_client, 1000)

                # If kill timer is off or kill timer equals = 0 then on key press K_Shift show reactor timer
                # on screen and start reactor_timer_event that decrements per second
                game.sabotage_timer_icon_status = False
                pygame.mixer.Channel(0).play(pygame.mixer.Sound(game.effect_sounds['crises_alarm']),
                                             loops=-1)
                game.sabotagecriticaltimer_start = pygame.time.get_ticks()

            # To Trigger Reactor meltdown Sabotage - Freeplay Mode
            elif game.night_reactor == True and c.distance_to(d) <= DETECT_RADIUS_SABOTAGE_FIX:
                game.night_reactor = False

                # if crew mates turns the reactor on then again reset the cooldown timer
                # so that it can again recharge for imposter to press K_shift and 
                # sabotage the reactor
                game.time_left_to_boom_cooldown = 15
                pg.time.set_timer(game.reactor_timer_cooldown_event, 1000)
                # show the reactor cooldown timer to imposter
                game.reactor_timer_cooldown_visible_status = True
                # Hide the sabotage reactor highlighted icon
                game.sabotage_timer_icon_status = False
                # Show the sabotage reactor dimmed icon
                game.sabotage_timer_icon_dim_status = True

                # if imposter turn on the reactor then again reset the
                # light timer to 15 so that it can be again used to turn
                # off the lights and decrement the light_timer_event
                game.time_left_to_light = 15
                pg.time.set_timer(game.light_timer_event, 1000)
                game.light_bulb_timer_icon_status = True

                game.sabotagecooldown_start = game.sabotagecooldown
                game.night_reactor_sync += 1
                game.sabotagecritical = False
                pygame.mixer.Channel(0).stop()

            elif game.player.imposter == True:
                game.effect_sounds['imposter_kill_cooldown_sound'].play()

        # if key is P or Esc then pause the game
        if event.key == pg.K_p or event.key == pg.K_ESCAPE:
            if not game.emergency:
                game.effect_sounds['go_back'].play()
                game.paused = not game.paused

        # Show mini map on Keypress TAB
        if event.key == pg.K_TAB and not game.view_admin_security_monitor_window_status and game.player.alive_status:
            game.effect_sounds['pause'].play()
            game.mini_map_button_status = not game.mini_map_button_status
            # If missions box is opened then close it when we press on TAB key to open mini map
            game.task_button_click_status = False

    # Check Mouse clicks the mini map button
    # Open map, play sound, change mini_map_button_status
    # if left mouse button is pressed and game is not paused
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and not game.emerg_meeting_button_status and not game.view_admin_security_monitor_window_status and game.player.alive_status:
        pos = pg.mouse.get_pos()
        if game.map_btn.click(pos):
            if game.map_btn.button_type == "mp_btn":
                game.effect_sounds['map_click2'].play()
                game.mini_map_button_status = not game.mini_map_button_status
                # If mission box is opened then close it when we click on mini map button
                game.task_button_click_status = False
    # For Pause Menu Buttons
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and game.paused:
        pos = pg.mouse.get_pos()
        if game.pause_btns.click(pos):
            # If player clicks quit game button
            if game.pause_btns.button_type == "pause_quit_btn":
                # game.effect_sounds['go_back'].play()
                # game.quit()
                # game.pause_quit_button_status = True
                game.menu.game_left(game.score_list, 'You Left The Game')
                game.game_left = True

    # Task Button
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.task_button_show_status and not game.view_admin_security_monitor_window_status and not game.mini_map_button_status:
        pos = pg.mouse.get_pos()
        if game.task_btn.click(pos):
            if game.task_btn.button_type == "tsk_btn":
                game.effect_sounds['map_click'].play()
                game.task_button_click_status = not game.task_button_click_status

    if game.gamemode == "Multiplayer":
        if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and not game.task_button_show_status:
            pos = pg.mouse.get_pos()
            if game.task_btn.click(pos):
                if game.task_btn.button_type == "tsk_btn":
                    game.effect_sounds['map_click'].play()
                    game.task_button_click_status = not game.task_button_click_status


    """ OPEN CAFETERIA COMPUTER BUTTONS & EVENTS """
    # Open Cafe Computer and Toggle Imposter Status
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.open_cafe_comp_window_status:
        pos = pg.mouse.get_pos()
        if game.open_cafe_comp_check_btn.click(pos):
            game.open_cafe_comp_check_pic_status = not game.open_cafe_comp_check_pic_status
            game.player.imposter = not game.player.imposter
            game.bot_count_show_status = not game.bot_count_show_status
            game.task_button_show_status = not game.task_button_show_status
            game.effect_sounds['invisible'].play()
        elif game.open_cafe_comp_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.open_cafe_comp_window_status = False
            game.open_cafe_comp_close_btn_status = False
            #game.open_cafe_comp_check_pic_status = False
            game.open_cafe_comp_sound_play_count += 1
            game.isdoingTask = False


    """ VIEW SECURITY MINI MAP BUTTON & EVENTS """
    # View Security Monitor Mini Map - Buttons
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.view_admin_security_monitor_window_status:
        pos = pg.mouse.get_pos()
        if game.view_security_monitor_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.view_admin_security_monitor_window_status = False
            game.view_admin_security_monitor_sound_play_count += 1
            game.isdoingTask = False


    """ STABILIZE NAVIGAITON TASK BUTTONS & EVENTS """
    # Stabilize Nav Button
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.target_center_sel_count == 1 and game.stabilize_steering_window_status:
        pos = pg.mouse.get_pos()
        if game.stabilize_target_center_btn.click(pos):
            game.effect_sounds['task_completed'].play()
            game.target_center_bt_status = True
            game.stabilize_target_btn1_status = False
            game.target_center_sel_count -= 1
            game.missions_done += 1
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.stabilize_steering_window_status:
        pos = pg.mouse.get_pos()
        if game.stabilize_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.effect_sounds['stabilize_nav_BG'].stop()
            game.target_center_bt_status = False
            game.stabilize_steering_button_status = False
            game.stabilize_steering_window_status = False
            game.stabilize_target_btn1_status = False
            game.stabilize_close_btn_status = False
            game.stablize_sound_play_count += 1
            game.isdoingTask = False


    """ EMPTY GARBAGE TASK BUTTONS & EVENTS """
    # Empty Garbage Button
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.garbage_liver_Up_sel_count == 1 and game.empty_garbage_window_status:
        pos = pg.mouse.get_pos()
        if game.garbage_liver_Up.click(pos):
            game.effect_sounds['task_completed'].play()
            game.garbage_liver_Up_status = False
            game.garbage_liver_Down_status = True
            game.empty_garbage_img_status = True
            game.garbage_liver_Up_sel_count -= 1
            game.empty_garbage_task_play_count -= 1
            game.missions_done += 1
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.empty_garbage_window_status:
        pos = pg.mouse.get_pos()
        if game.empty_garbage_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.effect_sounds['emtpy_garbage_BG'].fadeout(500)
            game.empty_garbage_window_status = False
            game.empty_garbage_close_btn_status = False
            game.empty_garbage_img_status = False
            game.empty_garbage_sound_play_count += 1
            game.isdoingTask = False


    """ REBOOT WIFI BUTTONS & EVENTS """
    # Reboot Wifi Button
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.reboot_wifi_liver_sel_count == 1 and game.reboot_wifi_window_status:
        pos = pg.mouse.get_pos()
        if game.reboot_wifi_liver.click(pos):
            game.effect_sounds['task_completed'].play()
            game.effect_sounds['rebooted_wifi_BG'].play(-1)
            game.reboot_wifi_liver_up_status = False
            game.reboot_wifi_liver_down_status = True
            game.rebooted_wifi_window_status = True
            game.reboot_wifi_liver_sel_count -= 1
            game.reboot_wifi_task_play_count -= 1
            game.missions_done += 1
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.reboot_wifi_window_status:
        pos = pg.mouse.get_pos()
        if game.reboot_wifi_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.effect_sounds['reboot_wifi_BG'].fadeout(500)
            game.effect_sounds['rebooted_wifi_BG'].fadeout(500)
            game.reboot_wifi_window_status = False
            game.reboot_wifi_liver_down_status = False
            game.reboot_wifi_sound_play_count += 1
            game.isdoingTask = False


    """ EMERGENCY MEETING & VOTING BUTTONS & EVENTS"""
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and (
            game.emerg_meeting_button_status or game.emerg_meeting_report_status) and game.emergency == True and game.player.alive_status == True:
        meeting.handle_vote_click(game, pg.mouse.get_pos())

    """ ELECTRIC WIRES TASK BUTTONS & EVENTS"""
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.electricity_wire_window_status:
        pos = pg.mouse.get_pos()
        if game.electricity_wire_red_btn.click(pos) and game.electricity_wires_red_sel_count == 1:
            random.choice(game.electric_shock_sounds['electric_shock']).play()
            game.electricity_wires_red_sel_count -= 1
            game.electricity_wires_fixed_count += 1
            game.electricity_wire_red_btn_status = True
        elif game.electricity_wire_blue_btn.click(pos) and game.electricity_wires_blue_sel_count == 1:
            random.choice(game.electric_shock_sounds['electric_shock']).play()
            game.electricity_wires_fixed_count += 1
            game.electricity_wires_blue_sel_count -= 1
            game.electricity_wire_blue_btn_status = True
        elif game.electricity_wire_yellow_btn.click(pos) and game.electricity_wires_yellow_sel_count == 1:
            random.choice(game.electric_shock_sounds['electric_shock']).play()
            game.electricity_wires_yellow_sel_count -= 1
            game.electricity_wires_fixed_count += 1
            game.electricity_wire_yellow_btn_status = True
        elif game.electricity_wire_pink_btn.click(pos) and game.electricity_wires_pink_sel_count == 1:
            random.choice(game.electric_shock_sounds['electric_shock']).play()
            game.electricity_wires_pink_sel_count -= 1
            game.electricity_wires_fixed_count += 1
            game.electricity_wire_pink_btn_status = True
        if game.electricity_wires_fixed_count == 4:
            game.effect_sounds['task_completed'].play()
            game.effect_sounds['fix_electric_wires_BG'].fadeout(500)
            game.effect_sounds['fixed_electric_wires_BG'].play(-1)
            game.missions_done += 1
            game.electricity_wire_task_play_count -= 1
            game.electricity_wires_fixed_count += 1

    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.electricity_wire_window_status:
        pos = pg.mouse.get_pos()
        if game.electricity_wire_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.effect_sounds['fix_electric_wires_BG'].fadeout(500)
            game.effect_sounds['fixed_electric_wires_BG'].fadeout(500)
            game.electricity_wire_window_status = False
            game.electricity_wire_close_btn_status = False
            game.electricity_wire_btns_visible = False
            game.electricity_wire_red_btn_status = False
            game.electricity_wire_blue_btn_status = False
            game.electricity_wire_yellow_btn_status = False
            game.electricity_wire_pink_btn_status = False
            game.electricity_wire_sound_play_count += 1
            game.electricity_wires_red_sel_count = 1
            game.electricity_wires_blue_sel_count = 1
            game.electricity_wires_yellow_sel_count = 1
            game.electricity_wires_pink_sel_count = 1
            game.electricity_wires_fixed_count = 0
            # game.missions_done += 1
            game.isdoingTask = False
    """ ELECTRIC WIRES TASK BUTTONS CODE CLOSES HERE"""

    """ DIVERT POWER TO REACTOR TASK BUTTONS & EVENTS"""
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.divert_power_to_reactor_window_status:
        pos = pg.mouse.get_pos()
        if game.divert_power_to_reactor_livers_btn.click(pos) and game.divert_power_to_reactor_liversUP_sel_count == 1:
            game.effect_sounds['task_completed'].play()
            game.divert_power_to_reactor_livers_btn_status = False
            game.divert_power_to_reactor_liversUP_status = True
            game.divert_power_to_reactor_task_play_count -= 1
            game.divert_power_to_reactor_liversUP_sel_count -= 1
            game.missions_done += 1
        elif game.divert_power_to_reactor_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.effect_sounds['fix_electric_wires_BG'].fadeout(500)
            game.divert_power_to_reactor_window_status = False
            game.divert_power_to_reactor_liversUP_status = False
            game.divert_power_to_reactor_close_btn_status = False
            game.divert_power_to_reactor_sound_play_count += 1
            game.isdoingTask = False

    """ ALIGN ENGINE OUTPUT TASK BUTTONS & EVENTS"""
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.align_engine_output_window_status:
        pos = pg.mouse.get_pos()
        if game.align_engine_liver_pos_btn1.click(pos) and game.align_engine_liver_pos_btn1_sel_count == 1:
            game.effect_sounds['map_click'].play()
            game.align_engine_output_window2_status = False
            game.align_engine_liver_status = False
            game.align_engine_output_window3_status = True
            game.align_engine_liver_pos_btn1_sel_count -= 1
        elif game.align_engine_liver_pos_btn2.click(pos) and game.align_engine_liver_pos_btn2_sel_count == 1 and game.align_engine_liver_pos_btn1_sel_count < 1:
            game.effect_sounds['task_completed'].play()
            game.align_engine_output_window3_status = False
            game.align_engine_liver_pos_btn1_status = False
            game.align_engine_output_window4_status = True
            game.align_engine_liver_pos_btn2_sel_count -= 1
            game.align_engine_output_task_play_count -=1
            game.missions_done += 1
        # if player has not click on button 1 and he then clicks button 2 then play error sound
        if game.align_engine_liver_pos_btn2.click(pos) and game.align_engine_liver_pos_btn1_sel_count == 1:
            game.effect_sounds['imposter_kill_cooldown_sound'].play()

    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.align_engine_output_window_status:
        pos = pg.mouse.get_pos()
        if game.align_engine_output_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.align_engine_output_window_status = False
            game.align_engine_liver_status = False
            game.align_engine_output_window2_status = False
            game.align_engine_output_window3_status = False
            game.align_engine_output_window4_status = False
            game.align_engine_liver_pos_btn1_status = False
            game.align_engine_liver_pos_btn2_status = False
            game.align_engine_output_close_btn_status = False
            game.isdoingTask = False
            if game.align_engine_liver_pos_btn1_sel_count > 1 or game.align_engine_liver_pos_btn1_sel_count < 1:
                game.align_engine_liver_pos_btn1_sel_count = 1
            game.align_engine_output_sound_play_count += 1

    """ FUEL ENGINE TASK BUTTONS & EVENTS"""
    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and game.fuel_engine_fill_btn_sel_count == 1 and not game.paused and game.fuel_engine_window_status:
        pos = pg.mouse.get_pos()
        if game.fuel_engine_fill_btn.click(pos):
            game.effect_sounds['fill_gas_can'].play()
            game.fuel_level -= 10
            if game.fuel_level <= 0:
                game.fuel_engine_fill_btn_sel_count -=1
                game.effect_sounds['task_completed'].play()
                game.missions_done += 1
                game.is_gas_can_picked = False
                game.fuel_engine_task_play_count -=1

    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.fuel_engine_window_status:
        pos = pg.mouse.get_pos()
        if game.fuel_engine_close_btn.click(pos):
            game.effect_sounds['go_back'].play()
            game.fuel_engine_window_status = False
            game.fuel_engine_close_btn_status = False
            game.isdoingTask = False
            game.fuel_engine_sound_play_count +=1

    if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON and not game.paused and game.gas_can_not_picked_text_visible_status:
        pos = pg.mouse.get_pos()
        if game.fuel_engine_close_btn2.click(pos):
            game.gas_can_not_picked_text_visible_status = False
            game.isdoingTask = False

    """ CLEAR ASTEROIDS TASK BUTTONS & EVENTS"""
    # Check if Left /Right /Up /Down key is pressed
    asteroids.handle_event(game, event)


def pump(game):
    """Drain the event queue for this frame."""
    for event in pg.event.get():
        dispatch(game, event)
