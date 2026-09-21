"""Drawing the task windows.

Each task, once opened, blits its own panel and whatever widgets it owns
over a dimmed screen. These are sequences of blits against fixed offsets --
there is no logic here to test beyond that they run, which is what the
smoke tests assert and all they honestly can.

What opens these windows lives in core/task_triggers.py; what the buttons
inside them do lives in the mouse handlers.
"""

import pygame
import pygame as pg

from core.paths import asset
from core.settings import *
from core.sprites import *      # Button, which the navigation task builds inline
from core import task_triggers
from minigames import asteroids


def draw_task_windows(game):
    """Draw whichever task windows are currently open."""
    # Open Cafeteria Computer and Toggle Imposter Status
    if game.open_cafe_comp_window_status and game.isdoingTask:
        game.screen.blit(game.dim_screen, (0,0))
        game.display_open_cafe_comp_window()
        if game.open_cafe_comp_check_btn_status:
            game.open_cafe_comp_check_btn.draw_Image(game.screen)
        if game.open_cafe_comp_check_pic_status:
            game.display_open_cafe_comp_check_window()
        if game.open_cafe_comp_close_btn_status:
            game.open_cafe_comp_close_btn.draw_Image(game.screen)

    # Open Cafeteria Computer Task trigger
    keys = pg.key.get_pressed()
    c = pygame.Vector2(3060, 385)
    d = pygame.Vector2(game.player.pos.x, game.player.pos.y)
    if d.distance_to(c) <= 200 and game.gamemode == "Freeplay":
        if keys[pg.K_SPACE] and game.open_cafe_comp_sound_play_count == 1:
            game.effect_sounds['selected'].play()
            game.open_cafe_comp_window_status = True
            game.open_cafe_comp_check_btn_status = True
            game.open_cafe_comp_close_btn_status = True
            game.isdoingTask = True
            game.open_cafe_comp_sound_play_count -= 1

    # Stabilize the Navigation Task
    game.i = WIDTH / 2 - 18
    game.j = HEIGHT / 2 - 4

    game.stabilize_target_btn1 = Button(game, None, None, 56, 56, WIDTH / 2, 60, "stbl_nav_btn",
                                        Transparent_Black,
                                        Transparent_Black,
                                        asset("Assets/Images/Tasks/Stabilize Steering/nav_stabilize_target.png"), 128,
                                        128,
                                        255)
    game.stabilize_target_center_btn = Button(game, None, None, 10, 10, game.i, game.j, "target_center_btn",
                                              Transparent_Black,
                                              Transparent_Black,
                                              asset("Assets/Images/Tasks/Stabilize Steering/target_center.png"), 10,
                                              10,
                                              255)
    game.stabilize_close_btn = Button(game, None, None, 65, 65, WIDTH / 1.5 + 80, 40, "stbl_close_btn",
                                      Transparent_Black,
                                      Transparent_Black,
                                      asset("Assets/Images/Tasks/Stabilize Steering/close.png"), 65, 65,
                                      255)

    if game.stabilize_steering_button_status and game.stabilize_steering_window_status and game.isdoingTask:
        game.screen.blit(game.dim_screen, (0, 0))
        game.display_stablize_navigation_window()
        game.stabilize_target_center_btn.draw_Image(game.screen)
        if game.stabilize_close_btn_status:
            game.stabilize_close_btn.draw_Image((game.screen))
        if game.stabilize_target_btn1_status:
            game.stabilize_target_btn1.draw_Image(game.screen)

    if game.target_center_bt_status:
        i = game.navigation_screen_img.get_width() / 3 + 20
        j = game.navigation_screen_img.get_height() / 3 + 20
        game.stabilize_target_btn1_status = False
        game.stabilize_target_btn2 = Button(game, None, None, 56, 56, i, j, "stbl_nav_btn", Transparent_Black,
                                            Transparent_Black,
                                            asset("Assets/Images/Tasks/Stabilize Steering/nav_stabilize_target.png"),
                                            128, 128, 255)
        game.stabilize_target_btn2.draw_Image(game.navigation_screen_img)
        game.stabilize_task_play_count -= 1

    # Every task you can walk up to and open; see core/task_triggers.py.
    task_triggers.fire_all(game, pg.key.get_pressed())
    ''' Yes'''

    ''' Yes'''
    # Empty the Garbage - Task

    if game.empty_garbage_window_status and game.isdoingTask:
        game.screen.blit(game.dim_screen, (0, 0))
        game.display_full_garbage_window()
        if game.garbage_liver_Up_status:
            game.garbage_liver_Up.draw_Image(game.screen)
        if game.garbage_liver_Down_status:
            game.garbage_liver_Down.draw_Image(game.screen)
        if game.empty_garbage_img_status:
            game.display_empty_garbage_window()
        if game.empty_garbage_close_btn_status:
            game.empty_garbage_close_btn.draw_Image(game.screen)

    # Empty the garbage Task trigger
    ''' Yes'''

    ''' Yes'''
    # Reboot Wifi Task

    if game.reboot_wifi_window_status and game.isdoingTask:
        game.screen.blit(game.dim_screen, (0, 0))
        game.display_reboot_wifi_window()
        game.reboot_wifi_close_btn.draw_Image(game.screen)
        if game.reboot_wifi_liver_up_status:
            game.reboot_wifi_liver.draw_Image(game.screen)
        if game.reboot_wifi_liver_down_status:
            game.display_reboot_wifi_liver_down()
        if game.rebooted_wifi_window_status:
            game.display_rebooted_wifi_window()

    # Reboot Wifi Task trigger
    ''' Yes'''

    ''' Yes'''
    # Fix Electricity Wires Task
    if game.electricity_wire_window_status and game.isdoingTask:
        game.screen.blit(game.dim_screen, (0, 0))
        game.display_electricity_wire_window()
        if game.electricity_wire_close_btn_status:
            game.electricity_wire_close_btn.draw_Image(game.screen)
        if game.electricity_wire_btns_visible:
            game.electricity_wire_red_btn.draw_Image(game.screen)
            game.electricity_wire_blue_btn.draw_Image(game.screen)
            game.electricity_wire_yellow_btn.draw_Image(game.screen)
            game.electricity_wire_pink_btn.draw_Image(game.screen)
            if game.electricity_wire_red_btn_status:
                game.display_electricity_red()
            if game.electricity_wire_blue_btn_status:
                game.display_electricity_blue()
            if game.electricity_wire_yellow_btn_status:
                game.display_electricity_yellow()
            if game.electricity_wire_pink_btn_status:
                game.display_electricity_pink()

    # Fix Electricity Wires Task Trigger

    ''' Yes'''
    # Divert Power to Reactor Task
    if game.divert_power_to_reactor_window_status and game.isdoingTask:
        game.screen.blit(game.dim_screen, (0, 0))
        game.display_divert_power_to_reactor_window()
        if game.divert_power_to_reactor_livers_btn_status:
            game.divert_power_to_reactor_livers_btn.draw_Image(game.screen)
        if game.divert_power_to_reactor_liversUP_status:
            game.display_power_diverted_to_reactor_window()
            game.display_divert_power_to_reactor_liverUp_window()
        if game.divert_power_to_reactor_close_btn_status:
            game.divert_power_to_reactor_close_btn.draw_Image(game.screen)


    # Divert Power to Reactor Task Trigger

    ''' Yes'''
    # Align Engine Output Task
    if game.align_engine_output_window_status and game.isdoingTask:
        game.display_align_engine_output_window()
        if game.align_engine_output_window2_status:
            game.display_align_engine_output_window2()
        if game.align_engine_output_window2_status:
            game.display_align_engine_output_window2()
        if game.align_engine_liver_status:
            game.display_align_engine_liver(WIDTH / 2 + 130, 100)
        if game.align_engine_output_window2_status:
            game.display_align_engine_output_window2()
        if game.align_engine_liver_pos_btn1_status:
            game.align_engine_liver_pos_btn1.draw_Image(game.screen)
        if game.align_engine_liver_pos_btn2_status:
            game.align_engine_liver_pos_btn2.draw_Image(game.screen)
        if game.align_engine_output_window3_status:
            game.display_align_engine_output_window3()
            game.display_align_engine_liver(WIDTH / 2 + 100, 195)
        if game.align_engine_output_window4_status:
            game.display_align_engine_output_window4()
            game.display_align_engine_liver(WIDTH / 2 + 100, 285)
        if game.align_engine_output_close_btn_status:
            game.align_engine_output_close_btn.draw_Image(game.screen)

    # Align Engine Output Task Trigger
    ''' Yes'''


    ''' Yes'''
    # Fuel Engine Task
    game.fuel_engine_yellow_bg = pg.Surface((340, 495))
    game.fuel_engine_yellow_bg.fill((235, 195, 52))
    if game.fuel_level <= 0:
        game.fuel_level = 1
    game.fuel_engine_filled_black_reverse_bg = pg.Surface((340, game.fuel_level))
    game.fuel_engine_filled_black_reverse_bg.fill((0, 0, 0))

    if game.fuel_engine_window_status and game.isdoingTask:
        game.screen.blit(game.dim_screen, (0,0))
        game.screen.blit(game.fuel_engine_yellow_bg, (WIDTH / 3 - 45, 70))
        game.screen.blit(game.fuel_engine_filled_black_reverse_bg, (WIDTH / 3 - 45, 167))
        game.display_fuel_engine_window()
        if game.fuel_engine_fill_btn_status:
            game.fuel_engine_fill_btn.draw_Image(game.screen)
        if game.fuel_engine_close_btn_status:
            game.fuel_engine_close_btn.draw_Image(game.screen)
    if game.is_gas_can_picked and not game.isdoingTask:
        game.display_gas_can_picked()

    # IF player has not picked up gas can then show text
    GAME_FONT = pygame.font.Font(FONT, 34)
    if game.gas_can_not_picked_text_visible_status:
        game.screen.blit(game.fuel_engine_filled_black_bg, (WIDTH / 3 - 45, 70))
        game.display_fuel_engine_window()
        game.screen.blit(game.dim_screen, (0, 0))
        game.text = GAME_FONT.render(" Find a Gas Can Nearby", True, WHITE)
        game.screen.blit(game.text, (450, HEIGHT/2 - 30))
        game.fuel_engine_close_btn2.draw_Image(game.screen)

    # The gas can and the engine it fuels; neither fits the trigger table.
    task_triggers.gas_can_trigger(game, pg.key.get_pressed())
    task_triggers.fuel_engine_trigger(game, pg.key.get_pressed())
    ''' Yes'''


    ''' Yes'''
    # Clear Asteroid Task
    # The asteroid shooter draws and runs itgame.
    asteroids.draw_window(game)

    # Clear Asteroid Task Trigger
    keys = pg.key.get_pressed()
    c = pygame.Vector2(4513, 450)
    d = pygame.Vector2(game.player.pos.x, game.player.pos.y)
    if d.distance_to(c) <= DETECT_RADIUS and game.clear_asteroid_sound_play_count == 1 and game.clear_asteroid_task_play_count == 1:
        if game.player.imposter == False:
            if keys[pg.K_SPACE]:
                game.asteroid_bg.play(-1, -1, 1500)
                game.clear_asteroid_task_window_status = True
                game.clear_asteroid_task_available = True
                game.isdoingTask = True
                game.clear_asteroid_sound_play_count -=1

