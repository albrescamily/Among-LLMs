"""Where the game's files live.

The code sits in amongUs/src/ and the artwork in amongUs/Assets/ next to it,
so anything that has to reach an asset needs the folder holding both, not the
directory a module happens to be in:

    amongUs/src/core/paths.py   <- this file
    amongUs/Assets/Images/...   <- what asset() points at

Every path is resolved from this file's own location, so the game finds its
assets no matter which directory it was started from. That also means the
number of dirname() calls below is tied to how deep this file sits: move it
and every asset in the game silently resolves to the wrong folder. tests/
test_paths.py pins it.
"""

from os import path

# core/ -> src/ -> amongUs/, which holds src/ and Assets/
ROOT = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))

ASSETS = path.join(ROOT, 'Assets')


def asset(relative):
    """Absolute path to an asset, given the way it is written in the code.

    Accepts the Windows separators used by some of the older calls
    ('Assets\\Images\\...') and normalises them, so the same literal also works
    on Linux and macOS.
    """
    return path.join(ROOT, *relative.replace('\\', '/').split('/'))
