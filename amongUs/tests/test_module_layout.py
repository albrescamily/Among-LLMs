"""Every module imports cleanly, on its own, from a cold interpreter.

There is no coverage of game, menu, board, tasks, sprites or tilemap, so the
package moves need *some* guard. This is the cheap one: if a module can be
imported by itself then its own imports resolve, which is the failure mode the
moves actually introduce.

Each import runs in a fresh subprocess on purpose. Doing it in-process with
importlib would inherit sys.modules from every test that ran before, and a
circular import between the new packages would be masked by whichever module
happened to be imported first.

MODULES is extended as each step of the refactor lands, so the list doubles as
a record of the layout the refactor is heading for.
"""

import os
import subprocess
import sys
from os import path

import pytest

SRC = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'src')

MODULES = [
    # shared by both game modes
    "core.paths",
    "core.settings",
    "core.sprites",
    "core.tilemap",
    "core.tasks",
    "core.chat",
    "core.drawable",
    "core.board",
    "core.menu",
    "core.gamefunctions",
    "core.audio",
    "core.loop",
    # multiplayer only
    "multiplayer.protocol",
    "multiplayer.server",
    "multiplayer.net_client",
    "multiplayer.state_sync",
    "multiplayer.world_sync",
    # the god object, still at the root
    "game",
    # main is deliberately absent: it is a bare `while True:` loop.
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports_on_its_own(module):
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    proc = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=SRC,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
