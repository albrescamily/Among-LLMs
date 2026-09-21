"""A whole frame runs end to end without raising.

These are crash tests, not correctness tests. They prove that events(), update()
and draw() execute against a real Game; they prove nothing whatsoever about
pixels, and they are not meant to.

That is worth having because of how this file is about to be taken apart. draw()
is 834 lines reading dozens of attributes, and one of its blocks fetches a
`keys` local that six later blocks depend on. The failure mode of a botched
extraction is NameError or AttributeError on a frame -- which, until now,
nothing in the suite would have noticed, because nothing ran a frame.
"""

import pygame as pg


def test_a_freeplay_frame_draws_without_raising(frame_game):
    frame_game.draw()


def test_a_frame_updates_without_raising(frame_game):
    frame_game.update()


def test_a_frame_pumps_events_without_raising(frame_game):
    pg.event.clear()
    frame_game.events()


def test_several_frames_in_a_row_are_fine(frame_game):
    # One frame can pass on a state the next one breaks -- the meeting index
    # and the animation counters all advance between frames.
    for _ in range(3):
        frame_game.events()
        frame_game.update()
        frame_game.draw()


def test_a_frame_draws_while_paused(frame_game):
    # The pause menu draws over the world, so draw() keeps running when update
    # does not. Different branch, worth its own frame.
    frame_game.paused = True

    frame_game.draw()


def test_a_frame_draws_during_a_meeting(frame_game):
    # The meeting flow is the biggest branch in draw() that a quiet frame skips.
    # emergency_img_sync has to be set the way starting a meeting sets it: it
    # is the name of the alert image, and the meeting alert eval()s it.
    frame_game.emerg_meeting_button_status = 1
    frame_game.emergency = True
    frame_game.emergency_img_sync = frame_game.player.emergency_meeting_img_sync

    frame_game.draw()


def test_a_frame_draws_during_a_reported_meeting(frame_game):
    # The other flow, which is a near-copy of the one above and about to stop
    # being one.
    frame_game.emerg_meeting_report_status = 1
    frame_game.emergency = True
    frame_game.emergency_img_sync_report = (
        frame_game.player.emergency_meeting_img_sync_report)

    frame_game.draw()
