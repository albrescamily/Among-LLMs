"""The single-player round: one human imposter against ten bots.

The bots are already on the map by the time this runs -- Game.new() spawns
them for both modes -- so all this does is take the local player's colour
out of the bot roster and start the frame loop.
"""

import random

import pygame
import pygame as pg
from pygame import mixer

from core.audio import stop_all_audio
from core.loop import tick
from core.sprites import Player


def start_round(game):
    """Everything that has to happen before the first frame.

    Split out from run() so the tests can reach the same starting state the
    game does, rather than approximating it.
    """
    # bg music
    mixer.music.play(-1)
    mixer.music.set_volume(0.7)

    game.player = Player(game, random.choice(game.player_pos), 0, True, game.player_colour)

    game.playing = True
    game.player.imposter = True

    for b in game.bots:
        if b.bot_colour == game.player_colour:
            b.kill()
            break

    game.imposter_among_us_status = False

    game.timer_start = pygame.time.get_ticks()
    game.killcooldown_start = pygame.time.get_ticks()
    game.sabotagecooldown_start = pygame.time.get_ticks()
    game.sabotagecriticaltimer_start = pygame.time.get_ticks()
    game.ventcooldown_start = pygame.time.get_ticks()
    game.meetingcooldown_start = pygame.time.get_ticks()
    game.start_ticks = pg.time.get_ticks()
    game.time_left = 20


def run(game):
    """Play a freeplay round, returning when it is won, lost or left."""
    # Game main loop - set game.playing = False to end the game
    start_round(game)

    while game.playing:
        tick(game)
        game.seconds = (pg.time.get_ticks() - game.start_ticks) / 1000

        # If missions are completed then win or loss display
        # For crew mate
        if game.missions_done == 8:
            stop_all_audio(game)
            game.effect_sounds["victory_crew"].play()
            game.menu.game_over(game.score_list, '')
            return
        # For imposter
        # if imposter kills all the bots or reactor meltdown sabotage timer equals to 0 then imposter wins
        elif game.bot_count == 0 or (game.sabotagecritical == True and (game.sabotagecriticaltimer - game.sabotagecriticaltimer_start) > 20000):
            stop_all_audio(game)
            game.effect_sounds["victory_imposter"].play()
            game.menu.game_over_imposter(game.score_list, '')
            return
        elif game.game_left:
            stop_all_audio(game)
            game.effect_sounds["game_left"].play()
            return

