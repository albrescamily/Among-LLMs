"""Applying the server's broadcast to the world we are drawing.

Rows are addressed by position, so the bare integers below are the wire
format itself; protocol.py names the handful that were added later.

Every row repeats on every frame until something changes, so the guards
here are mostly 'have I already applied this' -- the *_sync counters only
ever move forward, and the chat drops what it has already shown.
"""

import pygame
import pygame as pg

from core.sprites import Player, vec
from multiplayer import protocol


def apply_row(self, p, player_id):
    """One player's row out of the broadcast, applied to the local world.

    The first parameter is called `self` on purpose, and renaming it breaks
    multiplayer. Peers send the sprite they are showing as a *string of
    Python source* -- core/sprites.py builds strings like
    "self.Players[p[0]].player_imgs_left" -- which is eval'd below and so
    resolves `self` and `p` out of this function's own frame.

    (That the wire carries executable source at all is a remote-code hole
    over the LAN. Out of scope here; test_world_sync now makes replacing it
    with a lookup table a contained change.)
    """
    # case1, when local player is connected and needs to be appended to the dictionary
    # check if player is not already in the dictionary, and if the player id created dynamically 
    # previously in gameEvent 'id update' matches with the id received right now
    # we don't want to add any random player as local player
    if p[0] not in self.Players.keys() and p[0] == player_id:
        # update previously created player object id with the id created dynamically by the server
        self.player.player_id = p[0]
        # updating local player selected colour on the server
        self.Players[p[0]] = self.player
        # just to check if previously created id and newly assigned id match up
        print(self.Players[p[0]].player_id)
    # case2, when a new server side player wants to join, and we want to store a copy of the object locally
    # check if player is not already in the list
    if p[0] not in self.Players.keys():
        # jugaad to fix colour inconsistency
        if p[10] != None:
            self.Players[p[0]] = Player(self, (p[1], p[2]), p[0], False, p[10])
            self.server_players_connected += 1
            self.server_player_alive += 1

    # case3, when player is already in the list and data needs to be received locally from the server
    # check if player is already in the list and that player is not local player, since we do not want to receive
    # data for our local player, only send it
    elif p[0] in self.Players.keys() and p[0] != self.player.player_id:
        self.Players[p[0]].pos = vec(p[1], p[2])
        self.Players[p[0]].alive_status = p[3]
        self.Players[p[0]].sync_img = p[4]
        self.Players[p[0]].sync_img_index = p[5]
        self.Players[p[0]].image = eval(p[4] + p[5])
        self.Players[p[0]].left_img_index = p[6]
        self.Players[p[0]].right_img_index = p[7]
        self.Players[p[0]].up_img_index = p[8]
        self.Players[p[0]].down_img_index = p[9]
        self.Players[p[0]].tasks_completed = p[11]
        self.Players[p[0]].imposter = p[15]
        self.Players[p[0]].voted = p[17]
        self.Players[p[0]].got_votes = p[18]
        self.Players[p[0]].emergency_meeting_img_sync = p[19]
        self.Players[p[0]].emergency_meeting_img_sync_report = p[20]
        self.Players[p[0]].victim_id_report = p[21]
        self.Players[p[0]].got_reported = p[22]

        # Meeting chat line this player is broadcasting.
        # receive_remote drops repeats, so it is safe to
        # feed it the same state on every frame
        if len(p) > protocol.OUT_CHAT_TEXT:
            self.meeting_chat.receive_remote(
                p[0], p[protocol.OUT_CHAT_SEQ],
                p[protocol.OUT_CHAT_AUTHOR],
                p[protocol.OUT_COLOUR],
                p[protocol.OUT_CHAT_TEXT])

        if self.player.player_id == p[14] and self.player.alive_status == True:
            self.player.alive_status = False
            self.player.image = self.player.image_dead
            self.player.sync_img = "self.Players[p[0]].image_dead"
            self.player.sync_img_index = ""
            self.player.pos_corpse.x = self.player.pos.x
            self.player.pos_corpse.y = self.player.pos.y
            self.kill_victim_anim = True


        # If Dead body of Ghost - victim is reported
        if self.player.player_id == p[21] and self.player.alive_status == False and self.player.got_reported == False:
            self.player.got_reported = True
            self.emerg_meeting_report_status = 1
            self.emergency = True
            self.effect_sounds['dead_body_found'].play()
            self.emergency_sync += 1
            self.emergency_img_sync_report = self.player.emergency_meeting_img_sync_report
            self.isdoingTask = False

            # If some player from server reports dead body, meeting timer of
            # 30 seconds will be displayed and decremented on voting screen but it does not
            # decrements on ghost voting screen, the trick is to decrement meeting_timer_event
            # when someone report dead body
            self.time_left_to_end_meeting = 30
            pg.time.set_timer(self.meeting_timer_event, 1000)
            self.timer_start = pygame.time.get_ticks()

        if self.player.victim_id != 0 and self.player.victim_id == p[0] and p[3] == False:
            self.player.victim_id = 0

        if self.player.victim_id_report != 0 and self.player.victim_id_report == p[0] and p[
            22] == True:
            self.player.victim_id_report = 0

        # Night - Turn On/Off the lights
        if self.night_sync < p[12]:
            self.night_sync = p[12]
            if self.night_sync % 2 != 0:
                self.night = True
            elif self.night_sync % 2 == 0:
                self.night = False

                # if some other player from server turn on the light
                # then reset the light timer to 15 and again decrement
                # light_timer_event
                self.time_left_to_light = 15
                pygame.time.set_timer(self.light_timer_event, 1000)
                self.light_bulb_timer_icon_status = True

                # if some other player from server turn on the light
                # then reset the ractor cooldown timer and decrement
                # reactor_timer_cooldown_event
                self.time_left_to_boom_cooldown = 15
                pg.time.set_timer(self.reactor_timer_cooldown_event, 1000)

                self.sabotagecooldown_start = self.sabotagecooldown

        # To Trigger Reactor meltdown Sabotage - Multiplayer Mode
        # If reactor medltdown on and sync with other server players
        # then show meltdown timer
        if self.night_reactor_sync < p[13]:
            self.night_reactor_sync = p[13]
            if self.night_reactor_sync % 2 != 0:
                self.night_reactor = True
                self.sabotagecritical = True
                self.reactor_timer_visible_client_status = True
                pg.time.set_timer(self.reactor_timer_event_client, 1000)
                self.sabotagecriticaltimer_start = pygame.time.get_ticks()

            # If crew mates turn on reactor then show reactor sabotage cooldown
            # timer + sabotage_icon on imposter window
            elif self.night_reactor_sync % 2 == 0:
                self.time_left_to_boom_cooldown = 15
                pg.time.set_timer(self.reactor_timer_cooldown_event, 1000)
                self.night_reactor = False

                #if player turn on the reactor then also reset the light timer
                # and decrement light_timer_event
                self.time_left_to_light = 15
                pygame.time.set_timer(self.light_timer_event, 1000)
                self.light_bulb_timer_icon_status = True

                self.sabotagecooldown_start = self.sabotagecooldown
                self.sabotagecritical = False
                pygame.mixer.Channel(0).stop()

        # Emergency Meeting called from server player
        # connected to the server
        if self.emergency_sync < p[16] and p[19] != None:
            self.emergency_sync = p[16]
            self.emerg_meeting_button_status = 1
            self.emergency = True
            self.effect_sounds['emergency_alarm'].play()
            self.emergency_img_sync = p[19]
            self.isdoingTask = False

            # If some player from server starts meeting then show
            # meeting timer of 30 seconds on each client connected
            # on server and decrement meeting_timer_event
            self.time_left_to_end_meeting = 30
            pg.time.set_timer(self.meeting_timer_event, 1000)

            # If some player from server starts meeting then hide
            # meeting highlighted icon and meeting cooldown timer of 15 sec
            # and when meeting is over decrement meeting_timer_cooldown_event
            # for other client connected to the server
            self.emergency_timer_icon_status = False
            self.time_left_to_end_meeting_cooldown = 15
            self.meeting_timer_cooldown_visible_status = False
            pg.time.set_timer(self.meeting_timer_cooldown_event, 1000)

            if self.invisible_play_count == 1:
                self.player.image = self.player.player_imgs_down[0]
                self.player.sync_img = "self.Players[p[0]].player_imgs_down"
                self.player.sync_img_index = "[0]"
                self.invisible_play_count = 0
            self.timer_start = pygame.time.get_ticks()


        # Report Dead Body - Emergency Meeting called from server player
        # connected to the server
        if self.emergency_sync < p[16] and p[20] != None:
            self.emergency_sync = p[16]
            self.emerg_meeting_report_status = 1
            self.emergency = True
            self.effect_sounds['dead_body_found'].play()
            self.emergency_img_sync_report = p[20]
            self.isdoingTask = False

            # If some player from server reports dead body, meeting timer of
            # 30 seconds will be displayed and decremented on voting screen but it does not
            # decrements on ghost voting screen, the trick is to decrement meeting_timer_event
            # when someone report dead body
            pg.time.set_timer(self.meeting_timer_event, 1000)


            # If some player from server reports dead body then hide
            # meeting highlighted icon and meeting cooldown timer of 15 sec
            # and when meeting is over decrement meeting_timer_cooldown_event
            # for other client connected to the server
            self.emergency_timer_icon_status = False
            self.time_left_to_end_meeting_cooldown = 15
            self.meeting_timer_cooldown_visible_status = False
            pg.time.set_timer(self.meeting_timer_cooldown_event, 1000)

            if self.invisible_play_count == 1:
                self.player.image = self.player.player_imgs_down[0]
                self.player.sync_img = "self.Players[p[0]].player_imgs_down"
                self.player.sync_img_index = "[0]"
                self.invisible_play_count = 0
            self.timer_start = pygame.time.get_ticks()

        # Eject Player
        if self.eject_sync < p[23] and p[24] != None and (
                self.emerg_meeting_report_status == 1 or self.emerg_meeting_button_status == 1) and self.emergency == True:
            self.eject_sync = p[23]
            self.eject = True
            self.eject_img = p[24]
            self.eject_colour = p[10]
            self.timer_start = pygame.time.get_ticks()

        # Votes and Eject
        if self.player.player_colour == p[17] and self.player.alive_status == True and p[0] not in self.voters:
            self.player.got_votes += 1
            self.voters.append(p[0])
        # If player got equal or more than specified votes then eject him
        if self.player.got_votes >= 2 and self.player.alive_status == True and (
                self.emerg_meeting_report_status == 1 or self.emerg_meeting_button_status == 1) and self.emergency == True:
            self.player.alive_status = False
            self.player.got_reported == True
            self.player.image = self.invsible_player_image
            self.eject_colour = self.player.player_colour
            self.eject = True
            self.eject_sync += 1
            self.eject_img = self.player.eject_img
            self.timer_start = pygame.time.get_ticks()

        if p[0] > self.player_highest_id:
            self.player_highest_id = p[0]
        if self.player.player_id > self.player_highest_id and self.player.imposter == False:
            print("yes")
            self.player_highest_id = self.player.player_id
            self.player.imposter = True
        elif self.player.player_id < self.player_highest_id and self.player.imposter == True:
            print("no")
            self.player.imposter = False

