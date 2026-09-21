"""The wait before a round: nobody plays until every expected player has connected.

The server broadcasts ['lobby status', connected, expected, started] each time
someone joins, and started turns True for good once the last one arrives. Until
then a client only draws this waiting screen; it sends no position updates, so
the server has no world to broadcast yet either.
"""

import pygame as pg

from core import display
from core.settings import BLACK, FONT, FPS, HEIGHT, WHITE, WIDTH


def wait_for_start(game, net):
    """Block, drawing a waiting screen, until the server says the round starts.

    Returns the player id the server assigned (0 if it never arrived).
    """
    font = pg.font.Font(FONT, 48)
    player_id = 0
    connected, expected = 0, 0

    started = False
    while not started:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game.quit()

        for message in net.poll():
            if message[0] == 'id update':
                player_id = message[1]
            elif message[0] == 'lobby status':
                connected, expected, started = message[1], message[2], message[3]

        game.screen.fill(BLACK)
        text = "Waiting for players... %d/%d" % (connected, expected) if expected else "Connecting..."
        label = font.render(text, True, WHITE)
        game.screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        display.present()
        game.clock.tick(FPS)

    return player_id
