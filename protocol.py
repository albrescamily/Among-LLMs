"""Field layout of the LAN packets, shared by the game client and the server.

The protocol is a plain pickled list, addressed by position, so client and
server have to agree on every index. These constants are that agreement: the
chat fields were appended at the end precisely so no existing index moved.

Two shapes travel on the wire:

    client -> server   ['position update', player_id, ...25 fields..., ...chat]
    server -> clients  ['player locations', row, row, ...]
                       where row = [player_id, ...24 fields..., ...chat]

The client packet carries the message tag up front, so its indices are the
row indices shifted by one.
"""

# chat fields in the packet a client sends (tag occupies index 0)
IN_COLOUR = 11
IN_CHAT_SEQ = 26
IN_CHAT_AUTHOR = 27
IN_CHAT_TEXT = 28

# chat fields in a row of the broadcast the server sends back
OUT_COLOUR = 10
OUT_CHAT_SEQ = 25
OUT_CHAT_AUTHOR = 26
OUT_CHAT_TEXT = 27
