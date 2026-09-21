"""The meeting: alert, discussion, vote, reset.

There are two ways a meeting starts -- somebody presses the emergency button,
or somebody reports a body -- and draw() used to run each through its own copy
of the same 66-line state machine. The copies differed in four places, and one
of those differences looks accidental (see the task-button test at the bottom).

The machine itself is an index that advances on a timer:

    0  the "emergency meeting" alert splash
    1  the discussion, which is the chat
    2  the voting window
    >2 over: reset everything and start the cooldown

The tests drive it through a SimpleNamespace. The alert frame is reached by
name through getattr, so a recorder stands in for the blitter and none of this
needs a display.
"""

from types import SimpleNamespace

import pygame as pg
import pytest

from conftest import Recorder
from core.meeting import BUTTON_FLOW, MEETING_MS, REPORT_FLOW, draw_meeting

FLOWS = [BUTTON_FLOW, REPORT_FLOW]
FLOW_IDS = ["button", "report"]


class ChatSpy:
    def __init__(self):
        self.opened = 0
        self.closed = 0

    def open(self, *args):
        self.opened += 1

    def close(self):
        self.closed += 1

    def draw(self, surface):
        pass


def meeting_game(flow, index=0, elapsed=0, **over):
    """A game mid-meeting, `elapsed` ms into stage `index`."""
    player = SimpleNamespace(
        alive_status=True, got_votes=3, voted="Red",
        pos=pg.math.Vector2(0, 0),
        player_imgs_down=["down-0"], image=None,
        sync_img="", sync_img_index="")
    state = dict(
        screen=SimpleNamespace(blit=lambda *a: None),
        dim_screen=None,
        timer=elapsed, timer_start=0,
        emergency_meeting_index=index,
        emergency=True,
        meeting_chat=ChatSpy(),
        meeting_timer_visible_status=False,
        meeting_timer_cooldown_visible_status=False,
        meeting_timer_event=pg.USEREVENT + 4,
        time_left_to_end_meeting=0,
        meetingcooldown=1234, meetingcooldown_start=0,
        player=player, player_pos=[(10, 20)],
        voters=["Red", "Blue"],
        task_button_click_status=True,
        emerg_vote_red_checkbox_tick_status=True,
        emerg_vote_orange_checkbox_tick_status=True,
        emerg_vote_green_checkbox_tick_status=True,
        emerg_vote_yellow_checkbox_tick_status=True,
        emerg_vote_blue_checkbox_tick_status=True,
        display_chat=Recorder().play,
        display_vote=Recorder().play,
        display_meeting_alert=Recorder().play,
        display_meeting_alert_report=Recorder().play,
        emerg_meeting_button_status=0,
        emerg_meeting_report_status=0,
        emergency_img_sync="an-image-name",
        emergency_img_sync_report="a-report-image-name",
    )
    state.update(over)
    game = SimpleNamespace(**state)
    setattr(game, flow.status, 1)
    return game


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_a_quiet_flow_draws_nothing(flow):
    game = meeting_game(flow)
    setattr(game, flow.status, 0)

    draw_meeting(game, flow)

    assert game.emergency_meeting_index == 0


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_the_index_advances_once_a_stage_has_run_its_time(flow):
    # Past the alert window, so the else branch fires and moves us on.
    game = meeting_game(flow, index=0, elapsed=2000)

    draw_meeting(game, flow)

    assert game.emergency_meeting_index == 1


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_the_discussion_closes_before_the_vote_opens(flow):
    game = meeting_game(flow, index=1, elapsed=MEETING_MS + 1)

    draw_meeting(game, flow)

    assert game.meeting_chat.closed == 1
    assert game.emergency_meeting_index == 2


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_the_vote_window_shows_the_meeting_timer(flow):
    game = meeting_game(flow, index=2, elapsed=100)

    draw_meeting(game, flow)

    assert game.meeting_timer_visible_status is True


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_a_meeting_that_runs_out_of_time_hides_its_timer(flow):
    game = meeting_game(flow, index=2, elapsed=MEETING_MS + 1)

    draw_meeting(game, flow)

    assert game.time_left_to_end_meeting == 30
    assert game.meeting_timer_visible_status is False


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_closing_the_meeting_clears_its_own_sync_image(flow):
    """The cross-wiring test.

    Each flow owns one of two nearly identically named attributes. A single
    character wrong in the parameterised version -- emergency_img_sync where
    emergency_img_sync_report belongs -- is invisible in review and would leave
    a stale alert image on the wire.
    """
    game = meeting_game(flow, index=3)
    other = (REPORT_FLOW if flow is BUTTON_FLOW else BUTTON_FLOW)

    draw_meeting(game, flow)

    assert getattr(game, flow.img_sync) is None
    assert getattr(game, other.img_sync) is not None


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_closing_the_meeting_ends_it(flow):
    game = meeting_game(flow, index=3)

    draw_meeting(game, flow)

    assert game.emergency_meeting_index == 0
    assert getattr(game, flow.status) == 0
    assert game.emergency is False


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_closing_arms_the_meeting_cooldown(flow):
    game = meeting_game(flow, index=3)

    draw_meeting(game, flow)

    assert game.meeting_timer_cooldown_visible_status is True
    assert game.meetingcooldown_start == game.meetingcooldown


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_closing_clears_every_vote(flow):
    game = meeting_game(flow, index=3)

    draw_meeting(game, flow)

    assert game.voters == []
    assert game.player.got_votes == 0
    assert game.player.voted is None
    for colour in ("red", "orange", "green", "yellow", "blue"):
        assert getattr(game, f"emerg_vote_{colour}_checkbox_tick_status") is False


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_closing_sends_the_player_back_to_a_spawn(flow):
    game = meeting_game(flow, index=3)

    draw_meeting(game, flow)

    assert (game.player.pos.x, game.player.pos.y) == (10, 20)


@pytest.mark.parametrize("flow", FLOWS, ids=FLOW_IDS)
def test_a_ghost_keeps_its_sprite_when_the_meeting_ends(flow):
    # Only the living are put back into the walk cycle.
    game = meeting_game(flow, index=3)
    game.player.alive_status = False

    draw_meeting(game, flow)

    assert game.player.image is None


def test_only_the_button_flow_clears_the_task_button():
    """Asymmetry between the two copies, preserved deliberately.

    The emergency-button block cleared task_button_click_status and the report
    block did not. Nothing suggests that was intended, but changing it here
    would smuggle a behaviour change into a dedupe. Named so it is a decision
    rather than an accident.
    """
    by_button = meeting_game(BUTTON_FLOW)
    by_report = meeting_game(REPORT_FLOW)

    draw_meeting(by_button, BUTTON_FLOW)
    draw_meeting(by_report, REPORT_FLOW)

    assert by_button.task_button_click_status is False
    assert by_report.task_button_click_status is True
