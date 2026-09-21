"""Nobody plays until the server says every expected player has connected.

The waiting screen blocks, so the tests feed it a scripted wire: a fake net
whose poll() hands back one batch of messages per frame.
"""

import pygame as pg

from multiplayer import lobby


class ScriptedNet:
    def __init__(self, *batches):
        self.batches = list(batches)
        self.polls = 0

    def poll(self):
        self.polls += 1
        return self.batches.pop(0) if self.batches else []


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pg.time.Clock()

    def quit(self):
        raise SystemExit


def test_it_waits_until_the_server_says_started(display):
    net = ScriptedNet(
        [['id update', 4242]],
        [['lobby status', 1, 3, False]],
        [['lobby status', 2, 3, False]],
        [['lobby status', 3, 3, True]],
    )

    player_id = lobby.wait_for_start(Game(display), net)

    assert player_id == 4242
    assert net.polls == 4   # returned on the message that started the round, not before


def test_it_does_not_start_on_a_partial_lobby(display):
    net = ScriptedNet(*[[['lobby status', 2, 3, False]]] * 5, [['lobby status', 3, 3, True]])

    lobby.wait_for_start(Game(display), net)

    assert net.polls == 6


def test_closing_the_window_while_waiting_quits(display):
    import pytest
    pg.event.post(pg.event.Event(pg.QUIT))

    with pytest.raises(SystemExit):
        lobby.wait_for_start(Game(display), ScriptedNet())
