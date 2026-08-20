"""Where the game looks for its artwork.

Every image, sound, font and the tilemap itself is resolved relative to
paths.ROOT, which is computed from paths.py's own location. That makes ROOT
silently wrong the moment the module is moved to a different depth -- and
nothing else in the suite would notice, because a missing asset only blows up
when the game is actually started.

So these tests pin the resolution against real files on disk.
"""

from os import path

from core.paths import ROOT, ASSETS, asset


def test_root_is_the_amongus_folder():
    # ROOT has to be the directory holding both src/ and Assets/, not the
    # directory paths.py happens to sit in.
    assert path.basename(ROOT) == 'amongUs'
    assert path.isdir(path.join(ROOT, 'Assets'))
    assert path.isdir(path.join(ROOT, 'src'))


def test_assets_points_at_the_real_artwork():
    assert path.isfile(path.join(ASSETS, 'Images', 'Menu', 'back.png'))


def test_asset_resolves_the_files_the_game_actually_loads():
    # board.py:19 is the first asset the game ever touches; the tilemap is the
    # one game.load_data() needs before it can draw anything.
    assert path.isfile(asset("Assets/Images/Menu/back.png"))
    assert path.isfile(asset("Assets/Maps/map.tmx"))


def test_asset_normalises_windows_separators():
    # Some of the older call sites still write 'Assets\\Images\\...'.
    assert asset("Assets\\Images\\Menu\\back.png") == asset("Assets/Images/Menu/back.png")
