"""Ciclo 1 - the message log and the scheduling queue."""

import pytest

from core.chat import MeetingChat


def test_add_message_appends_and_returns_it(chat):
    message = chat.add_message("madara", "Green", "eu vi ele saindo do vent")

    assert chat.messages == [message]
    assert message.author == "madara"
    assert message.colour == "Green"
    assert message.text == "eu vi ele saindo do vent"


@pytest.mark.parametrize("text", ["", "   ", "\n", "\t "])
def test_blank_messages_are_dropped(chat, text):
    assert chat.add_message("madara", "Green", text) is None
    assert chat.messages == []


def test_whitespace_is_normalised(chat):
    message = chat.add_message("madara", "Green", "  matou   na\nminha  frente ")

    assert message.text == "matou na minha frente"


def test_scheduled_message_waits_for_its_turn(chat, monkeypatch):
    monkeypatch.setattr(chat, "_now", lambda: 1000)
    chat.schedule_message("lalanga", "Orange", "ciano", 500)

    chat.update()
    assert chat.messages == []

    monkeypatch.setattr(chat, "_now", lambda: 1499)
    chat.update()
    assert chat.messages == []

    monkeypatch.setattr(chat, "_now", lambda: 1500)
    chat.update()
    assert [m.text for m in chat.messages] == ["ciano"]


def test_scheduled_messages_arrive_in_deadline_order(chat, monkeypatch):
    monkeypatch.setattr(chat, "_now", lambda: 0)
    chat.schedule_message("a", "Red", "terceira", 300)
    chat.schedule_message("b", "Blue", "primeira", 100)
    chat.schedule_message("c", "Green", "segunda", 200)

    monkeypatch.setattr(chat, "_now", lambda: 1000)
    chat.update()

    assert [m.text for m in chat.messages] == ["primeira", "segunda", "terceira"]


def test_update_is_a_noop_while_closed(chat, monkeypatch):
    monkeypatch.setattr(chat, "_now", lambda: 0)
    chat.schedule_message("madara", "Green", "ciano", 100)
    chat.is_open = False

    monkeypatch.setattr(chat, "_now", lambda: 1000)
    chat.update()

    assert chat.messages == []


def test_open_starts_from_a_clean_log(fake_game, monkeypatch):
    chat = MeetingChat(fake_game)
    chat.responder = lambda *args: None     # keep the demo chatter out of the way
    chat.open()
    chat.add_message("madara", "Green", "reuniao anterior")
    chat.schedule_message("lalanga", "Orange", "pendente", 5000)
    chat.close()

    chat.open()

    assert chat.messages == []
    assert chat.pending == []


def test_close_drops_pending_messages(chat, monkeypatch):
    monkeypatch.setattr(chat, "_now", lambda: 0)
    chat.schedule_message("madara", "Green", "nao devia aparecer", 100)

    chat.close()

    assert chat.pending == []
