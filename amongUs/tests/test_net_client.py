"""Talking to the LAN server.

Real sockets throughout -- socketpair() for the unit tests and a real server for
the integration one. Mocking a socket here would mostly assert that the mock
was called, and the interesting behaviour (a quiet wire, a half-received
pickle, a peer that hung up) is exactly what a mock would not reproduce.
"""

import pickle
import socket

import pytest

from multiplayer.net_client import BUFFERSIZE, DEFAULT_PORT, NetClient


@pytest.fixture
def wire():
    """A NetClient wired to a socket a test can write to and read from."""
    ours, theirs = socket.socketpair()
    client = NetClient("127.0.0.1", sock=ours)
    yield client, theirs
    client.close()
    theirs.close()


def test_a_quiet_wire_yields_nothing(wire):
    client, _peer = wire

    assert client.poll() == []


def test_poll_does_not_block_when_nothing_has_arrived(wire):
    # The game loop calls this every frame; blocking would freeze the game.
    client, _peer = wire

    for _ in range(5):
        assert client.poll() == []


def test_poll_decodes_a_message(wire):
    client, peer = wire
    peer.send(pickle.dumps(['id update', 4242]))

    assert client.poll() == [['id update', 4242]]


def test_garbage_on_the_wire_does_not_raise(wire):
    # Anything can turn up on a socket, and the game loop must survive it.
    client, peer = wire
    peer.send(b"not a pickle at all")

    assert client.poll() == []


def test_a_failed_read_does_not_replay_the_previous_message(wire):
    """The bug this class replaced.

    The old inline loop assigned into `gameEvent` inside a try, so a failed
    read left the *previous* packet bound and applied it a second time -- or,
    on the very first read, left it unbound and raised NameError.
    """
    client, peer = wire
    peer.send(pickle.dumps(['id update', 1]))
    assert client.poll() == [['id update', 1]]

    peer.send(b"garbage")

    assert client.poll() == []


def test_send_puts_a_pickled_packet_on_the_wire(wire):
    client, peer = wire

    client.send(['position update', 7, 100, 200])

    assert pickle.loads(peer.recv(BUFFERSIZE)) == ['position update', 7, 100, 200]


def test_send_survives_a_dead_socket(wire):
    # Someone closing the game must not take the other clients down with them.
    # Closing the underlying socket rather than the client, so send() reaches
    # its error handling instead of short-circuiting on "no socket".
    client, peer = wire
    peer.close()
    client.socket.close()

    assert client.send(['position update', 7]) is False


def test_send_reports_that_it_got_through(wire):
    client, _peer = wire

    assert client.send(['position update', 7]) is True


def test_a_client_with_no_socket_yet_is_inert(wire):
    # connect() has not been called, which is the state after close().
    client, _peer = wire
    client.close()

    assert client.poll() == []
    assert client.send(['position update', 7]) is False


def test_the_default_port_is_the_one_the_server_listens_on():
    from multiplayer import server

    assert DEFAULT_PORT == 4321
    assert server.serve.__defaults__[0] == DEFAULT_PORT


def test_connecting_to_a_real_server_yields_an_id(lan):
    """The one test that exercises connect() against a real listener."""
    _join, pump, port = lan
    client = NetClient("127.0.0.1", port)
    client.connect()
    pump()

    messages = client.poll()
    client.close()

    assert messages, "server sent nothing"
    tag, player_id = messages[0][0], messages[0][1]
    assert tag == 'id update'
    assert isinstance(player_id, int)


def test_a_typed_address_with_stray_whitespace_still_connects(lan):
    # menu.game_input_address feeds whatever the player typed straight in.
    _join, pump, port = lan
    client = NetClient(" 127.0.0.1 \n", port)
    client.connect()
    pump()

    messages = client.poll()
    client.close()

    assert messages and messages[0][0] == 'id update'
