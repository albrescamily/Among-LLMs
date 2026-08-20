"""Turning the local player into the packet the server reads.

The protocol is a plain list addressed by position, so field order *is* the
contract -- see protocol.py before touching anything here, and note that
tests/test_state_packet.py pins every slot.

A player is in one of three states, and each sends a different sprite and
position: alive (its own position), dead with the body still lying where it was
killed, or dead and already reported, which is when it starts moving around as
a ghost.
"""


def build_state_packet(game, player_id):
    # Our last chat line rides along on every packet until a newer one replaces
    # it, which is what makes late listeners still receive it.
    chat_fields = list(game.meeting_chat.outgoing_fields())

    if game.player.alive_status:
        return ['position update', player_id, game.player.pos.x, game.player.pos.y, game.player.alive_status,
                game.player.sync_img, game.player.sync_img_index, game.player.left_img_index,
                game.player.right_img_index, game.player.up_img_index, game.player.down_img_index,
                game.player.player_colour, game.player.tasks_completed, game.night_sync, game.night_reactor_sync,
                game.player.victim_id, game.player.imposter, game.emergency_sync, game.player.voted,
                game.player.got_votes, game.emergency_img_sync, game.emergency_img_sync_report,
                game.player.victim_id_report, game.player.got_reported, game.eject_sync,
                game.eject_img] + chat_fields

    if game.player.got_reported == False:
        # dead, body still lying where it was killed
        return ['position update', player_id, game.player.pos_corpse.x, game.player.pos_corpse.y,
                game.player.alive_status, game.player.pos_corpse_img, game.player.pos_corpse_img_index, 0, 0, 0,
                0, game.player.player_colour, game.player.tasks_completed, game.night_sync,
                game.night_reactor_sync, 0, game.player.imposter, game.emergency_sync, None, 0, None,
                game.emergency_img_sync_report, 0, game.player.got_reported, game.eject_sync,
                game.eject_img] + chat_fields

    # dead and already reported, so we move around as a ghost
    return ['position update', player_id, game.player.pos_corpse.x, game.player.pos_corpse.y,
            game.player.alive_status, game.player.ghost_img, game.player.ghost_img_index, 0, 0, 0, 0,
            game.player.player_colour, game.player.tasks_completed, game.night_sync, game.night_reactor_sync,
            0, game.player.imposter, game.emergency_sync, None, 0, None, game.emergency_img_sync_report, 0,
            game.player.got_reported, game.eject_sync, game.eject_img] + chat_fields
