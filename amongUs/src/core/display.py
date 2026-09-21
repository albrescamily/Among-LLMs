"""The game draws on a fixed WIDTH x HEIGHT canvas; this scales it to a resizable window.

Everything else keeps using canvas coordinates: present() replaces pg.display.flip()
and mouse_pos()/to_canvas() replace pg.mouse.get_pos()/event.pos.
"""
import pygame as pg

from core.settings import HEIGHT, WIDTH

INITIAL_SCALE = 0.75  # the window opens smaller than the canvas so other windows fit beside it

_canvas = None


def create_canvas():
    global _canvas
    if _canvas is None:
        pg.display.set_mode((int(WIDTH * INITIAL_SCALE), int(HEIGHT * INITIAL_SCALE)), pg.RESIZABLE)
        _canvas = pg.Surface((WIDTH, HEIGHT)).convert()
    return _canvas


def _layout():
    window_w, window_h = pg.display.get_surface().get_size()
    scale = min(window_w / WIDTH, window_h / HEIGHT)
    size = (max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale)))
    return scale, size, ((window_w - size[0]) // 2, (window_h - size[1]) // 2)


def present():
    window = pg.display.get_surface()
    _, size, offset = _layout()
    window.fill((0, 0, 0))
    if size == (WIDTH, HEIGHT):
        window.blit(_canvas, offset)
    else:
        window.blit(pg.transform.smoothscale(_canvas, size), offset)
    pg.display.flip()


def to_canvas(pos):
    scale, _, offset = _layout()
    return int((pos[0] - offset[0]) / scale), int((pos[1] - offset[1]) / scale)


def mouse_pos():
    return to_canvas(pg.mouse.get_pos())
