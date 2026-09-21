"""The server, not each client, now decides the imposter and the eject.

Before this, every client guessed the imposter by "whoever has the highest
connected id" and self-ejected once it counted >= 2 votes -- both computed
independently per client, with no real per-round randomness and no majority
that scales with how many players are actually in the game. These tests pin
the server-side replacement: multiplayer/server.py's RoundState.
"""

import io
import pickle

import pytest

from multiplayer import server


@pytest.fixture
def clean_server():
    server.minionmap.clear()
    del server.outgoing[:]
    server.round_state.reset()
    yield server
    server.minionmap.clear()
    del server.outgoing[:]
    server.round_state.reset()


class FakeConnection:
    def __init__(self):
        self.sent = []

    def send(self, data):
        self.sent.append(pickle.loads(data))


def packet(player_id, colour="Red", voted=None, alive=True):
    """A client state packet: the tag, then the 25 original fields."""
    fields = ['position update', player_id, 100, 200, alive, "img", "[0]",
              0, 0, 0, 0, colour, 0, 0, 0, 0, False, 0, voted, 0, None, None,
              0, False, 0, None]
    return pickle.dumps(fields)


def connect(srv, player_id, expected_players=4):
    """A player joining, the way MainServer.handle_accept does it."""
    srv.minionmap[player_id] = srv.Minion(player_id)
    conn = FakeConnection()
    srv.outgoing.append(conn)
    srv.assign_imposter_if_ready(expected_players)
    return conn


def test_no_imposter_until_enough_players_have_joined(clean_server):
    connect(clean_server, 1, expected_players=2)

    assert clean_server.round_state.imposter_id is None


def test_the_imposter_is_assigned_once_the_lobby_fills(clean_server):
    connect(clean_server, 1, expected_players=2)
    connect(clean_server, 2, expected_players=2)

    assert clean_server.round_state.imposter_id in (1, 2)


def test_exactly_one_player_is_broadcast_as_the_imposter(clean_server):
    connect(clean_server, 1, expected_players=2)
    listener = connect(clean_server, 2, expected_players=2)

    clean_server.updateWorld(packet(1))

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    imposters = [pid for pid, row in rows.items() if row[15] is True]
    assert imposters == [clean_server.round_state.imposter_id]


def test_a_client_cannot_lie_its_way_into_being_the_imposter(clean_server):
    connect(clean_server, 1, expected_players=2)
    listener = connect(clean_server, 2, expected_players=2)
    not_the_imposter = 2 if clean_server.round_state.imposter_id == 1 else 1

    # the client claims imposter=True for itself regardless of the round
    clean_server.updateWorld(packet(not_the_imposter))
    fields = list(pickle.loads(packet(not_the_imposter)))
    fields[16] = True
    clean_server.updateWorld(pickle.dumps(fields))

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    assert rows[not_the_imposter][15] is False


def test_a_late_joiner_never_becomes_imposter_once_assigned(clean_server):
    connect(clean_server, 1, expected_players=2)
    connect(clean_server, 2, expected_players=2)
    chosen = clean_server.round_state.imposter_id

    connect(clean_server, 3, expected_players=2)

    assert clean_server.round_state.imposter_id == chosen


def test_a_majority_vote_ejects_the_colour(clean_server):
    connect(clean_server, 1, expected_players=3)
    connect(clean_server, 2, expected_players=3)
    listener = connect(clean_server, 3, expected_players=3)

    clean_server.updateWorld(packet(1, colour="Red"))
    clean_server.updateWorld(packet(2, colour="Blue", voted="Red"))
    clean_server.updateWorld(packet(3, colour="Green", voted="Red"))

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    assert rows[1][3] is False              # alive_status
    assert rows[1][23] == 1                 # eject_sync bumped once


def test_a_vote_short_of_majority_does_not_eject(clean_server):
    connect(clean_server, 1, expected_players=3)
    connect(clean_server, 2, expected_players=3)
    listener = connect(clean_server, 3, expected_players=3)

    clean_server.updateWorld(packet(1, colour="Red"))
    clean_server.updateWorld(packet(2, colour="Blue", voted="Red"))
    clean_server.updateWorld(packet(3, colour="Green"))    # no vote

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    assert rows[1][3] is True
    assert rows[1][23] == 0


def test_holding_the_same_majority_does_not_eject_twice(clean_server):
    connect(clean_server, 1, expected_players=3)
    connect(clean_server, 2, expected_players=3)
    listener = connect(clean_server, 3, expected_players=3)
    clean_server.updateWorld(packet(1, colour="Red"))
    clean_server.updateWorld(packet(2, colour="Blue", voted="Red"))
    clean_server.updateWorld(packet(3, colour="Green", voted="Red"))

    # the same votes keep arriving every frame, as they do on the real wire
    clean_server.updateWorld(packet(2, colour="Blue", voted="Red"))

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    assert rows[1][23] == 1


def test_a_dead_player_does_not_count_towards_the_majority(clean_server):
    # 4 connected, but only 3 are alive: majority among the alive is 2, which
    # would not be enough if the dead 4th were (wrongly) still counted, since
    # that would put majority at 3.
    connect(clean_server, 1, expected_players=4)
    connect(clean_server, 2, expected_players=4)
    connect(clean_server, 3, expected_players=4)
    listener = connect(clean_server, 4, expected_players=4)
    clean_server.updateWorld(packet(4, colour="Yellow", alive=False))

    clean_server.updateWorld(packet(1, colour="Red"))
    clean_server.updateWorld(packet(2, colour="Blue", voted="Red"))
    clean_server.updateWorld(packet(3, colour="Green", voted="Red"))

    rows = {row[0]: row for row in listener.sent[-1][1:]}
    assert rows[1][3] is False


# -- over a real socket, the same way the LAN chat tests do -----------------

def state(player_id, colour="Red", voted=None, alive=True):
    return pickle.dumps(['position update', player_id, 100, 200, alive,
                         "img", "[0]", 0, 0, 0, 0, colour, 0, 0, 0, 0, False,
                         0, voted, 0, None, None, 0, False, 0, None])


def rows_from(sock):
    """Every broadcast waiting on the socket, flattened to {player_id: row}."""
    buffer = io.BytesIO(sock.recv(65536))
    rows = {}
    while True:
        try:
            update = pickle.load(buffer)
        except EOFError:
            break
        assert update[0] == 'player locations'
        for row in update[1:]:
            rows[row[0]] = row
    return rows


def test_imposter_assignment_over_a_real_socket(lan):
    # lan's MainServer uses the default expected_players (4), unlike the
    # in-process tests above which pass it explicitly through connect().
    join, pump, _port = lan
    players = [join() for _ in range(4)]
    pump()

    last, last_id = players[-1]
    last.send(state(last_id))
    pump()

    rows = rows_from(last)
    imposters = [pid for pid, row in rows.items() if row[15] is True]
    assert len(imposters) == 1


def test_eject_over_a_real_socket(lan):
    join, pump, _port = lan
    (a, a_id), (b, b_id), (c, c_id), (d, d_id) = [join() for _ in range(4)]
    pump()

    a.send(state(a_id, colour="Red"))
    pump()
    b.send(state(b_id, colour="Blue", voted="Red"))
    pump()
    c.send(state(c_id, colour="Orange", voted="Red"))
    pump()
    d.send(state(d_id, colour="Yellow", voted="Red"))
    pump()

    rows = rows_from(d)
    assert rows[a_id][3] is False
    assert rows[a_id][23] == 1
