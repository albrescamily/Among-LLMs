"""No module-level function reads a name it never bound.

This is the guard for the single most dangerous thing in the game.py refactor.

draw() fetches `keys = pg.key.get_pressed()` six times, but twelve places use
`keys`. Six of them -- wires, divert power, align engine, gas can, fuel and
asteroids -- have no fetch of their own. They work only because the *wifi*
block's fetch leaks down the rest of the function body.

Extract the wifi block into its own function and all six raise NameError, in a
codebase where nothing runs a frame and so nothing notices. Same failure class
as the stray `self` in test_no_stray_self.py, which bit us once already.

The structural fix is that every extracted trigger takes `keys` as a parameter.
This test is what makes forgetting that impossible.
"""

import ast
import importlib
import builtins
from os import path

import pytest

SRC = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'src')

MODULES = [
    "core/audio.py", "core/loop.py", "core/paths.py",
    "core/kills.py", "core/meeting.py", "core/task_triggers.py", "core/hud.py", "core/render.py", "core/task_render.py",
    "minigames/asteroids.py",
    "singleplayer/freeplay.py",
    "multiplayer/session.py", "multiplayer/state_sync.py",
    "multiplayer/world_sync.py", "multiplayer/net_client.py",
]

BUILTINS = set(dir(builtins))


def _star_import_names(module_name):
    """What `from <module> import *` actually puts in scope.

    Resolved by importing the module rather than guessed, because two of the
    modules here star-import core.settings and core.sprites for hundreds of
    surface and constant names. Treating a star import as opaque would mean
    either skipping those modules entirely -- losing the check where it matters
    most -- or flagging every constant they use.
    """
    module = importlib.import_module(module_name)
    exported = getattr(module, "__all__", None)
    if exported is not None:
        return set(exported)
    return {name for name in vars(module) if not name.startswith("_")}


def _module_level_names(tree):
    """Everything bound at module scope: imports, assignments, defs, classes."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
            names |= _star_import_names(node.module)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
    return names


def _bound_in(func):
    """Every name the function itself binds: params, assignments, loops, withs."""
    args = func.args
    names = {a.arg for a in args.args + args.posonlyargs + args.kwonlyargs}
    if args.vararg:
        names.add(args.vararg.arg)
    if args.kwarg:
        names.add(args.kwarg.arg)
    for node in ast.walk(func):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.Global) or isinstance(node, ast.Nonlocal):
            names.update(node.names)
    return names


def unbound_locals(tree):
    """Names a top-level function loads without ever binding them.

    Module globals, imports and builtins are all fine -- the target is the name
    that only exists because some *other* function happened to assign it in a
    shared frame.
    """
    module_names = _module_level_names(tree)
    found = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        bound = _bound_in(node) | module_names | BUILTINS
        seen = set()
        for inner in ast.walk(node):
            if (isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load)
                    and inner.id not in bound and inner.id not in seen):
                seen.add(inner.id)
                found.append((node.name, inner.lineno, inner.id))
    return found


@pytest.mark.parametrize("relative", MODULES)
def test_no_function_reads_a_name_it_never_bound(relative):
    source = open(path.join(SRC, relative), encoding="utf-8").read()

    assert unbound_locals(ast.parse(source)) == []


def test_the_check_catches_the_keys_leak():
    # Exactly the shape an extracted trigger takes if it forgets its parameter.
    leaked = ast.parse("def trigger(game):\n"
                       "    if keys[32]:\n"
                       "        game.window_status = True\n")

    assert unbound_locals(leaked) == [("trigger", 2, "keys")]


def test_a_trigger_that_takes_keys_is_fine():
    correct = ast.parse("def trigger(game, keys):\n"
                        "    if keys[32]:\n"
                        "        game.window_status = True\n")

    assert unbound_locals(correct) == []


def test_module_globals_and_builtins_are_not_flagged():
    fine = ast.parse("import pygame as pg\n"
                     "RADIUS = 90\n"
                     "def trigger(game):\n"
                     "    return len(pg.key.get_pressed()) and RADIUS\n")

    assert unbound_locals(fine) == []
