import socket
import asyncore
import random
import pickle
import time

from multiplayer import protocol

BUFFERSIZE = 8192

print("Server Address: " + socket.gethostbyname(socket.gethostname()))

outgoing = []

# The image each colour's ejected sprite uses, mirroring the per-colour
# strings core/sprites.py: Player.__init__ hardcodes on eject_img. Only
# these five colours are selectable (see core/menu.py's colour choices and
# core/meeting.py: VOTE_CHECKBOXES), so this is the full set.
EJECT_IMG_BY_COLOUR = {
    "Red": "red_player_imgs_right[9]",
    "Blue": "blue_player_imgs_right[9]",
    "Orange": "orange_player_imgs_right[9]",
    "Yellow": "yellow_player_imgs_right[9]",
    "Green": "green_player_imgs_right[9]",
}


class RoundState:
    """Server-authoritative facts about the current round.

    Without this, every client guessed independently: the highest connected
    id called itself the imposter, and each client self-tallied votes and
    self-ejected once it counted >= 2 -- a race with no real per-round
    randomness, and a threshold that does not scale with how many players
    are actually connected. The server is the only process that sees every
    connection, so it is the only one that can actually assign a role or
    count a majority.
    """

    def __init__(self):
        self.imposter_id = None
        # set once every expected player has connected; clients wait in a
        # lobby until they are told, so nobody starts before the others
        self.started = False
        # edge-trigger guard: a majority is only acted on once, and resets
        # to None on its own once votes clear out at the end of a meeting
        self.last_majority_colour = None

    def reset(self):
        self.__init__()


round_state = RoundState()


def assign_imposter_if_ready(expected_players):
    """Pick the round's imposter once enough players have connected."""
    if round_state.imposter_id is not None:
        return
    if len(minionmap) < expected_players:
        return
    round_state.imposter_id = random.choice(list(minionmap.keys()))
    print("[round] imposter assigned: player %s" % round_state.imposter_id)


def broadcast_lobby(expected_players):
  """Tell every client how many have connected, and whether the round has started.

  The round starts, for good, the moment the expected number of players is
  reached; a client leaves its lobby screen on the first message that says so.
  """
  if not round_state.started and len(minionmap) >= expected_players:
    round_state.started = True
    print("[round] all %d players connected, starting" % len(minionmap))
  message = pickle.dumps(['lobby status', len(minionmap), expected_players, round_state.started])
  for conn in list(outgoing):
    try:
      conn.send(message)
    except Exception:
      outgoing.remove(conn)


def apply_round_authority():
    """Overwrite the fields the server -- not the client -- now owns.

    Runs on every update so a client's stale or wrong self-report can never
    reach the broadcast: imposter is set from round_state, not from
    whatever a minion last claimed about itself.
    """
    for player_id, minion in minionmap.items():
        minion.imposter = (player_id == round_state.imposter_id)
    tally_votes_and_maybe_eject()


def tally_votes_and_maybe_eject():
    """Count votes among the alive and connected, eject on a real majority."""
    alive = [m for m in minionmap.values() if m.alive_status]
    if not alive:
        return

    votes_for = {}
    for minion in alive:
        if minion.voted:
            votes_for.setdefault(minion.voted, set()).add(minion.player_id)

    majority_needed = len(alive) // 2 + 1
    winner = next((colour for colour, voters in votes_for.items()
                   if len(voters) >= majority_needed), None)

    if winner == round_state.last_majority_colour:
        return
    round_state.last_majority_colour = winner
    if winner is None:
        return

    for minion in alive:
        if minion.player_colour == winner:
            minion.alive_status = False
            minion.eject_sync = (minion.eject_sync or 0) + 1
            minion.eject_img = EJECT_IMG_BY_COLOUR.get(winner)
    print("[round] %s ejected by vote (%d/%d)"
          % (winner, len(votes_for[winner]), len(alive)))


class Minion:
  def __init__(self, player_id):
    self.x = 50
    self.y = 50
    self.sync_img = None
    self.sync_img_index = None
    self.left_img_index = 0
    self.right_img_index = 0
    self.up_img_index = 0
    self.down_img_index = 0
    self.alive_status = True
    self.player_id = player_id
    self.player_colour = None
    self.tasks_completed = 0
    self.sabotagelights_sync = 0
    self.sabotagereactor_sync = 0
    self.victim_id = 0
    self.imposter = False
    self.emergency_sync = 0
    self.voted = None
    self.got_votes = 0
    self.emergency_meeting_img_sync = None
    self.emergency_meeting_img_sync_report = None
    self.victim_id_report = 0
    self.got_reported = False
    self.eject_sync = False
    self.eject_img = None
    # last meeting chat line this player sent, rebroadcast until replaced
    self.chat_seq = 0
    self.chat_author = ""
    self.chat_text = ""

minionmap = {}

def updateWorld(message):
  arr = pickle.loads(message)
  player_id = arr[1]
  x = arr[2]
  y = arr[3]
  alive_status = arr[4]
  sync_img = arr[5]
  sync_img_index = arr[6]
  left_img_index = arr[7]
  right_img_index = arr[8]
  up_img_index = arr[9]
  down_img_index = arr[10]
  player_colour = arr[11]
  tasks_completed = arr[12]
  sabotagelights_sync = arr[13]
  sabotagereactor_sync = arr[14]
  victim_id = arr[15]
  imposter = arr[16]
  emergency_sync = arr[17]
  voted = arr[18]
  got_votes = arr[19]
  emergency_meeting_img_sync = arr[20]
  emergency_meeting_img_sync_report = arr[21]
  victim_id_report = arr[22]
  got_reported = arr[23]
  eject_sync = arr[24]
  eject_img = arr[25]
  # chat fields are appended at the end, older clients simply omit them
  chat_seq = arr[protocol.IN_CHAT_SEQ] if len(arr) > protocol.IN_CHAT_SEQ else 0
  chat_author = arr[protocol.IN_CHAT_AUTHOR] if len(arr) > protocol.IN_CHAT_AUTHOR else ""
  chat_text = arr[protocol.IN_CHAT_TEXT] if len(arr) > protocol.IN_CHAT_TEXT else ""

  if player_id == 0: return

  minionmap[player_id].x = x
  minionmap[player_id].y = y
  minionmap[player_id].alive_status = alive_status
  minionmap[player_id].sync_img = sync_img
  minionmap[player_id].sync_img_index = sync_img_index
  minionmap[player_id].left_img_index = left_img_index
  minionmap[player_id].right_img_index = right_img_index
  minionmap[player_id].up_img_index = up_img_index
  minionmap[player_id].down_img_index = down_img_index
  minionmap[player_id].player_colour = player_colour
  minionmap[player_id].tasks_completed = tasks_completed
  minionmap[player_id].sabotagelights_sync = sabotagelights_sync
  minionmap[player_id].sabotagereactor_sync = sabotagereactor_sync
  minionmap[player_id].victim_id = victim_id
  minionmap[player_id].imposter = imposter
  minionmap[player_id].emergency_sync = emergency_sync
  minionmap[player_id].voted = voted
  minionmap[player_id].got_votes = got_votes
  minionmap[player_id].emergency_meeting_img_sync = emergency_meeting_img_sync
  minionmap[player_id].emergency_meeting_img_sync_report = emergency_meeting_img_sync_report
  minionmap[player_id].victim_id_report = victim_id_report
  minionmap[player_id].got_reported = got_reported
  minionmap[player_id].eject_sync = eject_sync
  minionmap[player_id].eject_img = eject_img
  minionmap[player_id].chat_seq = chat_seq
  minionmap[player_id].chat_author = chat_author
  minionmap[player_id].chat_text = chat_text

  apply_round_authority()

  remove = []

  for i in outgoing:
    update = ['player locations']

    for key, value in minionmap.items():
      update.append([value.player_id, value.x, value.y, value.alive_status, value.sync_img, value.sync_img_index, value.left_img_index, value.right_img_index, value.up_img_index, value.down_img_index, value.player_colour, value.tasks_completed, value.sabotagelights_sync, value.sabotagereactor_sync, value.victim_id, value.imposter, value.emergency_sync, value.voted, value.got_votes, value.emergency_meeting_img_sync, value.emergency_meeting_img_sync_report, value.victim_id_report, value.got_reported, value.eject_sync, value.eject_img, value.chat_seq, value.chat_author, value.chat_text])

    try:
      i.send(pickle.dumps(update))
    except Exception:
      remove.append(i)
      continue

    for r in remove:
      outgoing.remove(r)

class MainServer(asyncore.dispatcher):
  def __init__(self, port, expected_players=4):
    asyncore.dispatcher.__init__(self)
    self.expected_players = expected_players
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.bind(('', port))
    self.listen(10)
  def handle_accept(self):
    conn, addr = self.accept()
    outgoing.append(conn)
    player_id = random.randint(1000, 1000000)
    playerminion = Minion(player_id)
    minionmap[player_id] = playerminion
    print("[round] player %s connected (%d/%d)"
          % (player_id, len(minionmap), self.expected_players))
    conn.send(pickle.dumps(['id update', player_id]))
    assign_imposter_if_ready(self.expected_players)
    broadcast_lobby(self.expected_players)
    SecondaryServer(conn)

class SecondaryServer(asyncore.dispatcher_with_send):
  def handle_read(self):
    recievedData = self.recv(BUFFERSIZE)
    if recievedData:
      updateWorld(recievedData)
    else: self.close()

def serve(port=4321, expected_players=4):
  MainServer(port, expected_players)
  asyncore.loop()

# guarded so the module can be imported (by tests) without opening a socket
if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--port', type=int, default=4321)
  parser.add_argument('--players', type=int, default=4,
                       help='connections to wait for before assigning the imposter')
  args = parser.parse_args()
  serve(args.port, args.players)