"""Ciclo 2 - typing, editing and sending."""

import pygame as pg
import pytest

from core.chat import CHAT_MAX_CHARS


def key(chat, key_code, unicode=""):
    return chat.handle_event(pg.event.Event(pg.KEYDOWN, key=key_code,
                                            unicode=unicode))


def type_text(chat, text):
    for char in text:
        key(chat, ord(char) if len(char) == 1 else 0, char)


def test_printable_characters_are_typed(chat):
    type_text(chat, "ciano")

    assert chat.input_text == "ciano"
    assert chat.caret == 5


def test_characters_are_inserted_at_the_caret(chat):
    type_text(chat, "cano")
    chat.caret = 1

    type_text(chat, "i")

    assert chat.input_text == "ciano"
    assert chat.caret == 2


def test_input_stops_at_the_character_limit(chat):
    type_text(chat, "a" * (CHAT_MAX_CHARS + 10))

    assert len(chat.input_text) == CHAT_MAX_CHARS


def test_accented_characters_are_typed(chat):
    # o jogo Ã© jogado em portuguÃªs, acento nÃ£o pode sumir
    type_text(chat, "vocÃª nÃ£o Ã© impostor")

    assert chat.input_text == "vocÃª nÃ£o Ã© impostor"


def test_control_characters_are_not_typed(chat):
    key(chat, pg.K_TAB, "\t")
    key(chat, pg.K_RETURN, "\r")

    assert chat.input_text == ""


def test_backspace_deletes_before_the_caret(chat):
    type_text(chat, "ciano")

    key(chat, pg.K_BACKSPACE)

    assert chat.input_text == "cian"
    assert chat.caret == 4


def test_backspace_at_the_start_does_nothing(chat):
    type_text(chat, "ciano")
    chat.caret = 0

    key(chat, pg.K_BACKSPACE)

    assert chat.input_text == "ciano"


def test_delete_removes_after_the_caret(chat):
    type_text(chat, "ciano")
    chat.caret = 0

    key(chat, pg.K_DELETE)

    assert chat.input_text == "iano"
    assert chat.caret == 0


def test_caret_movement_keys(chat):
    type_text(chat, "ciano")

    key(chat, pg.K_LEFT)
    assert chat.caret == 4

    key(chat, pg.K_RIGHT)
    assert chat.caret == 5

    key(chat, pg.K_RIGHT)               # jÃ¡ no fim, nÃ£o passa
    assert chat.caret == 5

    key(chat, pg.K_HOME)
    assert chat.caret == 0

    key(chat, pg.K_LEFT)                # jÃ¡ no inÃ­cio, nÃ£o passa
    assert chat.caret == 0

    key(chat, pg.K_END)
    assert chat.caret == 5


def test_enter_posts_the_message_and_resets_the_field(chat):
    type_text(chat, "ciano")
    chat.scroll_px = 200

    key(chat, pg.K_RETURN)

    assert [m.text for m in chat.messages] == ["ciano"]
    assert chat.input_text == ""
    assert chat.caret == 0
    assert chat.scroll_px == 0


def test_sent_message_carries_the_local_player_identity(chat):
    type_text(chat, "ciano")
    key(chat, pg.K_RETURN)

    message = chat.messages[0]
    assert message.author == "camily"           # menu.word
    assert message.colour == "Red"              # game.player_colour


def test_player_without_a_name_falls_back_to_the_colour(make_chat):
    chat = make_chat(name="")
    type_text(chat, "ciano")

    key(chat, pg.K_RETURN)

    assert chat.messages[0].author == "Red"


def test_enter_with_only_spaces_posts_nothing(chat):
    type_text(chat, "   ")

    key(chat, pg.K_RETURN)

    assert chat.messages == []
    assert chat.input_text == "   "             # o texto continua lÃ¡


def test_ghost_cannot_type_or_send(make_chat):
    chat = make_chat(alive=False)

    assert chat.can_type is False
    assert key(chat, pg.K_a, "a") is True       # o evento Ã© engolido mesmo assim
    type_text(chat, "ciano")
    key(chat, pg.K_RETURN)

    assert chat.input_text == ""
    assert chat.messages == []


def test_keydown_is_consumed_only_while_open(chat):
    assert key(chat, pg.K_h, "h") is True

    chat.close()

    assert key(chat, pg.K_h, "h") is False
