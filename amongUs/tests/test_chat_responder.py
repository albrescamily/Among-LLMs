"""Ciclo 4 - the responder hook, where an LLM plugs in."""

from core.chat import DEMO_LINES, MeetingChat


def record_calls(chat):
    calls = []
    chat.responder = lambda c, kind, message: calls.append((c, kind, message))
    return calls


def test_open_notifies_the_responder(fake_game):
    chat = MeetingChat(fake_game)
    calls = record_calls(chat)

    chat.open()

    assert len(calls) == 1
    who, kind, message = calls[0]
    assert who is chat
    assert kind == "meeting_start"
    assert message is None


def test_send_notifies_the_responder_with_the_message(fake_game):
    chat = MeetingChat(fake_game)
    chat.open()
    calls = record_calls(chat)
    chat.input_text = "ciano"

    sent = chat.send()

    assert [(kind, message) for _, kind, message in calls] == \
        [("player_message", sent)]


def test_responder_replaces_the_demo_chatter(fake_game):
    chat = MeetingChat(fake_game)
    record_calls(chat)

    chat.open()

    assert chat.pending == []           # nenhuma fala enlatada agendada


def test_without_a_responder_the_bots_chatter(fake_game):
    chat = MeetingChat(fake_game)

    chat.open()

    assert chat.pending, "os bots deveriam ter falas agendadas"
    alive = {name for name, _ in chat.alive_bots()}
    for _, message in chat.pending:
        assert message.author in alive
        assert message.text in DEMO_LINES


def test_demo_chatter_is_spread_over_time(fake_game):
    chat = MeetingChat(fake_game)

    chat.open()

    deadlines = sorted(deadline for deadline, _ in chat.pending)
    assert deadlines[0] > chat.opened_at            # ninguÃ©m fala instantaneamente
    assert len(set(deadlines)) == len(deadlines)    # nem todos de uma vez


def test_alive_bots_skips_the_dead_ones(chat):
    crew = chat.alive_bots()

    assert ("madara", "Green") in crew
    assert ("pernilongo", "Yellow") not in crew     # morto no fake_game
    assert len(crew) == 3


def test_responder_can_schedule_the_reply(fake_game):
    chat = MeetingChat(fake_game)

    def responder(c, kind, message):
        if kind == "player_message":
            c.schedule_message("madara", "Green", "para de mentir", 500)

    chat.responder = responder
    chat.open()
    chat.input_text = "eletrica comigo"
    chat.send()

    assert [m.text for _, m in chat.pending] == ["para de mentir"]
