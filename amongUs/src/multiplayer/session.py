"""A multiplayer round: the connection, and the loop that drives it.

Two things happen per frame beyond the shared tick(): whatever the server
has sent is applied to the local world, and the local player's state goes
back out. Everything else here is the ways a round can end.

The bots Game.new() spawned are killed off at the top: this mode's players
all come from the wire.
"""

import random

import pygame
import pygame as pg
from pygame import mixer

from core.audio import stop_all_audio
from core.loop import tick
from core.sprites import Player
from multiplayer import state_sync, world_sync
from multiplayer.net_client import NetClient


def run(game):
    """Play a multiplayer round, returning when it is over."""
    # Game main loop - set game.playing = False to end the game
    # bg music
    global ge
    mixer.music.play(-1)
    mixer.music.set_volume(0.7)

    # remove bots
    for b in game.bots:
        b.kill()
    game.bot_count = 0

    game.killcooldown_start = pygame.time.get_ticks()
    game.sabotagecooldown_start = pygame.time.get_ticks()
    game.sabotagecriticaltimer_start = pygame.time.get_ticks()
    game.ventcooldown_start = pygame.time.get_ticks()
    game.meetingcooldown_start = pygame.time.get_ticks()
    game.timer_start = pygame.time.get_ticks()


    net = NetClient(game.serveraddress).connect()

    # temp var to store dynamically generated id
    player_id = 0

    # dictionary that stores all connected players as objects, including local player. uses player id as key
    game.player = Player(game, random.choice(game.player_pos), 0, True, game.player_colour)
    game.Players = {}


    game.playing = True
    while game.playing:
        tick(game)

        if (game.timer - game.timer_start) > 3000:
            game.imposter_among_us_status = False

        # update player tasks count for server
        game.player.tasks_completed = game.missions_done

        # whatever the server has sent since the last frame
        for gameEvent in net.poll():
            if gameEvent[0] == 'id update':
                # the id the server generated for us
                player_id = gameEvent[1]
            if gameEvent[0] == 'player locations':
                gameEvent.pop(0)        # drop the tag, the rest is rows
                for p in gameEvent:
                    world_sync.apply_row(game, p, player_id)

        # now after receiving data from the server, time to send data to the server
        # update local player object in the list
        game.Players[game.player.player_id] = game.player
        net.send(state_sync.build_state_packet(game, player_id))

        # check for game end condition
        if len(game.Players) > 1:
            # For crew mate
            for p in game.Players.values():
                if p.tasks_completed < 8 and p.imposter == False:
                    break
            else:
                stop_all_audio(game)
                game.effect_sounds["victory_crew"].play()
                game.menu.game_over(game.score_list, '')
                return
            # When imposter is ejecting
            for p in game.Players.values():
                if p.alive_status == False and p.imposter == True and game.emergency == False:
                    stop_all_audio(game)
                    game.effect_sounds["victory_crew"].play()
                    # game.effect_sounds["victory_imposter"].play()
                    game.menu.game_over(game.score_list, '')
                    return

            # When imposter kills all players
            for p in game.Players.values():
                if p.alive_status == True and p.imposter == False:
                    break
            else:
                pass
                if game.emergency == False and game.kill_victim_anim == False:
                    stop_all_audio(game)
                    game.effect_sounds["victory_imposter"].play()
                    game.menu.game_over_imposter(game.score_list, '')
                    return
            # For imposter - Critical Sabotage
            if game.sabotagecritical == True and (
                    game.sabotagecriticaltimer - game.sabotagecriticaltimer_start) > 20000:
                stop_all_audio(game)
                game.effect_sounds["victory_imposter"].play()
                game.menu.game_over_imposter(game.score_list, '')
                return

