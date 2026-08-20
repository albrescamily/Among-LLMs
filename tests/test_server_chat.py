"""The server has to carry the chat fields through to the other players.

It keeps one snapshot per player and rebroadcasts all of them on every update,
so the chat line has to survive that round trip untouched.
"""

import pickle

import pytest

import protocol
import server


@pytest.fixture
def clean_server():
    server.minionmap.clear()
    del server.outgoing[:]
    yield server
    server.minionmap.clear()
    del server.outgoing[:]


class FakeConnection:
    def __init__(self):
        self.sent = []

    def send(self, data):
        self.sent.append(pickle.loads(data))


def packet(player_id, chat=(0, "", ""), colour="Red"):
    """A client state packet: the tag, the 25 original fields, then the chat."""
    fields = ['position update', player_id, 100, 200, True, "img", "[0]",
              0, 0, 0, 0, colour, 0, 0, 0, 0, False, 0, None, 0, None, None,
              0, False, 0, None]
    return pickle.dumps(fields + list(chat))


def connect(srv, player_id):
    srv.minionmap[player_id] = srv.Minion(player_id)
    conn = FakeConnection()
    srv.outgoing.append(conn)
    return conn


def test_server_stores_the_chat_line(clean_server):
    connect(clean_server, 42)

    clean_server.updateWorld(packet(42, chat=(1, "camily", "ciano")))

    minion = clean_server.minionmap[42]
    assert minion.chat_seq == 1
    assert minion.chat_author == "camily"
    assert minion.chat_text == "ciano"


def test_chat_reaches_the_other_players(clean_server):
    connect(clean_server, 42)
    listener = connect(clean_server, 99)

    clean_server.updateWorld(packet(42, chat=(1, "camily", "ciano")))

    update = listener.sent[-1]
    assert update[0] == 'player locations'
    rows = {row[0]: row for row in update[1:]}
    assert rows[42][protocol.OUT_CHAT_SEQ] == 1
    assert rows[42][protocol.OUT_CHAT_AUTHOR] == "camily"
    assert rows[42][protocol.OUT_CHAT_TEXT] == "ciano"


def test_chat_survives_updates_from_other_players(clean_server):
    connect(clean_server, 42)
    listener = connect(clean_server, 99)
    clean_server.updateWorld(packet(42, chat=(1, "camily", "ciano")))

    # somebody else moves; the line from 42 must still be in the broadcast
    clean_server.updateWorld(packet(99))

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    assert rows[42][protocol.OUT_CHAT_TEXT] == "ciano"


def test_a_new_line_replaces_the_previous_one(clean_server):
    connect(clean_server, 42)
    listener = connect(clean_server, 99)

    clean_server.updateWorld(packet(42, chat=(1, "camily", "primeira")))
    clean_server.updateWorld(packet(42, chat=(2, "camily", "segunda")))

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    assert rows[42][protocol.OUT_CHAT_SEQ] == 2
    assert rows[42][protocol.OUT_CHAT_TEXT] == "segunda"


def test_players_start_with_no_chat(clean_server):
    listener = connect(clean_server, 99)
    connect(clean_server, 42)

    clean_server.updateWorld(packet(42))

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    assert rows[99][protocol.OUT_CHAT_SEQ] == 0
    assert rows[99][protocol.OUT_CHAT_TEXT] == ""


def test_broadcast_row_has_the_expected_width(clean_server):
    connect(clean_server, 42)
    listener = connect(clean_server, 99)

    clean_server.updateWorld(packet(42, chat=(1, "camily", "ciano")))

    row = listener.sent[-1][1]
    assert len(row) == protocol.OUT_CHAT_TEXT + 1
