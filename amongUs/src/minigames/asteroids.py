"""The asteroid shooter, one of the ship's tasks.

A whole second game -- its own sprites, sounds, controls and win condition --
that used to live inside Game, with its simulation running from inside draw().
It touches very little of the ship: the player (to decide whether a crewmate
earns mission credit), the shared sound bank, and the task flags that open and
close its window.

Shoot thirty asteroids and the task completes. State still lives on the game
object, as everywhere else in this codebase, so the ship's own code can read
the task flags without knowing this module exists.
"""

import math
import random

import pygame as pg
from pygame import mixer

from core.paths import asset
from core.settings import BLACK, CLEAR_ASTEROIDS_IMAGES, FONT, WIDTH

# how many asteroids clear the task
TARGET_KILLS = 30

# the box the starship may fly in
MAX_X = 1185
MAX_Y = 550

# how far a falling asteroid gets before it wraps back above the screen
FALL_LIMIT = 640

STEER_SPEED = 10


def load(game):
    """Load every image and sound this mini-game owns, and seed its state."""
    # Asteroid images loading
    game.asteroid_images = []
    for image in CLEAR_ASTEROIDS_IMAGES:
        game.asteroid_images.append(pg.image.load(image).convert_alpha())

    # Player image
    game.starship_image = pg.image.load(
        asset("Assets/Images/Tasks/Clear Asteroids/starship.png")).convert_alpha()
    game.starship_image = pg.transform.smoothscale(game.starship_image, (96, 96)).convert_alpha()
    game.starship_image2 = pg.image.load(
        asset("Assets/Images/Tasks/Clear Asteroids/starship2.png")).convert_alpha()
    game.starship_image2 = pg.transform.smoothscale(game.starship_image2, (96, 96)).convert_alpha()
    game.starship_image3 = pg.image.load(
        asset("Assets/Images/Tasks/Clear Asteroids/starship3.png")).convert_alpha()
    game.starship_image3 = pg.transform.smoothscale(game.starship_image3, (96, 96)).convert_alpha()
    game.starship_image_alignment = "middle"
    game.starship_posX = 370
    game.starship_posY = 550
    game.starship_posX_change = 0
    game.starship_posY_change = 0

    # Asteroids
    game.asteroid_image = []
    game.asteroid_posX = []
    game.asteroid_posY = []
    game.asteroid_posY_change = 1
    game.num_of_asteroids = 10
    game.increment_in_missions = 1
    game.asteroid_kill_count = 0

    # randomly select asteroid image from game.asteroid_images array
    for i in range(game.num_of_asteroids):
        game.asteroid_image.append(random.choice(game.asteroid_images).convert_alpha())
        game.asteroid_posX.append(random.randint(50, 1200))
        game.asteroid_posY.append(random.randint(-200, -100))

    # Bullet
    game.bullet_image = pg.image.load(
        asset("Assets/Images/Tasks/Clear Asteroids/laser.png")).convert_alpha()
    game.bulletX = 0
    game.bulletY = 550
    game.bulletY_change = 30
    game.bullet_state = "ready"

    # Background
    game.clear_asteroid_background = pg.image.load(
        asset("Assets/Images/Tasks/Clear Asteroids/space3.png")).convert_alpha()

    # Sounds
    game.asteroid_bg = mixer.Sound(asset("Assets/Sounds/Clear Asteroids/AMB_Space.wav"))
    game.bullet_sound = mixer.Sound(asset("Assets/Sounds/Clear Asteroids/fire3.mp3"))
    game.collision_sound = mixer.Sound(
        asset("Assets/Sounds/Clear Asteroids/explosion2.mp3"))

    # Score Board
    game.score_box_img = pg.image.load(
        asset("Assets/Images/Tasks/Clear Asteroids/score_box.png")).convert_alpha()
    game.score_box_img = pg.transform.smoothscale(game.score_box_img, (250, 60)).convert_alpha()
    game.score_value = 30


# -- drawing ---------------------------------------------------------------

def show_score(game, x, y):
    game.screen.blit(game.score_box_img, (x, y))
    font = pg.font.Font(FONT, 20)
    game.screen.blit(
        font.render("Asteroids Left: " + str(game.score_value), True, BLACK),
        (x + 30, y + 10))


def display_starship(game, x, y, alignment):
    image = {"middle": game.starship_image,
             "left": game.starship_image3,
             "right": game.starship_image2}.get(alignment)
    if image is not None:
        game.screen.blit(image, (game.starship_posX, game.starship_posY))


def display_window(game):
    game.screen.blit(game.clear_asteroid_background, (0, 0))


def display_asteroid(game, x, y, index):
    game.screen.blit(game.asteroid_image[index], (x, y))


def fire_bullet(game, x, y):
    game.bullet_state = "fire"
    game.screen.blit(game.bullet_image, (x + 15, y + 10))


# -- pure helpers ----------------------------------------------------------

def clamp_starship(x, y):
    """Keep the ship inside the window."""
    return (min(max(x, 0), MAX_X), min(max(y, 0), MAX_Y))


def is_collision(game, asteroid_x, asteroid_y, bullet_x, bullet_y, index):
    """Did this bullet hit this asteroid? Scores the kill if so.

    The offsets are fudge: +50 horizontally and +27 vertically, to line the
    hit box up with where the sprites actually look like they are.
    """
    asteroid_radius = game.asteroid_image[index].get_rect().center[0]
    bullet_radius = game.bullet_image.get_rect().center[0]
    touching = asteroid_radius + bullet_radius

    distance = math.sqrt(math.pow(asteroid_x - bullet_x + 50, 2)
                         + math.pow(asteroid_y - bullet_y + 27, 2))

    if distance <= touching and game.bullet_state == "fire":
        game.asteroid_kill_count += 1
        return True
    return False


# -- the frame -------------------------------------------------------------

def simulate(game):
    """Advance the shooter by one frame and draw it."""
    game.starship_posX += game.starship_posX_change
    game.starship_posY += game.starship_posY_change
    game.starship_posX, game.starship_posY = clamp_starship(
        game.starship_posX, game.starship_posY)

    for index in range(game.num_of_asteroids):
        if game.asteroid_kill_count == TARGET_KILLS:
            _complete(game)
            break

        if not game.paused:
            game.asteroid_posY[index] += game.asteroid_posY_change
            if game.asteroid_posY[index] >= FALL_LIMIT:
                _respawn(game, index)

        if is_collision(game, game.asteroid_posX[index], game.asteroid_posY[index],
                        game.bulletX, game.bulletY, index):
            game.collision_sound.play()
            game.bulletY = MAX_Y
            game.bullet_state = "ready"
            game.score_value -= 1
            _respawn(game, index)
        display_asteroid(game, game.asteroid_posX[index], game.asteroid_posY[index],
                              index)

    if game.bulletY <= -100:
        game.bulletY = MAX_Y
        game.bullet_state = "ready"

    if game.bullet_state == "fire":
        fire_bullet(game, game.bulletX, game.bulletY)
        game.bulletY -= game.bulletY_change

    display_starship(game, game.starship_posX, game.starship_posY,
                          game.starship_image_alignment)
    show_score(game, WIDTH / 2.5, 10)


def _respawn(game, index):
    """Put an asteroid back above the top of the screen."""
    game.asteroid_posX[index] = random.randint(50, 1200)
    game.asteroid_posY[index] = random.randint(-200, -150)


def _complete(game):
    """Thirty down: close the task and credit it, once."""
    game.effect_sounds['task_completed'].play()
    game.clear_asteroid_task_available = False
    game.asteroid_bg.fadeout(500)
    game.clear_asteroid_task_window_status = False
    game.isdoingTask = False

    # the imposter can sit through the mini-game but earns nothing for it
    if not game.player.imposter:
        game.clear_asteroid_task_play_count -= 1
        # increment_in_missions is a one-shot guard: simulate() runs every
        # frame the window is open, so without it the credit would repeat
        if game.increment_in_missions == 1:
            game.missions_done += 1
        game.increment_in_missions -= 1


def draw_window(game):
    """The whole mini-game, if its window is open."""
    if not (game.clear_asteroid_task_window_status and game.isdoingTask):
        return
    game.task_button_click_status = False
    game.screen.blit(game.dim_screen, (0, 0))
    display_window(game)
    if game.clear_asteroid_task_available:
        simulate(game)


def handle_event(game, event):
    """Steer and shoot."""
    if not game.clear_asteroid_task_available or game.paused:
        return False

    if event.type == pg.KEYDOWN:
        if event.key == pg.K_LEFT:
            game.starship_posX_change = -STEER_SPEED
        if event.key == pg.K_RIGHT:
            game.starship_posX_change = STEER_SPEED
        if event.key == pg.K_SPACE and game.bullet_state == "ready":
            game.bullet_sound.play()
            game.bulletX = game.starship_posX + 27
            game.bulletY = game.starship_posY - 20
            fire_bullet(game, game.bulletX, game.bulletY)
        return True

    if event.type == pg.KEYUP:
        if event.key in (pg.K_LEFT, pg.K_RIGHT):
            game.starship_posX_change = 0
        if event.key in (pg.K_UP, pg.K_DOWN):
            game.starship_posY_change = 0
        return True

    return False
