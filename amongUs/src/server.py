"""Launcher for the LAN game server. The implementation is multiplayer/server.py.

Running a file by path puts that file's own directory on sys.path, so a script
inside multiplayer/ could not import its own package. Launchers therefore stay
here at src/, where README points them.
"""

from multiplayer.server import serve

if __name__ == '__main__':
    serve()
