"""Ciclo 5 - drawing must never blow up, and must not re-render every frame."""

import pygame as pg

from core.settings import HEIGHT, WIDTH


def canvas():
    return pg.Surface((WIDTH, HEIGHT))


def test_draw_with_an_empty_log(chat):
    chat.draw(canvas())


def test_draw_with_messages(chat):
    chat.add_message("madara", "Green", "matou na minha frente")
    chat.add_message("lalanga", "Orange", "ciano")

    chat.draw(canvas())


def test_draw_wraps_a_long_message(chat):
    short = chat.add_message("madara", "Green", "ciano")
    long = chat.add_message("madara", "Green", "eu vi ele saindo do vent " * 30)

    chat.draw(canvas())

    # o balÃ£o longo quebra em vÃ¡rias linhas, entÃ£o Ã© bem mais alto que o curto
    assert long.height > short.height * 2
    assert long.surface.get_width() == short.surface.get_width()


def test_draw_survives_a_single_giant_word(chat):
    chat.add_message("madara", "Green", "a" * 400)

    chat.draw(canvas())


def test_draw_handles_every_colour(chat):
    for colour in ["Red", "Blue", "Green", "Orange", "Yellow",
                   "Black", "Brown", "Pink", "Purple", "White", None]:
        chat.add_message("bot", colour, "teste")

    chat.draw(canvas())


def test_draw_while_ghost(make_chat):
    chat = make_chat(alive=False)
    chat.add_message("madara", "Green", "ele ta morto", dead=True)

    chat.draw(canvas())


def test_draw_while_closed_paints_nothing(chat):
    chat.close()
    surface = canvas()
    surface.fill((7, 7, 7))

    chat.draw(surface)

    assert surface.get_at(chat.panel_rect.center)[:3] == (7, 7, 7)


def test_bubbles_are_rendered_once(chat):
    message = chat.add_message("madara", "Green", "ciano")
    screen = canvas()

    chat.draw(screen)
    first = message.surface
    chat.draw(screen)

    assert message.surface is first


def test_scrolled_log_still_draws(chat):
    for i in range(40):
        chat.add_message("madara", "Green", "mensagem %d" % i)
    chat._scroll(10_000)

    chat.draw(canvas())

    assert chat.scroll_px > 0


def test_seconds_left_counts_down_and_stops_at_zero(fake_game, monkeypatch):
    from core.chat import MeetingChat

    chat = MeetingChat(fake_game)
    monkeypatch.setattr(chat, "_now", lambda: 0)
    chat.open(20_000)

    assert chat.seconds_left() == 20

    monkeypatch.setattr(chat, "_now", lambda: 19_500)
    assert chat.seconds_left() == 1

    monkeypatch.setattr(chat, "_now", lambda: 20_000)
    assert chat.seconds_left() == 0

    monkeypatch.setattr(chat, "_now", lambda: 99_000)
    assert chat.seconds_left() == 0


def test_untimed_chat_has_no_countdown(chat):
    assert chat.seconds_left() is None
