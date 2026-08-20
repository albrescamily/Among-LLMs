"""Importing a program must not run it.

server.py has been guarded since before this refactor; the two voice modules
were not, and both did their work at module scope. voice.py in particular calls
input() at import, and its bare except turns the resulting EOFError into an
endless retry loop -- so importing it does not fail, it hangs.

Which is why these run in a subprocess with a timeout: a test that hangs the
whole suite is worse than one that fails.
"""

import os
import subprocess
import sys
from os import path

import pytest

SRC = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'src')

ENTRY_POINTS = [
    "multiplayer.server",           # the control: already guarded
    "multiplayer.voice.client",
    "multiplayer.voice.relay",
]


@pytest.mark.parametrize("module", ENTRY_POINTS)
def test_importing_does_not_run_the_program(module):
    pytest.importorskip("pyaudio", reason="the voice stack needs pyaudio")

    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    proc = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=SRC,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=15,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")


LAUNCHERS = ["server.py", "voice.py", "server_voice.py"]


@pytest.mark.parametrize("script", LAUNCHERS)
def test_the_documented_launcher_still_exists(script):
    """README tells people to run these by path, so the paths have to hold.

    Running one by path puts its own directory on sys.path, so a launcher deep
    inside multiplayer/ could not import its own package. They stay at src/.
    """
    assert path.isfile(path.join(SRC, script))


@pytest.mark.parametrize("script", LAUNCHERS)
def test_a_launcher_is_a_shim_and_not_a_second_copy(script):
    source = open(path.join(SRC, script), encoding="utf-8").read()

    assert "if __name__ == '__main__':" in source
    assert len(source.splitlines()) < 20, "launchers delegate, they don't implement"
