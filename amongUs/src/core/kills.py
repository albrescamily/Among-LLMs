"""The imposter killing a bot.

update() used to state this rule ten times, once per bot, with the index
changed each time. The blocks tested `hit.type == 'botN'` and then acted on
`game.botN` -- but those are the same object, because new() builds each bot
from the single tmx object of that name (see tests/test_bot_identity.py). So
the rule only ever needed the sprite the collision already handed it.
"""

import pygame
import pygame as pg

# How long the imposter waits between kills.
COOLDOWN_MS = 15000

BOT_TYPES = frozenset("bot%d" % n for n in range(1, 11))


def bot_kill(game, bot, keys):
    """Try to kill one bot. True if it died."""
    if not keys[pg.K_RETURN]:
        return False
    if bot.play_kill_count >= 1 or not bot.alive_status:
        return False
    if game.invisible_play_count != 0 or not game.player.imposter:
        return False

    if (game.killcooldown - game.killcooldown_start) <= COOLDOWN_MS:
        game.kill_timer_icon_status = False
        game.effect_sounds['imposter_kill_cooldown_sound'].play()
        return False

    game.effect_sounds['imposter_kill_sound'].play()
    bot.image = bot.dead_player_img
    bot.alive_status = False
    bot.play_kill_count += 1
    game.bot_killed += 1
    game.bot_count -= 1
    game.kill_timer_icon_status = True

    # Show the cooldown counting back down from 15, a second at a time.
    game.time_left_to_kill = 15
    pygame.time.set_timer(game.kill_timer_event, 1000)
    game.killcooldown_start = game.killcooldown
    return True


def apply_bot_kills(game, keys):
    """Offer every bot the player is standing on to the kill rule."""
    for hit in pg.sprite.spritecollide(game.player, game.bots, False):
        if hit.type in BOT_TYPES:
            bot_kill(game, hit, keys)
