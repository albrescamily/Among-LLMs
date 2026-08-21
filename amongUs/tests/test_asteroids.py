"""The asteroid shooter.

A whole second game -- its own sprites, its own sounds, its own loop, its own
win condition -- that lived inside Game and ran its simulation from inside
draw(). It touches almost nothing else, which makes it the easiest thing in the
file to lift out and the only part with genuinely pure functions in it.
"""

from collections import defaultdict
from types import SimpleNamespace

import pygame as pg
import pytest

from conftest import Recorder
from minigames import asteroids


class Sprite:
    """Stands in for a loaded image, answering the one question collision asks."""

    def __init__(self, radius):
        self.radius = radius

    def get_rect(self):
        return pg.Rect(0, 0, self.radius * 2, self.radius * 2)


def shooter(**over):
    state = dict(
        screen=SimpleNamespace(blit=lambda *a: None),
        asteroid_image=[Sprite(40)] * 6,
        bullet_image=Sprite(10),
        bullet_state="fire",
        asteroid_kill_count=0,
        num_of_asteroids=6,
        asteroid_posX=[100] * 6, asteroid_posY=[100] * 6,
        asteroid_posY_change=0.5,
        bulletX=100, bulletY=300, bulletY_change=5,
        starship_posX=600, starship_posY=500,
        starship_posX_change=0, starship_posY_change=0,
        starship_image_alignment="middle",
        score_value=30, increment_in_missions=1, missions_done=0,
        paused=False,
        player=SimpleNamespace(imposter=False),
        clear_asteroid_task_available=True,
        clear_asteroid_task_window_status=True,
        clear_asteroid_task_play_count=1,
        isdoingTask=True, task_button_click_status=True,
        asteroid_bg=Recorder(),
        collision_sound=Recorder(),
        bullet_sound=Recorder(),
        effect_sounds=defaultdict(Recorder),
    )
    state.update(over)
    game = SimpleNamespace(**state)
    game.asteroid_bg.fadeout = lambda ms: None
    # the module draws through its own functions now, so the fake needs the
    # surfaces they blit rather than stubs of the old methods
    game.starship_image = game.starship_image2 = game.starship_image3 = Sprite(48)
    game.clear_asteroid_background = Sprite(600)
    game.score_box_img = Sprite(125)
    game.dim_screen = None
    return game


# -- the pure ones ---------------------------------------------------------

def test_a_bullet_on_top_of_an_asteroid_collides():
    game = shooter()

    assert asteroids.is_collision(game, 100, 100, 150, 127, 0) is True


def test_a_bullet_far_away_misses():
    game = shooter()

    assert asteroids.is_collision(game, 100, 100, 900, 900, 0) is False


def test_a_collision_only_counts_while_a_bullet_is_in_flight():
    game = shooter(bullet_state="ready")

    assert asteroids.is_collision(game, 100, 100, 150, 127, 0) is False


def test_a_hit_scores_a_kill():
    game = shooter()

    asteroids.is_collision(game, 100, 100, 150, 127, 0)

    assert game.asteroid_kill_count == 1


@pytest.mark.parametrize("x, y, expected", [
    (-50, 300, (0, 300)),
    (2000, 300, (1185, 300)),
    (600, -50, (600, 0)),
    (600, 900, (600, 550)),
    (600, 300, (600, 300)),
])
def test_the_starship_stays_on_screen(x, y, expected):
    assert asteroids.clamp_starship(x, y) == expected


# -- the simulation --------------------------------------------------------

def test_an_asteroid_falls():
    game = shooter()
    before = game.asteroid_posY[0]

    asteroids.simulate(game)

    assert game.asteroid_posY[0] > before


def test_a_paused_game_freezes_the_asteroids():
    game = shooter(paused=True)
    before = list(game.asteroid_posY)

    asteroids.simulate(game)

    assert game.asteroid_posY == before


def test_an_asteroid_that_falls_off_the_bottom_comes_back_above():
    game = shooter(asteroid_posY=[700] * 6)

    asteroids.simulate(game)

    assert game.asteroid_posY[0] < 0


def test_thirty_kills_ends_the_task():
    game = shooter(asteroid_kill_count=30)

    asteroids.simulate(game)

    assert game.clear_asteroid_task_available is False
    assert game.clear_asteroid_task_window_status is False
    assert game.isdoingTask is False


def test_finishing_the_task_credits_one_mission():
    game = shooter(asteroid_kill_count=30)

    asteroids.simulate(game)

    assert game.missions_done == 1
    assert game.clear_asteroid_task_play_count == 0


def test_the_mission_is_credited_only_once():
    """simulate() runs every frame the window is open, so double-counting is
    the live risk here."""
    game = shooter(asteroid_kill_count=30)

    asteroids.simulate(game)
    game.clear_asteroid_task_available = True
    asteroids.simulate(game)

    assert game.missions_done == 1


def test_an_imposter_gets_no_credit():
    game = shooter(asteroid_kill_count=30, player=SimpleNamespace(imposter=True))

    asteroids.simulate(game)

    assert game.missions_done == 0
    assert game.clear_asteroid_task_play_count == 1


def test_a_spent_bullet_is_reloaded():
    game = shooter(bulletY=-200)

    asteroids.simulate(game)

    assert game.bullet_state == "ready"
    assert game.bulletY == 550


def test_a_bullet_in_flight_travels_upward():
    game = shooter(bulletY=300, bullet_state="fire", asteroid_posX=[9000] * 6)

    asteroids.simulate(game)

    assert game.bulletY < 300


# -- input -----------------------------------------------------------------

def test_firing_launches_a_bullet_from_the_ship():
    game = shooter(bullet_state="ready", starship_posX=444, starship_posY=500)

    asteroids.handle_event(game, pg.event.Event(pg.KEYDOWN, key=pg.K_SPACE))

    assert game.bulletX == 444 + 27
    assert game.bulletY == 500 - 20


def test_you_cannot_fire_while_a_bullet_is_already_out():
    game = shooter(bullet_state="fire", bulletX=100, starship_posX=444)

    asteroids.handle_event(game, pg.event.Event(pg.KEYDOWN, key=pg.K_SPACE))

    assert game.bulletX == 100


def test_a_paused_game_ignores_the_controls():
    game = shooter(paused=True, starship_posX_change=0)

    asteroids.handle_event(game, pg.event.Event(pg.KEYDOWN, key=pg.K_RIGHT))

    assert game.starship_posX_change == 0


def test_a_finished_task_ignores_the_controls():
    game = shooter(clear_asteroid_task_available=False)

    asteroids.handle_event(game, pg.event.Event(pg.KEYDOWN, key=pg.K_RIGHT))

    assert game.starship_posX_change == 0


@pytest.mark.parametrize("key, expected", [(pg.K_LEFT, -10), (pg.K_RIGHT, 10)])
def test_the_arrows_steer(key, expected):
    game = shooter()

    asteroids.handle_event(game, pg.event.Event(pg.KEYDOWN, key=key))

    assert game.starship_posX_change == expected


def test_releasing_an_arrow_stops_the_ship():
    game = shooter(starship_posX_change=10)

    asteroids.handle_event(game, pg.event.Event(pg.KEYUP, key=pg.K_RIGHT))

    assert game.starship_posX_change == 0
