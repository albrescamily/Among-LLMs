"""Drawing the world: the map, the sprites standing on it, the debug overlay."""

import pygame as pg

from core.settings import HEIGHT, LIGHTGREY, TILESIZE, WIDTH, YELLOW


def draw_world(game):
    """The map and everything on it, seen through the camera."""
    game.screen.blit(game.map_img, game.camera.apply_rect(game.map_rect))

    for sprite in game.all_sprites:
        game.screen.blit(sprite.image, game.camera.apply(sprite))
        if game.draw_debug:
            pg.draw.rect(game.screen, YELLOW,
                         game.camera.apply_rect(sprite.hit_rect), 1)
        if game.draw_debug:
            for wall in game.walls:
                pg.draw.rect(game.screen, YELLOW,
                             game.camera.apply_rect(wall.rect), 1)
        if game.draw_debug:
            for x in range(0, WIDTH, TILESIZE):
                pg.draw.line(game.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        if game.draw_debug:
            for y in range(0, HEIGHT, TILESIZE):
                pg.draw.line(game.screen, LIGHTGREY, (0, y), (WIDTH, y))
