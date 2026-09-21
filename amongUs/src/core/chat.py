"""Meeting chat.

The discussion window that shows up while an emergency meeting (or a body
report) is running: the message log, the scrollbar, the text input, the
character counter and the send button.

The game only has to do this much with it (see game.py):

    self.meeting_chat.open(duration)     when the discussion phase starts
    self.meeting_chat.handle_event(e)    inside events()
    self.meeting_chat.update()           every frame
    self.meeting_chat.draw(surface)      while the discussion is running
    self.meeting_chat.close()            when the discussion is over

To let an LLM (or the network) speak for the bots, set a responder:

    game.meeting_chat.responder = my_responder

    def my_responder(chat, kind, message):
        # kind is "meeting_start" or "player_message"
        # message is the ChatMessage that was just sent (None on meeting_start)
        for name, colour in chat.alive_bots():
            chat.schedule_message(name, colour, generate(...), delay_ms=1500)

While no responder is set the bots use the canned lines below, so the chat can
be tried out right away.
"""

import random

import pygame as pg
from core import display

from core.settings import *

CHAT_MAX_CHARS = 100            # what the counter shows: 0/100
CHAT_PANEL_W = 660
CHAT_PANEL_H = 560
CHAT_SCROLL_STEP = 45
AVATAR_SIZE = (36, 48)

PANEL_BG = (46, 50, 62)
PANEL_BORDER = (18, 20, 26)
HEADER_BG = (32, 35, 44)
BUBBLE_BG = (247, 248, 250)
BUBBLE_BG_DEAD = (198, 202, 212)
BUBBLE_BORDER = (24, 26, 33)
TEXT_DARK = (26, 28, 34)
TEXT_LIGHT = (236, 238, 243)
TEXT_MUTED = (150, 156, 172)
INPUT_BG = (252, 252, 253)
INPUT_BG_OFF = (206, 209, 218)
SEND_BG = (86, 173, 88)
SEND_BG_OFF = (120, 124, 136)
SCROLLBAR_FG = (120, 126, 142)

# Colour of the little name tag under each avatar
COLOUR_RGB = {
    "Red": (197, 17, 17),
    "Blue": (19, 46, 209),
    "Green": (17, 127, 45),
    "Pink": (237, 84, 249),
    "Orange": (239, 125, 48),
    "Yellow": (245, 245, 87),
    "Black": (63, 71, 78),
    "White": (214, 222, 241),
    "Purple": (108, 47, 188),
    "Brown": (113, 73, 30),
}
# Tags that need dark text to stay readable
COLOUR_DARK_TEXT = ("Yellow", "White")

# Names handed out to the bots, so the chat shows a nickname and not a colour
BOT_NAMES = ["madara", "lalanga", "Vmbatalha", "pernilongo", "Hollow",
             "Kitex", "Fisk", "Inkz", "Dracko", "Nyra", "Bolha", "Zoy"]

# Canned lines, used while no responder (LLM / network) is plugged in
DEMO_LINES = ["onde tu tava?", "eletrica comigo", "eu vi ele saindo do vent",
              "ta muito quieto", "skip", "matou na minha frente",
              "tava fazendo task", "confio nele", "vota nele", "quem reportou?",
              "eu vi 2 juntos", "nao fui eu"]


def _avatar_source(colour):
    """First 'walking down' frame of a colour, used as the chat avatar."""
    return {
        "Red": red_player_imgs_down,
        "Blue": blue_player_imgs_down,
        "Green": green_player_imgs_down,
        "Orange": orange_player_imgs_down,
        "Yellow": yellow_player_imgs_down,
        "Black": black_player_imgs_down,
        "Brown": brown_player_imgs_down,
        "Pink": pink_player_imgs_down,
        "Purple": purple_player_imgs_down,
        "White": white_player_imgs_down,
    }.get(colour, [None])[0]


class ChatMessage:
    def __init__(self, author, colour, text, dead=False, system=False):
        self.author = author
        self.colour = colour
        self.text = text
        self.dead = dead
        self.system = system
        self.surface = None     # rendered once, then reused every frame
        self.height = 0


class MeetingChat:
    def __init__(self, game):
        self.game = game
        self.is_open = False
        self.messages = []
        self.pending = []       # [(show_at_ms, ChatMessage)]
        self.responder = None   # hook for LLM bots / networked chat
        self.opened_at = 0
        self.duration_ms = 0    # 0 = no countdown in the header
        self.input_text = ""
        self.caret = 0
        self.scroll_px = 0      # distance from the bottom of the log
        # multiplayer: our last line goes out with every state packet until it
        # is replaced, so remote clients dedupe it by this sequence number
        self.out_seq = 0
        self.out_author = ""
        self.out_text = ""
        self.seen_seq = {}      # player_id -> last sequence we already showed
        self._avatars = {}      # colour -> scaled surface
        self._fonts = {}
        self._content_h = 0     # 0 means "needs measuring"

        self.panel_rect = pg.Rect(0, 0, CHAT_PANEL_W, CHAT_PANEL_H)
        self.panel_rect.center = (WIDTH // 2, HEIGHT // 2)
        self.header_rect = pg.Rect(self.panel_rect.x, self.panel_rect.y,
                                   CHAT_PANEL_W, 46)
        self.input_rect = pg.Rect(self.panel_rect.x + 14,
                                  self.panel_rect.bottom - 60,
                                  CHAT_PANEL_W - 28 - 120, 46)
        self.send_rect = pg.Rect(self.input_rect.right + 8, self.input_rect.y,
                                 112, 46)
        self.list_rect = pg.Rect(self.panel_rect.x + 14,
                                 self.header_rect.bottom + 10,
                                 CHAT_PANEL_W - 28,
                                 self.input_rect.top - self.header_rect.bottom - 40)

    # -- clock -------------------------------------------------------------
    def _now(self):
        # single place the clock is read, so tests can freeze time
        return pg.time.get_ticks()

    # -- fonts / avatars ---------------------------------------------------
    def _font(self, size):
        if size not in self._fonts:
            self._fonts[size] = pg.font.Font(FONT, size)
        return self._fonts[size]

    def _avatar(self, colour):
        if colour not in self._avatars:
            source = _avatar_source(colour)
            self._avatars[colour] = None if source is None else \
                pg.transform.smoothscale(source, AVATAR_SIZE).convert_alpha()
        return self._avatars[colour]

    # -- lifecycle ---------------------------------------------------------
    def open(self, duration_ms=0):
        if self.is_open:
            return
        self.is_open = True
        self.opened_at = self._now()
        self.duration_ms = duration_ms
        self._reset_input()
        self.clear()
        # so holding backspace (or a letter) repeats while typing
        pg.key.set_repeat(400, 40)
        if self.responder:
            self.responder(self, "meeting_start", None)
        else:
            self._demo_chatter()

    def close(self):
        if not self.is_open:
            return
        self.is_open = False
        self.pending = []
        self._reset_input()
        pg.key.set_repeat()

    def clear(self):
        self.messages = []
        self.pending = []
        self.scroll_px = 0
        self._content_h = 0
        # a new meeting shows every line again, including the ones a remote
        # player is still broadcasting from the previous one
        self.seen_seq = {}

    def _reset_input(self):
        self.input_text = ""
        self.caret = 0

    def seconds_left(self):
        """Seconds left in the discussion, or None when it is not timed."""
        if not self.duration_ms:
            return None
        left = self.duration_ms - (self._now() - self.opened_at)
        return max(0, -(-left // 1000)) if left > 0 else 0

    @property
    def can_type(self):
        """Ghosts watch the discussion, they do not talk in it."""
        return bool(getattr(self.game.player, "alive_status", True))

    # -- messages ----------------------------------------------------------
    def add_message(self, author, colour, text, dead=False, system=False):
        text = " ".join(str(text).split())
        if not text:
            return None
        message = ChatMessage(author, colour, text, dead, system)
        self.messages.append(message)
        self._content_h = 0     # re-measure on the next draw
        return message

    def schedule_message(self, author, colour, text, delay_ms, dead=False):
        """Queue a message to land `delay_ms` from now (a bot 'typing')."""
        message = ChatMessage(author, colour, " ".join(str(text).split()), dead)
        self.pending.append((self._now() + delay_ms, message))
        return message

    def update(self):
        if not self.is_open or not self.pending:
            return
        now = self._now()
        due = sorted((t, i) for i, (t, _) in enumerate(self.pending) if t <= now)
        if not due:
            return
        for _, index in due:
            self.messages.append(self.pending[index][1])
        self.pending = [entry for i, entry in enumerate(self.pending)
                        if i not in {index for _, index in due}]
        self._content_h = 0

    def send(self):
        """Posts whatever is in the input field as the local player."""
        if not self.can_type or not self.input_text.strip():
            return None
        name = getattr(self.game.menu, "word", "") or self.game.player_colour
        message = self.add_message(name, self.game.player_colour,
                                   self.input_text)
        # hand the line to the network layer (see outgoing_fields)
        self.out_seq += 1
        self.out_author = name
        self.out_text = message.text
        self._reset_input()
        self.scroll_px = 0      # jump back to the bottom of the log
        if self.responder and message:
            self.responder(self, "player_message", message)
        return message

    # -- multiplayer -------------------------------------------------------
    def outgoing_fields(self):
        """The chat part of the state packet: (sequence, author, text).

        The same line is sent on every frame until a new one replaces it, so
        clients that join or open their chat late still receive it.
        """
        return self.out_seq, self.out_author, self.out_text

    def receive_remote(self, player_id, seq, author, colour, text):
        """Shows a line broadcast by another player, at most once.

        Dropped while the chat is closed on purpose: the sender keeps
        broadcasting it, so it lands as soon as the discussion opens here.
        """
        if not self.is_open or not seq or not text or not str(text).strip():
            return None
        if player_id == getattr(self.game.player, "player_id", None):
            return None                 # our own line, echoed back by the server
        if seq <= self.seen_seq.get(player_id, 0):
            return None                 # already shown, or older than what we have
        self.seen_seq[player_id] = seq
        return self.add_message(author or colour, colour, text)

    # -- input -------------------------------------------------------------
    def handle_event(self, event):
        """Returns True when the chat consumed the event."""
        if not self.is_open:
            return False

        if event.type == pg.KEYDOWN:
            # while the chat is up the keyboard belongs to it: a stray key must
            # not pause the game or fire an action behind the panel
            if self.can_type:
                self._handle_key(event)
            return True

        if event.type == pg.MOUSEWHEEL:
            self._scroll(event.y * CHAT_SCROLL_STEP)
            return True

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button in (4, 5):
                self._scroll(CHAT_SCROLL_STEP if event.button == 4
                             else -CHAT_SCROLL_STEP)
                return True
            if event.button == LEFT_MOUSE_BUTTON:
                if self.send_rect.collidepoint(display.to_canvas(event.pos)):
                    self.send()
                    return True
                # swallow clicks on the panel so they do not reach the game
                return bool(self.panel_rect.collidepoint(display.to_canvas(event.pos)))
            return False

        return False

    def _handle_key(self, event):
        if event.key in (pg.K_RETURN, pg.K_KP_ENTER):
            self.send()
        elif event.key == pg.K_BACKSPACE:
            if self.caret > 0:
                self.input_text = (self.input_text[:self.caret - 1]
                                   + self.input_text[self.caret:])
                self.caret -= 1
        elif event.key == pg.K_DELETE:
            self.input_text = (self.input_text[:self.caret]
                               + self.input_text[self.caret + 1:])
        elif event.key == pg.K_LEFT:
            self.caret = max(0, self.caret - 1)
        elif event.key == pg.K_RIGHT:
            self.caret = min(len(self.input_text), self.caret + 1)
        elif event.key == pg.K_HOME:
            self.caret = 0
        elif event.key == pg.K_END:
            self.caret = len(self.input_text)
        elif event.unicode and event.unicode.isprintable():
            if len(self.input_text) < CHAT_MAX_CHARS:
                self.input_text = (self.input_text[:self.caret]
                                   + event.unicode
                                   + self.input_text[self.caret:])
                self.caret += 1

    def _scroll(self, amount):
        limit = max(0, self.content_height() - self.list_rect.height)
        self.scroll_px = max(0, min(limit, self.scroll_px + amount))

    # -- layout ------------------------------------------------------------
    def content_height(self):
        """Height of the whole log in pixels, measured once per change."""
        if not self._content_h:
            total = 0
            for message in self.messages:
                self._message_surface(message)
                total += message.height + 8
            self._content_h = max(0, total - 8)
        return self._content_h

    def _wrap(self, text, font, max_width):
        lines = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split(" "):
                candidate = word if not line else line + " " + word
                if font.size(candidate)[0] <= max_width:
                    line = candidate
                    continue
                if line:
                    lines.append(line)
                # a single word wider than the bubble is cut character by character
                while font.size(word)[0] > max_width:
                    cut = len(word)
                    while cut > 1 and font.size(word[:cut])[0] > max_width:
                        cut -= 1
                    lines.append(word[:cut])
                    word = word[cut:]
                line = word
            lines.append(line)
        return lines

    def _message_surface(self, message):
        """Renders one bubble (avatar + colour tag + name + text), once."""
        if message.surface is not None:
            return message.surface

        width = self.list_rect.width - 14      # leave room for the scrollbar
        name_font = self._font(17)
        text_font = self._font(15)
        tag_font = self._font(10)

        text_x = 66
        lines = self._wrap(message.text, text_font, width - text_x - 14)
        line_h = text_font.get_linesize()
        # the floor fits the avatar plus the colour tag stacked under it
        height = max(78, 10 + name_font.get_linesize() + 2
                     + line_h * len(lines) + 10)

        surface = pg.Surface((width, height), pg.SRCALPHA)
        bubble = pg.Rect(0, 0, width, height)
        pg.draw.rect(surface, BUBBLE_BG_DEAD if message.dead else BUBBLE_BG,
                     bubble, border_radius=14)
        pg.draw.rect(surface, BUBBLE_BORDER, bubble, width=3, border_radius=14)

        if message.system:
            label = text_font.render(message.text, True, (90, 94, 106))
            surface.blit(label, (width // 2 - label.get_width() // 2,
                                 height // 2 - label.get_height() // 2))
            message.surface = surface
            message.height = height
            return surface

        avatar = self._avatar(message.colour)
        if avatar:
            surface.blit(avatar, (16, 9))

        # colour tag under the avatar, like the name plate in the game
        tag_text = tag_font.render(message.colour or "?", True,
                                   TEXT_DARK if message.colour in COLOUR_DARK_TEXT
                                   else TEXT_LIGHT)
        tag_w = max(44, tag_text.get_width() + 12)
        tag = pg.Rect(14 + (AVATAR_SIZE[0] - tag_w) // 2, height - 26, tag_w, 16)
        pg.draw.rect(surface, COLOUR_RGB.get(message.colour, (90, 94, 106)),
                     tag, border_radius=8)
        pg.draw.rect(surface, BUBBLE_BORDER, tag, width=2, border_radius=8)
        surface.blit(tag_text, (tag.centerx - tag_text.get_width() // 2,
                                tag.centery - tag_text.get_height() // 2))

        surface.blit(name_font.render(message.author, True, TEXT_DARK),
                     (text_x, 8))

        y = 8 + name_font.get_linesize() + 2
        for line in lines:
            surface.blit(text_font.render(line, True, TEXT_DARK), (text_x, y))
            y += line_h

        if message.dead:
            ghost = tag_font.render("FANTASMA", True, (70, 74, 86))
            surface.blit(ghost, (width - ghost.get_width() - 12, 10))

        message.surface = surface
        message.height = height
        return surface

    # -- drawing -----------------------------------------------------------
    def draw(self, surface):
        if not self.is_open:
            return

        pg.draw.rect(surface, PANEL_BG, self.panel_rect, border_radius=16)
        pg.draw.rect(surface, PANEL_BORDER, self.panel_rect, width=4,
                     border_radius=16)
        pg.draw.rect(surface, HEADER_BG, self.header_rect,
                     border_top_left_radius=16, border_top_right_radius=16)

        title = self._font(20).render("DISCUSSÃƒO", True, TEXT_LIGHT)
        surface.blit(title, (self.header_rect.x + 16,
                             self.header_rect.centery - title.get_height() // 2))
        seconds = self.seconds_left()
        if seconds is not None:
            clock = self._font(20).render("%ss" % seconds, True,
                                          RED if seconds <= 5 else TEXT_LIGHT)
            surface.blit(clock, (self.header_rect.right - clock.get_width() - 16,
                                 self.header_rect.centery - clock.get_height() // 2))

        self._draw_messages(surface)
        self._draw_input(surface)

    def _draw_messages(self, surface):
        view = self.list_rect
        pg.draw.rect(surface, HEADER_BG, view.inflate(8, 8), border_radius=10)

        if not self.messages:
            hint = self._font(15).render("NinguÃ©m falou ainda...", True,
                                         TEXT_MUTED)
            surface.blit(hint, (view.centerx - hint.get_width() // 2,
                                view.centery - hint.get_height() // 2))
            return

        content_h = self.content_height()
        limit = max(0, content_h - view.height)
        self.scroll_px = min(self.scroll_px, limit)
        # top of the content, in screen coordinates
        y = (view.bottom - content_h if content_h < view.height
             else view.y - limit + self.scroll_px)

        previous_clip = surface.get_clip()
        surface.set_clip(view)
        for message in self.messages:
            bubble = self._message_surface(message)
            if y + message.height >= view.y and y <= view.bottom:
                surface.blit(bubble, (view.x, y))
            y += message.height + 8
        surface.set_clip(previous_clip)

        if limit > 0:
            track = pg.Rect(view.right - 8, view.y, 6, view.height)
            pg.draw.rect(surface, HEADER_BG, track, border_radius=3)
            thumb_h = max(30, int(view.height * view.height / float(content_h)))
            travel = view.height - thumb_h
            offset = int(travel * (1 - self.scroll_px / float(limit)))
            pg.draw.rect(surface, SCROLLBAR_FG,
                         pg.Rect(track.x, track.y + offset, track.width, thumb_h),
                         border_radius=3)

    def _draw_input(self, surface):
        font = self._font(16)
        typing = self.can_type

        # character counter, right above the send button
        counter = self._font(14).render("%d/%d" % (len(self.input_text),
                                                   CHAT_MAX_CHARS),
                                        True, TEXT_MUTED)
        surface.blit(counter, (self.send_rect.right - counter.get_width(),
                               self.input_rect.top - 6 - counter.get_height()))

        pg.draw.rect(surface, INPUT_BG if typing else INPUT_BG_OFF,
                     self.input_rect, border_radius=12)
        pg.draw.rect(surface, PANEL_BORDER, self.input_rect, width=3,
                     border_radius=12)

        if typing:
            text = font.render(self.input_text, True, TEXT_DARK)
            caret_x = font.size(self.input_text[:self.caret])[0]
            # keep the caret inside the box on long messages
            shift = max(0, caret_x - (self.input_rect.width - 24))
            clip = surface.get_clip()
            surface.set_clip(self.input_rect.inflate(-16, -8))
            surface.blit(text, (self.input_rect.x + 12 - shift,
                                self.input_rect.centery - text.get_height() // 2))
            if (self._now() // 500) % 2 == 0:
                x = self.input_rect.x + 12 + caret_x - shift
                pg.draw.line(surface, TEXT_DARK, (x, self.input_rect.y + 10),
                             (x, self.input_rect.bottom - 10), 2)
            surface.set_clip(clip)
        else:
            hint = font.render("VocÃª estÃ¡ morto - sÃ³ pode observar", True,
                               (110, 114, 126))
            surface.blit(hint, (self.input_rect.x + 12,
                                self.input_rect.centery - hint.get_height() // 2))

        enabled = typing and bool(self.input_text.strip())
        pg.draw.rect(surface, SEND_BG if enabled else SEND_BG_OFF,
                     self.send_rect, border_radius=12)
        pg.draw.rect(surface, PANEL_BORDER, self.send_rect, width=3,
                     border_radius=12)
        label = self._font(17).render("Send", True, TEXT_LIGHT)
        surface.blit(label, (self.send_rect.centerx - label.get_width() // 2,
                             self.send_rect.centery - label.get_height() // 2))

    # -- bots --------------------------------------------------------------
    def alive_bots(self):
        """(name, colour) of every bot still alive, for the responder to use."""
        crew = []
        for bot in getattr(self.game, "bots", []):
            if getattr(bot, "alive_status", False):
                crew.append((getattr(bot, "bot_name", bot.bot_colour),
                             bot.bot_colour))
        return crew

    def _demo_chatter(self):
        """Placeholder chatter, replaced as soon as a responder is set."""
        crew = self.alive_bots()
        random.shuffle(crew)
        delay = 1200
        for name, colour in crew[:5]:
            self.schedule_message(name, colour, random.choice(DEMO_LINES), delay)
            delay += random.randint(1200, 2600)
