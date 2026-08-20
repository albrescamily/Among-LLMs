"""End to end: a line typed by one player reaches another player's chat.

Runs the real server over a real socket on localhost, with two real client
connections, and feeds what comes back into a real MeetingChat.
"""

import asyncore
import io
import pickle
import socket

import pytest

from multiplayer import protocol
from multiplayer import server


def state(player_id, colour="Red", chat=(0, "", "")):
    return pickle.dumps(['position update', player_id, 100, 200, True,
                         "img", "[0]", 0, 0, 0, 0, colour, 0, 0, 0, 0, False,
                         0, None, 0, None, None, 0, False, 0, None] + list(chat))


def rows_from(sock):
    """Every broadcast waiting on the socket, flattened to {player_id: row}.

    TCP may deliver several broadcasts in one read, so the buffer is unpickled
    object by object and the newest row per player wins.
    """
    buffer = io.BytesIO(sock.recv(65536))
    rows = {}
    while True:
        try:
            update = pickle.load(buffer)
        except EOFError:
            break
        assert update[0] == 'player locations'
        for row in update[1:]:
            rows[row[0]] = row
    return rows


def feed(chat, rows, skip_id):
    for player_id, row in rows.items():
        if player_id == skip_id:
            continue
        chat.receive_remote(player_id, row[protocol.OUT_CHAT_SEQ],
                            row[protocol.OUT_CHAT_AUTHOR],
                            row[protocol.OUT_COLOUR],
                            row[protocol.OUT_CHAT_TEXT])


def test_message_typed_by_one_player_shows_up_for_the_other(lan, make_chat):
    join, pump, _port = lan
    alice, alice_id = join()
    bob, bob_id = join()

    chat = make_chat()
    chat.game.player.player_id = bob_id

    # alice types and her state goes out with the chat fields attached
    alice.send(state(alice_id, colour="Green", chat=(1, "alice", "eu vi ele no vent")))
    pump()

    feed(chat, rows_from(bob), skip_id=bob_id)

    assert [(m.author, m.colour, m.text) for m in chat.messages] == \
        [("alice", "Green", "eu vi ele no vent")]


def test_repeated_state_packets_do_not_duplicate_the_line(lan, make_chat):
    join, pump, _port = lan
    alice, alice_id = join()
    bob, bob_id = join()

    chat = make_chat()
    chat.game.player.player_id = bob_id

    # the client resends its whole state every frame
    for _ in range(5):
        alice.send(state(alice_id, chat=(1, "alice", "skip")))
        pump()
        feed(chat, rows_from(bob), skip_id=bob_id)

    assert len(chat.messages) == 1


def test_both_players_see_each_other(lan, make_chat):
    join, pump, _port = lan
    alice, alice_id = join()
    bob, bob_id = join()

    alice_chat = make_chat()
    alice_chat.game.player.player_id = alice_id

    bob_chat = make_chat()
    bob_chat.game.player.player_id = bob_id

    alice.send(state(alice_id, colour="Green", chat=(1, "alice", "onde tu tava?")))
    pump()
    bob.send(state(bob_id, colour="Blue", chat=(1, "bob", "eletrica")))
    pump()

    feed(bob_chat, rows_from(bob), skip_id=bob_id)
    feed(alice_chat, rows_from(alice), skip_id=alice_id)

    assert [m.text for m in bob_chat.messages] == ["onde tu tava?"]
    assert [m.text for m in alice_chat.messages] == ["eletrica"]


def test_player_does_not_see_their_own_line_twice(lan, make_chat):
    join, pump, _port = lan
    alice, alice_id = join()

    chat = make_chat()
    chat.game.player.player_id = alice_id
    chat.add_message("alice", "Green", "ja escrevi isso")     # local echo

    alice.send(state(alice_id, colour="Green", chat=(1, "alice", "ja escrevi isso")))
    pump()

    for player_id, row in rows_from(alice).items():
        chat.receive_remote(player_id, row[protocol.OUT_CHAT_SEQ],
                            row[protocol.OUT_CHAT_AUTHOR],
                            row[protocol.OUT_COLOUR],
                            row[protocol.OUT_CHAT_TEXT])

    assert len(chat.messages) == 1
