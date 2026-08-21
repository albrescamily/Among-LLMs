"""No module-level function refers to a `self` it was never given.

The mode packages were lifted out of methods on Game, and `self.x` became
`game.x` by search-and-replace. Search-and-replace misses `Player(self, ...)`,
where `self` is followed by a comma rather than a dot -- which compiles fine,
imports fine, and raises NameError the moment a round starts. Three of those
survived the move here and no other test noticed, because nothing in the suite
runs a round.

So this checks it statically. It allows a function that genuinely takes a
parameter called `self`, which world_sync.apply_row does on purpose.
"""

import ast
from os import path

import pytest

SRC = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'src')

MODULES = [
    "core/audio.py", "core/loop.py", "core/paths.py",
    "core/kills.py", "core/meeting.py", "core/task_triggers.py", "core/hud.py", "core/render.py",
    "minigames/asteroids.py",
    "singleplayer/freeplay.py",
    "multiplayer/session.py", "multiplayer/state_sync.py",
    "multiplayer/world_sync.py", "multiplayer/net_client.py",
]


def stray_selfs(tree):
    """Every `self` used by a top-level function that has no such parameter."""
    found = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = {a.arg for a in node.args.args}
        if "self" in params:
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Name) and inner.id == "self":
                found.append((node.name, inner.lineno))
    return found


@pytest.mark.parametrize("relative", MODULES)
def test_no_function_refers_to_a_self_it_does_not_have(relative):
    source = open(path.join(SRC, relative), encoding="utf-8").read()

    assert stray_selfs(ast.parse(source)) == []


def test_the_check_would_actually_catch_it():
    # The exact shape that slipped through: self as a positional argument.
    leaked = ast.parse("def run(game):\n    game.player = Player(self, 1)\n")

    assert stray_selfs(leaked) == [("run", 2)]


def test_a_function_that_really_takes_self_is_left_alone():
    # world_sync.apply_row names its first parameter `self` deliberately.
    deliberate = ast.parse("def apply_row(self, p, i):\n    self.Players[p] = i\n")

    assert stray_selfs(deliberate) == []
