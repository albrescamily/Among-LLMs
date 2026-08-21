"""The meeting: alert, discussion, vote, reset.

A meeting starts one of two ways -- somebody presses the emergency button, or
somebody reports a body -- and the two used to run through separate copies of
the same state machine. They differ only in which flag started them, which
splash to show, which sync image to clear at the end, and one asymmetry noted
on MeetingFlow below.

The machine is an index that advances on a timer:

    0   the "emergency meeting" alert splash        (1.5s)
    1   the discussion, which is the chat
    2   the voting window                           (30s)
    >2  over: reset the votes, respawn, start the cooldown
"""

import random
from collections import namedtuple

import pygame
import pygame as pg

from core.settings import MEETING_CHAT_TIME, MEETING_SPLASH_TIME
from core.sprites import vec

# How long the alert splash holds before the discussion opens.
ALERT_MS = 1500

# How long a meeting lasts once the voting window is up.
MEETING_MS = 30000

VOTE_TICKS = ("emerg_vote_red_checkbox_tick_status",
              "emerg_vote_orange_checkbox_tick_status",
              "emerg_vote_green_checkbox_tick_status",
              "emerg_vote_yellow_checkbox_tick_status",
              "emerg_vote_blue_checkbox_tick_status")

MeetingFlow = namedtuple("MeetingFlow", "status alert img_sync clears_task_button")

BUTTON_FLOW = MeetingFlow(
    status="emerg_meeting_button_status",
    alert="display_meeting_alert",
    img_sync="emergency_img_sync",
    # NOTE: only this flow clears the task button. The report flow's copy of
    # this code never did, and nothing suggests that was deliberate -- but
    # changing it belongs in a commit of its own, not in a dedupe.
    clears_task_button=True)

REPORT_FLOW = MeetingFlow(
    status="emerg_meeting_report_status",
    alert="display_meeting_alert_report",
    img_sync="emergency_img_sync_report",
    clears_task_button=False)


def draw_meeting(game, flow):
    """Draw and advance one meeting, if this flow is the one running."""
    if not getattr(game, flow.status):
        return

    if flow.clears_task_button:
        game.task_button_click_status = False

    elapsed = game.timer - game.timer_start

    if game.emergency_meeting_index == 0 and elapsed < ALERT_MS:
        game.screen.blit(game.dim_screen, (0, 0))
        getattr(game, flow.alert)()             # beneath the screen
    elif game.emergency_meeting_index == 1 and elapsed < MEETING_CHAT_TIME:
        game.screen.blit(game.dim_screen, (0, 0))
        if elapsed < MEETING_SPLASH_TIME:
            game.display_chat()                 # "Discuss!" splash
        else:
            # open() is a no-op once the chat is already up
            game.meeting_chat.open(MEETING_CHAT_TIME - MEETING_SPLASH_TIME)
            game.meeting_chat.draw(game.screen)
    elif game.emergency_meeting_index == 2 and elapsed < MEETING_MS:
        game.screen.blit(game.dim_screen, (0, 0))
        game.display_vote()                     # beneath the screen

        # The timer has been running since the meeting was called; the voting
        # window is just where it becomes visible.
        game.meeting_timer_visible_status = True
    else:
        # Between stages. Hide the timer so that calling a second meeting does
        # not show it before its voting window arrives.
        game.meeting_timer_visible_status = False

        # discussion is over, drop the chat before the voting window
        game.meeting_chat.close()

        game.emergency_meeting_index += 1
        game.timer_start = pygame.time.get_ticks()

    if elapsed > MEETING_MS:
        # out of time: reset and hide the meeting timer
        game.time_left_to_end_meeting = 30
        game.meeting_timer_visible_status = False
        pg.time.set_timer(game.meeting_timer_event, 0)

    if game.emergency_meeting_index > 2:
        _end_meeting(game, flow)


def _end_meeting(game, flow):
    """Voting is over: clear the meeting and start its cooldown."""
    game.emergency_meeting_index = 0
    setattr(game, flow.status, 0)
    game.emergency = False

    # the cooldown timer is only shown once the voting window has gone
    game.meeting_timer_cooldown_visible_status = True
    game.meetingcooldown_start = game.meetingcooldown

    game.player.pos = vec(random.choice(game.player_pos))
    if game.player.alive_status == True:
        game.player.image = game.player.player_imgs_down[0]
        game.player.sync_img = "self.Players[p[0]].player_imgs_down"
        game.player.sync_img_index = "[0]"

    setattr(game, flow.img_sync, None)
    game.player.got_votes = 0
    game.player.voted = None
    for tick_status in VOTE_TICKS:
        setattr(game, tick_status, False)
    game.voters = []
