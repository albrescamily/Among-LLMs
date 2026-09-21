"""The client end of the LAN connection.

Packets are pickled lists over plain TCP, and the game loop drives the socket
by hand: it calls poll() once a frame to pick up whatever the server has sent,
and send() once a frame with the local player's state. Nothing here blocks --
the game has to keep drawing at sixty frames a second either way.
"""

import pickle
import select
import socket

BUFFERSIZE = 8192

# the port server.serve() listens on
DEFAULT_PORT = 4321


class NetClient:
    """A connection to the LAN server, polled once per frame."""

    def __init__(self, address, port=DEFAULT_PORT, sock=None):
        self.address = address
        self.port = port
        # a caller can pass its own socket; the tests hand over a socketpair
        self.socket = sock

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # the address came straight from what the player typed into the menu
        self.socket.connect((self.address.strip(), self.port))
        return self

    def poll(self):
        """Everything the server has sent since the last frame.

        Returns a list because a quiet frame is the common case and the caller
        should not have to tell 'nothing arrived' apart from 'something went
        wrong'. A read that fails is dropped: the next broadcast carries the
        same state, since the server resends every player's row every time.
        """
        if self.socket is None:
            return []

        messages = []
        readable, _writable, _errored = select.select([self.socket], [], [], 0)
        for ready in readable:
            try:
                messages.append(pickle.loads(ready.recv(BUFFERSIZE)))
            except Exception:
                continue
        return messages

    def send(self, packet):
        """Push the local player's state out, if the connection still holds."""
        if self.socket is None:
            return False
        try:
            self.socket.send(pickle.dumps(packet))
            return True
        except Exception:
            # someone quit, or the server went away; the loop's own win/lose
            # checks are what end the game, not this
            return False

    def close(self):
        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
