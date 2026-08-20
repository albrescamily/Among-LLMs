"""Shared test setup.

The game is a pygame app, so the tests need a video/audio driver. Both are set
to SDL's dummy backends before pygame is imported, which lets the whole suite
run headless (no window, no sound card).

A display is still created because pygame refuses to convert_alpha() a surface
without one, and the chat scales the player sprites into avatars.

The game modules live in amongUs/src/ and load their artwork through
paths.asset(), which resolves against amongUs/, so the tests do not need to
run from any particular directory.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
from os import path
from types import SimpleNamespace

import pytest

# the game modules live in src/, not in tests/
sys.path.insert(0, path.join(path.dirname(path.dirname(path.abspath(__file__))), 'src'))

import pygame as pg

from core.settings import WIDTH, HEIGHT


@pytest.fixture(scope="session", autouse=True)
def display():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    yield screen
    pg.quit()


class FakePlayer:
    def __init__(self, alive=True, player_id=7):
        self.alive_status = alive
        self.player_id = player_id


class FakeMenu:
    def __init__(self, word="camily"):
        self.word = word


class FakeBot:
    def __init__(self, bot_name, bot_colour, alive=True):
        self.bot_name = bot_name
        self.bot_colour = bot_colour
        self.alive_status = alive


class FakeGame:
    """Just enough of Game for the chat to work against.

    Building a real Game would load every image, sound and the mixer, which is
    far too heavy (and fragile) for a unit test.
    """

    def __init__(self, alive=True, name="camily", colour="Red", bots=None):
        self.player = FakePlayer(alive)
        self.menu = FakeMenu(name)
        self.player_colour = colour
        self.bots = bots if bots is not None else [
            FakeBot("madara", "Green"),
            FakeBot("lalanga", "Orange"),
            FakeBot("Vmbatalha", "White"),
            FakeBot("pernilongo", "Yellow", alive=False),
        ]


@pytest.fixture
def fake_game():
    return FakeGame()


@pytest.fixture
def make_chat():
    """Builds an open chat over a custom FakeGame."""
    from core.chat import MeetingChat

    def factory(**kwargs):
        instance = MeetingChat(FakeGame(**kwargs))
        instance.open()
        instance.clear()    # drop the demo chatter so tests start from zero
        return instance

    return factory


@pytest.fixture
def chat(make_chat):
    """An open chat, which is the state every interaction test needs."""
    return make_chat()


@pytest.fixture
def lan():
    """A running server plus a pump() that lets it process pending I/O.

    Shared by the chat end-to-end tests and the net client tests, which both
    need a real listener rather than a stand-in.
    """
    import asyncore
    import pickle
    import socket

    from multiplayer import server

    server.minionmap.clear()
    del server.outgoing[:]
    listener = server.MainServer(0)             # port 0 = pick a free one
    port = listener.socket.getsockname()[1]
    clients = []

    def pump(rounds=6):
        for _ in range(rounds):
            asyncore.loop(timeout=0.02, count=1)

    def join():
        sock = socket.create_connection(("127.0.0.1", port), timeout=2)
        sock.settimeout(2)
        clients.append(sock)
        pump()
        tag, player_id = pickle.loads(sock.recv(8192))
        assert tag == 'id update'
        return sock, player_id

    yield join, pump, port

    for sock in clients:
        sock.close()
    listener.close()
    asyncore.close_all()
    server.minionmap.clear()
    del server.outgoing[:]


class Recorder:
    """A sound that remembers it was asked to play, and a timer that isn't one."""

    def __init__(self):
        self.plays = 0
        self.stops = 0

    def play(self, *args, **kwargs):
        self.plays += 1

    def stop(self, *args, **kwargs):
        self.stops += 1


class FakeRemotePlayer:
    """A peer already known to us, for the rows that only update one."""

    def __init__(self, colour="Blue"):
        self.player_id = 7
        self.player_colour = colour
        self.alive_status = True
        self.pos = pg.math.Vector2(0, 0)
        self.sync_img = ""
        self.sync_img_index = ""
        self.image = None
        self.image_dead = SENTINEL_DEAD
        self.left_img_index = self.right_img_index = 0
        self.up_img_index = self.down_img_index = 0
        self.tasks_completed = 0
        self.imposter = False
        self.voted = None
        self.got_votes = 0
        self.emergency_meeting_img_sync = None
        self.emergency_meeting_img_sync_report = None
        self.victim_id_report = 0
        self.got_reported = False
        # the walk cycles the eval'd animation strings index into
        self.player_imgs_left = [SENTINEL_LEFT] * 10
        self.player_imgs_right = [SENTINEL_RIGHT] * 10
        self.player_imgs_up = [SENTINEL_UP] * 10
        self.player_imgs_down = [SENTINEL_DOWN] * 10


SENTINEL_LEFT = "left-frame"
SENTINEL_RIGHT = "right-frame"
SENTINEL_UP = "up-frame"
SENTINEL_DOWN = "down-frame"
SENTINEL_DEAD = "dead-frame"


class ChatRecorder:
    """Stands in for MeetingChat, remembering what the wire handed it.

    Every row carries the sender's last chat line, so the handler calls this on
    essentially every frame -- which makes it the easiest place to catch the
    chat field indexes drifting.
    """

    def __init__(self):
        self.received = []

    def receive_remote(self, player_id, seq, author, colour, text):
        self.received.append((player_id, seq, author, colour, text))


def remote_game(meeting_chat=None, **overrides):
    """Just enough Game for _apply_remote_row to run against.

    It reads about forty attributes off the game and writes about thirty back,
    which is a lot -- but every one of them is a plain value, so a namespace
    does the job and a real Game (every image, every sound) does not.
    """
    local = SimpleNamespace(
        player_id=1, player_colour="Red", alive_status=True,
        pos=pg.math.Vector2(50, 60), pos_corpse=pg.math.Vector2(0, 0),
        image=None, image_dead="local-dead", victim_id=0, victim_id_report=0,
        got_reported=False, got_votes=0, imposter=False,
        player_imgs_down=["local-down"], eject_img="local-eject",
        emergency_meeting_img_sync_report="local-report-img",
    )

    state = dict(
        player=local, Players={},
        meeting_chat=meeting_chat if meeting_chat is not None else ChatRecorder(),
        all_sprites=pg.sprite.LayeredUpdates(), players_server=pg.sprite.Group(),
        server_players_connected=0, server_player_alive=0,
        effect_sounds={name: Recorder() for name in
                       ('dead_body_found', 'emergency_alarm')},
        kill_victim_anim=False, isdoingTask=False, emergency=False,
        emerg_meeting_report_status=0, emerg_meeting_button_status=0,
        emergency_sync=0, emergency_img_sync=None,
        emergency_img_sync_report=None, emergency_timer_icon_status=True,
        night_sync=0, night=False, night_reactor_sync=0, night_reactor=False,
        sabotagecritical=False, sabotagecooldown=0, sabotagecooldown_start=0,
        sabotagecriticaltimer_start=0,
        reactor_timer_visible_client_status=False,
        light_bulb_timer_icon_status=False,
        time_left_to_light=0, time_left_to_boom_cooldown=0,
        time_left_to_end_meeting=0, time_left_to_end_meeting_cooldown=0,
        meeting_timer_cooldown_visible_status=True,
        eject_sync=0, eject=False, eject_img=None, eject_colour=None,
        voters=[], player_highest_id=0, invisible_play_count=0,
        invsible_player_image="invisible", timer_start=0,
        # pygame needs real event ids to hand to set_timer
        meeting_timer_event=pg.USEREVENT + 1,
        meeting_timer_cooldown_event=pg.USEREVENT + 2,
        light_timer_event=pg.USEREVENT + 3,
        reactor_timer_cooldown_event=pg.USEREVENT + 4,
        reactor_timer_event_client=pg.USEREVENT + 5,
    )
    state.update(overrides)
    return SimpleNamespace(**state)


@pytest.fixture
def quiet_row():
    """A broadcast row that updates a peer and triggers nothing else.

    Every conditional block downstream of the field update is switched off, so
    a test can turn exactly one of them back on and know what caused what.
    """
    def factory(player_id=7, **fields):
        row = [player_id,                       # 0  who this row is about
               100, 200,                        # 1,2 position
               True,                            # 3  alive
               "self.Players[p[0]].player_imgs_down", "[0]",   # 4,5 sprite
               1, 2, 3, 4,                      # 6-9 walk-cycle indexes
               "Blue",                          # 10 colour
               5,                               # 11 tasks completed
               0, 0,                            # 12,13 lights / reactor sync
               999,                             # 14 victim id (not us)
               False,                           # 15 imposter
               0,                               # 16 emergency sync
               "not-a-colour",                  # 17 voted
               0,                               # 18 votes received
               None, None,                      # 19,20 meeting images
               999,                             # 21 reported victim (not us)
               False,                           # 22 got reported
               0, None,                         # 23,24 eject sync / image
               0, "", ""]                       # 25-27 chat seq/author/text
        for index, value in fields.items():
            row[int(index)] = value
        return row

    return factory
