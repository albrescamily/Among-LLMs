"""The star import in game.py is load-bearing, and this is why.

Three of the display helpers blit an image named by a *string* that a sprite
handed them:

    game.py     self.screen.blit(eval(self.emergency_img_sync), (0, 0))
    sprites.py  self.emergency_meeting_img_sync = "red_player_emergency_meeting"

eval() with no globals argument uses the globals of the module that calls it,
so those bare names only resolve because game.py does `from settings import *`.
Rewriting that to `from core import settings` would leave the game importable,
the suite green, and the emergency-meeting screen crashing with NameError the
first time anybody calls a meeting.

Two things are pinned here, and the second matters more than it looks:

  1. The names resolve in the globals of every module that evals them.
  2. *Only declared modules eval at all.* Checking (1) against game.py alone
     would stay green if someone moved display_eject_alert into a new module
     that forgot the star import -- the check would simply be looking in the
     wrong place. EVAL_HOSTS forces that move to be a deliberate act.

There are two kinds of eval in this codebase and only one of them is fragile:

  game.py                    eval("red_player_emergency_meeting")
      A bare settings name. Needs that name in the calling module's globals,
      which is what the star import provides. This is the fragile kind.

  multiplayer/world_sync.py  eval("self.Players[p[0]].player_imgs_left[p[6]]")
      Attribute lookups on the frame's own locals. Needs no module globals at
      all, which is why apply_row's first parameter is named `self`.
"""

import ast
import importlib
from os import path, walk

import pygame as pg
import pytest

SRC = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'src')

# Every module allowed to eval anything at all.
EVAL_HOSTS = {"game", "multiplayer.world_sync"}

# The subset that evals bare settings names, and so must have them in its
# globals. Adding a module here is a promise that it star-imports settings;
# adding one to EVAL_HOSTS but not here is a claim that it only evals
# expressions built from its own locals.
SETTINGS_EVAL_HOSTS = {"game"}

COLOURS = ["red", "blue", "orange", "yellow", "green"]

EXPRESSIONS = (
    [f"{colour}_player_emergency_meeting" for colour in COLOURS]
    + [f"{colour}_player_emergency_meeting_report" for colour in COLOURS]
    # the eject animation indexes into the walk cycle
    + [f"{colour}_player_imgs_right[9]" for colour in COLOURS]
)


def calls_eval(tree):
    """True if this syntax tree calls the builtin eval anywhere."""
    return any(isinstance(node, ast.Call)
               and isinstance(node.func, ast.Name)
               and node.func.id == "eval"
               for node in ast.walk(tree))


def modules_that_eval():
    """Every module under src/ containing a bare eval() call, dotted."""
    found = set()
    for dirpath, _dirs, files in walk(SRC):
        if "__pycache__" in dirpath:
            continue
        for name in files:
            if not name.endswith(".py"):
                continue
            full = path.join(dirpath, name)
            source = open(full, encoding="utf-8").read()
            if not calls_eval(ast.parse(source)):
                continue
            relative = path.relpath(full, SRC)[:-3].replace("\\", "/")
            dotted = relative.replace("/", ".")
            found.add(dotted[:-9] if dotted.endswith(".__init__") else dotted)
    return found


def test_only_declared_modules_evaluate_a_wire_supplied_name():
    """Moving an eval out of game.py must be deliberate, not accidental.

    If this fails, either put the eval back or add the module to EVAL_HOSTS --
    which subjects it to the resolution tests below, where a missing star
    import shows up immediately.
    """
    assert modules_that_eval() == EVAL_HOSTS


def test_the_host_check_would_notice_a_new_eval():
    # The exact shape of the mistake: a helper moved into its own module.
    escaped = ast.parse("def draw_eject(game):\n"
                        "    game.screen.blit(eval(game.eject_img), (0, 0))\n")

    assert calls_eval(escaped)


def test_the_host_check_does_not_cry_wolf():
    innocent = ast.parse("def draw(game):\n    game.screen.blit(game.img, (0, 0))\n")

    assert not calls_eval(innocent)


@pytest.mark.parametrize("host", sorted(SETTINGS_EVAL_HOSTS))
@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_the_wire_supplied_image_name_resolves(host, expression):
    module = importlib.import_module(host)

    assert isinstance(eval(expression, vars(module)), pg.Surface)


def test_the_settings_hosts_are_a_subset_of_the_eval_hosts():
    assert SETTINGS_EVAL_HOSTS <= EVAL_HOSTS
