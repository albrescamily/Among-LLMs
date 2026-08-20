"""The client packet has to line up with what the server reads.

Everything is addressed by position, so a field in the wrong slot silently
corrupts another one. These tests pin the layout against protocol.py, which is
the same module the server indexes with.
"""

from types import SimpleNamespace

import pytest

import protocol
from game import Game


def stub_game(alive=True, got_reported=False, chat=(0, "", "")):
    player = SimpleNamespace(
        player_id=42, pos=SimpleNamespace(x=100, y=200),
        pos_corpse=SimpleNamespace(x=10, y=20),
        alive_status=alive, sync_img="img", sync_img_index="[0]",
        pos_corpse_img="corpse", pos_corpse_img_index="",
        ghost_img="ghost", ghost_img_index="",
        left_img_index=1, right_img_index=2, up_img_index=3, down_img_index=4,
        player_colour="Green", tasks_completed=5, victim_id=0, imposter=False,
        voted=None, got_votes=0, victim_id_report=0, got_reported=got_reported)
    return SimpleNamespace(
        player=player, night_sync=0, night_reactor_sync=0, emergency_sync=0,
        emergency_img_sync=None, emergency_img_sync_report=None,
        eject_sync=0, eject_img=None,
        meeting_chat=SimpleNamespace(outgoing_fields=lambda: chat))


@pytest.mark.parametrize("alive, got_reported", [
    (True, False),          # jogador vivo
    (False, False),         # corpo no chão
    (False, True),          # fantasma, corpo já reportado
])
def test_chat_travels_in_every_packet_variant(alive, got_reported):
    game = stub_game(alive, got_reported, chat=(3, "camily", "ciano"))

    packet = Game.build_state_packet(game, 42)

    assert packet[protocol.IN_CHAT_SEQ] == 3
    assert packet[protocol.IN_CHAT_AUTHOR] == "camily"
    assert packet[protocol.IN_CHAT_TEXT] == "ciano"
    assert len(packet) == protocol.IN_CHAT_TEXT + 1


@pytest.mark.parametrize("alive, got_reported", [
    (True, False), (False, False), (False, True)])
def test_identity_fields_keep_their_slots(alive, got_reported):
    packet = Game.build_state_packet(stub_game(alive, got_reported), 42)

    assert packet[0] == 'position update'
    assert packet[1] == 42
    assert packet[protocol.IN_COLOUR] == "Green"


def test_living_player_sends_its_own_position():
    packet = Game.build_state_packet(stub_game(alive=True), 42)

    assert (packet[2], packet[3]) == (100, 200)
    assert packet[4] is True


def test_dead_player_sends_the_corpse_position():
    packet = Game.build_state_packet(stub_game(alive=False), 42)

    assert (packet[2], packet[3]) == (10, 20)
    assert packet[4] is False
    assert packet[5] == "corpse"


def test_reported_ghost_switches_to_the_ghost_sprite():
    packet = Game.build_state_packet(stub_game(alive=False, got_reported=True), 42)

    assert packet[5] == "ghost"


def test_packet_matches_the_broadcast_row_offset():
    # the broadcast drops the tag, so every chat index shifts by exactly one
    assert protocol.IN_CHAT_SEQ - protocol.OUT_CHAT_SEQ == 1
    assert protocol.IN_CHAT_AUTHOR - protocol.OUT_CHAT_AUTHOR == 1
    assert protocol.IN_CHAT_TEXT - protocol.OUT_CHAT_TEXT == 1
    assert protocol.IN_COLOUR - protocol.OUT_COLOUR == 1
