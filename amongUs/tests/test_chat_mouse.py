"""Ciclo 3 - mouse clicks and scrolling."""

import pygame as pg


def click(chat, pos, button=1):
    return chat.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN, pos=pos,
                                            button=button))


def wheel(chat, y):
    return chat.handle_event(pg.event.Event(pg.MOUSEWHEEL, y=y, x=0))


def fill(chat, count=40):
    for i in range(count):
        chat.add_message("madara", "Green", "mensagem numero %d" % i)


def test_click_on_send_posts_the_message(chat):
    chat.input_text = "ciano"
    chat.caret = 5

    assert click(chat, chat.send_rect.center) is True
    assert [m.text for m in chat.messages] == ["ciano"]


def test_click_inside_the_panel_is_swallowed(chat):
    assert click(chat, chat.panel_rect.center) is True
    assert chat.messages == []


def test_click_outside_the_panel_passes_through(chat):
    outside = (chat.panel_rect.left - 20, chat.panel_rect.top - 20)

    assert click(chat, outside) is False


def test_click_is_ignored_while_closed(chat):
    chat.close()

    assert click(chat, chat.send_rect.center) is False


def test_wheel_scrolls_the_log(chat):
    fill(chat)

    assert wheel(chat, 1) is True
    assert chat.scroll_px > 0


def test_wheel_saturates_at_both_ends(chat):
    fill(chat)
    limit = chat.content_height() - chat.list_rect.height
    assert limit > 0                    # o log precisa ser maior que a área

    for _ in range(200):
        wheel(chat, 1)
    assert chat.scroll_px == limit

    for _ in range(200):
        wheel(chat, -1)
    assert chat.scroll_px == 0


def test_short_log_never_scrolls(chat):
    chat.add_message("madara", "Green", "unica mensagem")

    wheel(chat, 1)

    assert chat.scroll_px == 0


def test_legacy_wheel_buttons_scroll_too(chat):
    fill(chat)

    assert click(chat, chat.list_rect.center, button=4) is True
    assert chat.scroll_px > 0

    click(chat, chat.list_rect.center, button=5)
    assert chat.scroll_px == 0


def test_new_message_stays_pinned_to_the_bottom(chat):
    fill(chat)
    before = chat.content_height()

    chat.add_message("lalanga", "Orange", "mensagem nova")

    assert chat.content_height() > before
    assert chat.scroll_px == 0          # continua no fundo do log
