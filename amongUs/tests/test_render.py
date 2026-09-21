"""Drawing the world: the map, the sprites on it, and the debug overlay.

The debug overlay is the interesting part. Three of its four blocks used to sit
*inside* the per-sprite loop, so the wall outlines and both grid axes were
redrawn once for every sprite on screen -- same pixels, twenty-five times the
work. Only the per-sprite hit box actually belongs in that loop.
"""

from types import SimpleNamespace

import pygame as pg
import pytest

from core import render
from core.settings import HEIGHT, TILESIZE, WIDTH

EXPECTED_GRID_LINES = len(range(0, WIDTH, TILESIZE)) + len(range(0, HEIGHT, TILESIZE))


class FakeCamera:
    def apply(self, sprite):
        return pg.Rect(0, 0, 10, 10)

    def apply_rect(self, rect):
        return rect


def world(sprites=5, walls=3, debug=False):
    made = [SimpleNamespace(image=pg.Surface((10, 10)),
                            hit_rect=pg.Rect(0, 0, 10, 10),
                            rect=pg.Rect(0, 0, 10, 10)) for _ in range(sprites)]
    return SimpleNamespace(
        screen=SimpleNamespace(blit=lambda *a: None),
        map_img=pg.Surface((10, 10)), map_rect=pg.Rect(0, 0, 10, 10),
        camera=FakeCamera(),
        all_sprites=made,
        walls=[SimpleNamespace(rect=pg.Rect(0, 0, 10, 10)) for _ in range(walls)],
        draw_debug=debug,
        night=False, night_reactor=False,
    )


@pytest.fixture
def drawn(monkeypatch):
    """Counts what got drawn, without a display."""
    calls = SimpleNamespace(lines=[], rects=[], blits=[])
    monkeypatch.setattr(pg.draw, "line", lambda *a, **k: calls.lines.append(a))
    monkeypatch.setattr(pg.draw, "rect", lambda *a, **k: calls.rects.append(a))
    return calls


def test_every_sprite_is_drawn(drawn):
    game = world(sprites=7)
    blits = []
    game.screen.blit = lambda *a: blits.append(a)

    render.draw_world(game)

    assert len(blits) == 7 + 1        # the sprites, plus the map underneath


def test_the_map_goes_down_before_the_sprites(drawn):
    game = world(sprites=3)
    blits = []
    game.screen.blit = lambda *a: blits.append(a)

    render.draw_world(game)

    assert blits[0][0] is game.map_img


def test_nothing_debug_is_drawn_with_the_overlay_off(drawn):
    render.draw_world(world(debug=False))

    assert drawn.lines == []
    assert drawn.rects == []


def test_the_debug_grid_is_drawn_once_per_frame(drawn):
    """It used to be drawn once per sprite.

    Twenty-five sprites meant twenty-five identical grids stacked on top of
    each other -- invisible, and twenty-five times the work.
    """
    render.draw_world(world(sprites=25, debug=True))

    assert len(drawn.lines) == EXPECTED_GRID_LINES


def test_the_wall_outlines_are_drawn_once_per_frame(drawn):
    game = world(sprites=25, walls=4, debug=True)

    render.draw_world(game)

    # 4 walls once each, plus one hit box per sprite -- that one is per-sprite
    # by nature and stays in the loop
    assert len(drawn.rects) == 4 + 25


def test_the_grid_does_not_depend_on_how_many_sprites_exist(drawn):
    render.draw_world(world(sprites=1, debug=True))
    few = len(drawn.lines)

    drawn.lines.clear()
    render.draw_world(world(sprites=40, debug=True))

    assert len(drawn.lines) == few


def test_a_world_with_no_sprites_still_draws_the_debug_overlay(drawn):
    """It used to draw nothing at all, because the overlay lived in the loop."""
    render.draw_world(world(sprites=0, debug=True))

    assert len(drawn.lines) == EXPECTED_GRID_LINES
