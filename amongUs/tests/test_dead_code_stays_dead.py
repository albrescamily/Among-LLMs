"""Code that was removed does not come back.

game.py accumulated attributes that are assigned and never read, and methods
that are never called. Deleting them is easy; the value is in recording *what*
was deleted, so a later refactor that reintroduces one of these names has to do
it deliberately.

Each name below was verified write-only (or call-free) across src/ and tests/
before removal. Two candidates that look dead are deliberately absent:

    font_folder              read by test_game_boots.py
    pause_quit_button_status read by core/menu.py in three branches -- but its
                             only setter is commented out at the mouse handler,
                             so those branches are unreachable. That is a bug,
                             not dead code. See test_the_pause_quit_path_is_dead.
"""

import ast
import re
from os import path, walk

import pytest

ROOT = path.dirname(path.dirname(path.abspath(__file__)))
SRC = path.join(ROOT, 'src')
GAME_PY = path.join(SRC, 'game.py')

REMOVED_ATTRIBUTES = [
    "admin_mini_map", "admin_mini_map_img",
    "walls_img_folder", "player_img_folder",
    "sound_playing", "skip_meeting_button_status",
    "open_cafe_comp_imposter_select_status",
    "divert_power_to_reactor_livers_btn_sel_count",
    "view_admin_security_monitor_close_btn_status",
    "view_security_monitor_close_btn_status",
    "reboot_wifi_close_btn_status", "fuel_engine_sound_play_count2",
    "screen_width", "screen_height",
    "total_num_of_asteroids", "asteroid_mov", "asteroid_posX_change",
    "bgX", "bgY", "light_rect_reactor", "name_block",
    "sabotage_timer_visible_status",
]

REMOVED_METHODS = [
    "display_deadbody_alert",        # body was `pass`
    "draw_health",                   # drew a white rect onto player.image
    "draw_grid",                     # sole call site was commented out
    "draw_missions_box_imposter",
    "turn_on_the_lights",            # core/tasks.py; call site commented out
]


def _sources():
    for base in (SRC, path.join(ROOT, 'tests')):
        for dirpath, _dirs, files in walk(base):
            if "__pycache__" in dirpath:
                continue
            for name in files:
                if name.endswith(".py") and name != path.basename(__file__):
                    yield path.join(dirpath, name)


def _all_source_text():
    return "\n".join(open(p, encoding="utf-8").read() for p in _sources())


@pytest.mark.parametrize("name", REMOVED_ATTRIBUTES)
def test_the_attribute_is_gone_from_the_tree(name):
    """Matched as a whole identifier, not a substring.

    Several of these names are prefixes or suffixes of live ones --
    `sound_playing` sits inside `invisibility_sound_playing` -- so a plain
    containment check would report a deletion as incomplete forever.
    """
    hits = re.findall(r"\b(?:self|game)\.%s\b" % re.escape(name),
                      _all_source_text())

    assert hits == []


@pytest.mark.parametrize("name", REMOVED_METHODS)
def test_the_method_is_gone_from_the_tree(name):
    """Definition and call sites both.

    Matched precisely rather than as a substring: `turn_on_the_lights` is a
    prefix of `turn_on_the_lights_task_title`, which is a live attribute on
    Task, so a naive `name not in source` could never go green.
    """
    text = _all_source_text()

    assert f"def {name}(" not in text
    assert f".{name}(" not in text


def test_game_has_no_draw_text_method():
    from game import Game

    assert not hasattr(Game, "draw_text")


def test_button_and_board_keep_their_draw_text():
    """The near-miss guard: three classes had draw_text and only Game's was dead.

    Starts green. It exists so that deleting Game.draw_text by grep, rather
    than by reading, fails loudly instead of taking the menus with it.
    """
    from core.board import Board
    from core.sprites import Button

    assert callable(Button.draw_text)
    assert callable(Board.draw_text)


def test_game_has_no_debug_prints():
    tree = ast.parse(open(GAME_PY, encoding="utf-8").read())
    lines = [node.lineno for node in ast.walk(tree)
             if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "print"]

    assert lines == []


def test_the_font_attribute_is_assigned_once():
    """It was assigned twice: a path string, then the real Font that shadows it."""
    tree = ast.parse(open(GAME_PY, encoding="utf-8").read())
    stores = [node.lineno for node in ast.walk(tree)
              if isinstance(node, ast.Attribute) and node.attr == "font"
              and isinstance(node.ctx, ast.Store)]

    assert len(stores) == 1


@pytest.mark.xfail(reason="known bug, left deliberately: the only line that sets "
                          "pause_quit_button_status True is commented out, so the "
                          "three menu branches reading it are unreachable",
                   strict=True)
def test_the_pause_quit_path_is_reachable():
    """Records a latent bug rather than silently fixing or removing it.

    core/menu.py branches on game.pause_quit_button_status in three places, and
    nothing ever sets it True -- the assignment in the pause-menu mouse handler
    is commented out. Restoring it is a behaviour change and belongs in its own
    commit, made with the game running.

    Parsed rather than grepped: the commented-out setter still contains the
    text, so a substring search would say the path works.
    """
    tree = ast.parse(open(GAME_PY, encoding="utf-8").read())
    set_true = [node for node in ast.walk(tree)
                if isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Constant) and node.value.value is True
                and any(isinstance(t, ast.Attribute)
                        and t.attr == "pause_quit_button_status"
                        for t in node.targets)]

    assert set_true, "nothing sets pause_quit_button_status True"
