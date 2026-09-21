import sys

from cx_Freeze import setup,Executable

includefiles = [ ('amongUs/Assets', 'Assets') ] # files / folders to include. relative path to setup.py file
includes = []
excludes = []
# the game's own packages, plus what they import
packages = ["core", "singleplayer", "multiplayer",
            "idna", "pygame", "random", "sys", "os", "time", "pytmx", "random", "pickle", "select", "socket"]

# main.py imports `core.*` and friends as top level packages, which works
# because running it puts src/ on sys.path. The freezer has to be told the same.
searchpath = ['amongUs/src'] + sys.path

setup(
    name = 'FYP',
    version = '0.1',
    description = 'A general enhancement utility',
    author = 'ZFR',
    author_email = 'le...@null.com',
    options = {'build_exe': {'includes':includes,'excludes':excludes,'packages':packages,'include_files':includefiles,'path':searchpath}},
    executables = [Executable('amongUs/src/main.py')] # filename of python program main file
)
