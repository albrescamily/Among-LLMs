"""Multiplayer: what the local chat puts on the wire and takes off it.

The server rebroadcasts the whole state of every player on every frame, so a
chat message is sent over and over until the next one replaces it. A sequence
number per player is what turns that repetition into "one message, once".
"""

import pytest


def send_as_local(chat, text):
    chat.input_text = text
    chat.caret = len(text)
    return chat.send()


def test_nothing_to_broadcast_before_talking(chat):
    seq, author, text = chat.outgoing_fields()

    assert seq == 0
    assert text == ""


def test_sending_bumps_the_sequence_and_carries_the_message(chat):
    send_as_local(chat, "ciano")

    seq, author, text = chat.outgoing_fields()

    assert seq == 1
    assert author == "camily"
    assert text == "ciano"


def test_each_message_gets_its_own_sequence(chat):
    send_as_local(chat, "primeira")
    send_as_local(chat, "segunda")

    seq, _, text = chat.outgoing_fields()

    assert seq == 2
    assert text == "segunda"


def test_remote_message_lands_in_the_log(chat):
    chat.receive_remote(99, 1, "madara", "Green", "matou na minha frente")

    assert [(m.author, m.colour, m.text) for m in chat.messages] == \
        [("madara", "Green", "matou na minha frente")]


def test_repeated_broadcast_is_delivered_once(chat):
    for _ in range(30):        # the server resends the same state every frame
        chat.receive_remote(99, 1, "madara", "Green", "ciano")

    assert len(chat.messages) == 1


def test_next_message_from_the_same_player_gets_through(chat):
    chat.receive_remote(99, 1, "madara", "Green", "primeira")
    chat.receive_remote(99, 2, "madara", "Green", "segunda")

    assert [m.text for m in chat.messages] == ["primeira", "segunda"]


def test_stale_sequence_is_ignored(chat):
    chat.receive_remote(99, 2, "madara", "Green", "atual")
    chat.receive_remote(99, 1, "madara", "Green", "atrasada")

    assert [m.text for m in chat.messages] == ["atual"]


def test_players_have_independent_sequences(chat):
    chat.receive_remote(99, 1, "madara", "Green", "do madara")
    chat.receive_remote(50, 1, "lalanga", "Orange", "do lalanga")

    assert [m.text for m in chat.messages] == ["do madara", "do lalanga"]


def test_own_message_is_not_echoed_back(chat):
    send_as_local(chat, "ciano")
    seq, author, text = chat.outgoing_fields()

    # the server broadcasts our own state back to us
    chat.receive_remote(chat.game.player.player_id, seq, author, "Red", text)

    assert len(chat.messages) == 1


@pytest.mark.parametrize("seq, text", [(0, "ciano"), (1, ""), (1, "   ")])
def test_empty_broadcasts_are_ignored(chat, seq, text):
    chat.receive_remote(99, seq, "madara", "Green", text)

    assert chat.messages == []


def test_messages_arriving_while_closed_are_not_lost(chat):
    chat.close()

    chat.receive_remote(99, 1, "madara", "Green", "chegou cedo demais")
    assert chat.messages == []

    # the sender keeps broadcasting the same state, so it lands once we open
    chat.open()
    chat.receive_remote(99, 1, "madara", "Green", "chegou cedo demais")

    assert [m.text for m in chat.messages] == ["chegou cedo demais"]


def test_a_new_meeting_starts_from_a_clean_slate(chat):
    chat.receive_remote(99, 1, "madara", "Green", "reuniao passada")
    chat.close()

    chat.open()
    chat.clear()
    chat.receive_remote(99, 1, "madara", "Green", "reuniao passada")

    assert [m.text for m in chat.messages] == ["reuniao passada"]


def test_local_sequence_survives_a_new_meeting(chat):
    # the server has no idea a meeting ended, so the counter must keep growing
    send_as_local(chat, "primeira")
    chat.close()
    chat.open()
    send_as_local(chat, "segunda")

    seq, _, _ = chat.outgoing_fields()
    assert seq == 2
