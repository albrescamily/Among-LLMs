"""Applying one player's row out of the server's broadcast.

This is the other half of test_state_packet: that one pins what we put on the
wire, this one pins what we do with what comes back. Both address fields by
bare integer, so both are really pinning the same undocumented layout.

What is deliberately NOT covered here: the emergency-meeting, report-meeting
and eject blocks. Each sets eight to ten attributes, arms a pygame timer and
plays a sound, so a test would mostly restate the code it is testing. They are
verified by hand against two real clients instead -- see the plan's LAN
checklist. The blocks below are the ones where a wrong index is silent.
"""

import pytest

from conftest import (SENTINEL_DEAD, SENTINEL_DOWN, SENTINEL_LEFT,
                      SENTINEL_RIGHT, SENTINEL_UP, FakeRemotePlayer,
                      remote_game)
from multiplayer.world_sync import apply_row


def apply(game, row, player_id=1):
    return apply_row(game, row, player_id)


def known_peer(peer_id=7, **overrides):
    """A game that already knows this peer, so rows take the update path.

    Rows for an unknown id take the join path instead and stop there, which is
    why the tests below that care about anything downstream register the peer
    first.
    """
    game = remote_game(**overrides)
    game.Players[peer_id] = FakeRemotePlayer()
    game.Players[peer_id].player_id = peer_id
    return game


def test_remote_row_fills_every_field_it_owns(quiet_row):
    # The highest-value test here: it pins indexes 1-3, 6-9, 11, 15, 17-22,
    # which nothing else in the suite names and protocol.py does not document.
    game = known_peer()

    apply(game, quiet_row(
        **{"1": 111, "2": 222, "3": True, "6": 61, "7": 71, "8": 81, "9": 91,
           "11": 4, "15": True, "18": 2, "21": 33, "22": True}))

    peer = game.Players[7]
    assert (peer.pos.x, peer.pos.y) == (111, 222)
    assert peer.alive_status is True
    assert peer.left_img_index == 61
    assert peer.right_img_index == 71
    assert peer.up_img_index == 81
    assert peer.down_img_index == 91
    assert peer.tasks_completed == 4
    assert peer.imposter is True
    assert peer.got_votes == 2
    assert peer.victim_id_report == 33
    assert peer.got_reported is True


@pytest.mark.parametrize("sync_img, sync_img_index, expected", [
    ("self.Players[p[0]].player_imgs_left", "[p[6]]", SENTINEL_LEFT),
    ("self.Players[p[0]].player_imgs_right", "[p[7]]", SENTINEL_RIGHT),
    ("self.Players[p[0]].player_imgs_up", "[p[8]]", SENTINEL_UP),
    ("self.Players[p[0]].player_imgs_down", "[p[9]]", SENTINEL_DOWN),
    ("self.Players[p[0]].image_dead", "", SENTINEL_DEAD),
])
def test_the_animation_string_from_get_keys_still_evaluates(
        quiet_row, sync_img, sync_img_index, expected):
    """The peer sends Python source; we eval it to get the sprite.

    sprites.get_keys() builds these strings, and they name `self` and `p` --
    which only resolve because they are locals of the frame doing the eval. If
    the handler is ever moved somewhere those two are called anything else,
    every remote player freezes and only this test says why.
    """
    game = known_peer()

    apply(game, quiet_row(**{"4": sync_img, "5": sync_img_index}))

    assert game.Players[7].image == expected
    assert game.Players[7].sync_img == sync_img


def test_a_new_remote_player_is_created_and_counted(display, quiet_row):
    game = remote_game()

    apply(game, quiet_row(player_id=9))

    assert 9 in game.Players
    assert game.Players[9].player_colour == "Blue"
    assert game.server_players_connected == 1
    assert game.server_player_alive == 1


def test_a_row_with_no_colour_is_ignored(quiet_row):
    # A player that has not picked a colour yet would otherwise be built with
    # colour None and crash on its first sprite lookup.
    game = remote_game()

    apply(game, quiet_row(player_id=9, **{"10": None}))

    assert game.Players == {}
    assert game.server_players_connected == 0


def test_the_local_row_binds_our_own_player(quiet_row):
    # Our own row comes back to us with the id the server assigned; that is how
    # the local player learns its id.
    game = remote_game()

    apply(game, quiet_row(player_id=1), player_id=1)

    assert game.Players[1] is game.player
    assert game.player.player_id == 1


def test_our_own_row_never_overwrites_our_local_state(quiet_row):
    # We send our position, we do not receive it -- otherwise the local player
    # would rubber-band back to whatever the last broadcast said.
    game = remote_game()
    apply(game, quiet_row(player_id=1), player_id=1)

    apply(game, quiet_row(player_id=1, **{"1": 999, "2": 999}), player_id=1)

    assert (game.player.pos.x, game.player.pos.y) == (50, 60)


def test_a_chat_line_reaches_the_meeting_chat(make_chat, quiet_row):
    # Peer 3, because the chat's own player is 7 and it drops its own line
    # coming back off the server.
    chat = make_chat()
    game = known_peer(peer_id=3, meeting_chat=chat)

    apply(game, quiet_row(player_id=3,
                          **{"25": 1, "26": "madara", "27": "atras da nave"}))

    # Author, text and colour each come from a different index; a shift in any
    # one of them shows up here rather than as a mislabelled line in a meeting.
    assert [(m.author, m.text, m.colour) for m in chat.messages] == [
        ("madara", "atras da nave", "Blue")]


def test_a_short_legacy_row_is_tolerated(make_chat, quiet_row):
    # A peer on an older build sends a row with no chat fields on the end.
    chat = make_chat()
    game = known_peer(meeting_chat=chat)
    row = quiet_row()[:25]

    apply(game, row)          # must not IndexError

    assert game.Players[7].tasks_completed == 5


def test_lights_go_out_when_a_peer_reports_an_odd_count(quiet_row):
    game = known_peer()

    apply(game, quiet_row(**{"12": 1}))

    assert game.night is True
    assert game.night_sync == 1


def test_lights_come_back_on_and_reset_the_timer(quiet_row):
    game = known_peer(night_sync=1, night=True)

    apply(game, quiet_row(**{"12": 2}))

    assert game.night is False
    assert game.time_left_to_light == 15
    assert game.light_bulb_timer_icon_status is True


def test_a_stale_light_count_is_ignored(quiet_row):
    # Rows repeat every frame, so an old count must not re-toggle the lights.
    game = known_peer(night_sync=4, night=False)

    apply(game, quiet_row(**{"12": 3}))

    assert game.night_sync == 4
    assert game.night is False


def test_a_reactor_meltdown_starts_the_critical_timer(quiet_row):
    game = known_peer()

    apply(game, quiet_row(**{"13": 1}))

    assert game.night_reactor is True
    assert game.sabotagecritical is True
    assert game.reactor_timer_visible_client_status is True


def test_cancelling_the_reactor_clears_the_critical_state(quiet_row):
    game = known_peer(night_reactor_sync=1, night_reactor=True,
                      sabotagecritical=True)

    apply(game, quiet_row(**{"13": 2}))

    assert game.night_reactor is False
    assert game.sabotagecritical is False
    assert game.time_left_to_boom_cooldown == 15


def test_the_highest_player_id_becomes_the_imposter(quiet_row):
    # With no server-side role assignment, the clients elect by id: we outrank
    # every peer we have seen, so the role is ours.
    game = known_peer(peer_id=3, player_highest_id=0)
    game.player.player_id = 5

    apply(game, quiet_row(player_id=3), player_id=5)

    assert game.player_highest_id == 5
    assert game.player.imposter is True


def test_a_higher_peer_id_takes_the_imposter_role_away(quiet_row):
    # ...and a later-joining peer outranks us, so we hand it back.
    game = known_peer(peer_id=8, player_highest_id=2)
    game.player.player_id = 2
    game.player.imposter = True

    apply(game, quiet_row(player_id=8), player_id=2)

    assert game.player_highest_id == 8
    assert game.player.imposter is False


def test_being_killed_switches_us_to_the_corpse_sprite(quiet_row):
    # p[14] is the killer's victim id; when it is us, we die locally.
    game = known_peer()
    game.player.player_id = 1

    apply(game, quiet_row(**{"14": 1}))

    assert game.player.alive_status is False
    assert game.player.image == "local-dead"
    assert game.player.sync_img == "self.Players[p[0]].image_dead"
    assert (game.player.pos_corpse.x, game.player.pos_corpse.y) == (50, 60)
    assert game.kill_victim_anim is True
