"""Launcher for the LAN game server. The implementation is multiplayer/server.py.

Running a file by path puts that file's own directory on sys.path, so a script
inside multiplayer/ could not import its own package. Launchers therefore stay
here at src/, where README points them.
"""

import argparse

from multiplayer.server import serve

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--players', type=int, default=4,
                        help='connections to wait for before assigning the imposter')
    args = parser.parse_args()
    serve(expected_players=args.players)
