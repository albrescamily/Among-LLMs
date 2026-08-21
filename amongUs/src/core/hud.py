"""The heads-up display.

For now: the task checklist in the top-left corner. Nine rows, each green while
the task is outstanding and white once it is done.

Seven of the nine ask the same question -- has this task's counter been spent --
but two do not, and the table carries that rather than hiding it. Deciding the
colours is separated from drawing them so the decision can be tested without a
display.
"""

from collections import namedtuple

import pygame
import pygame as pg

from core.settings import FONT, GREEN, WHITE

# guard      the attribute that says whether the task is done
# done_when  the value of that attribute meaning "done"
# title      the attribute on Task holding the label
# y          where the row sits on screen
MissionRow = namedtuple("MissionRow", "guard done_when title y")

MISSION_ROWS = (
    # NOTE: the lights row is inverted and reads a bool, not a counter. Every
    # other row asks "has the counter been spent"; this one asks "is it dark".
    MissionRow("night", True, "turn_on_the_lights_task_title", 50),

    MissionRow("reboot_wifi_task_play_count", 1, "reboot_the_wifi_task_title", 75),

    # NOTE: guarded by a lever's sel_count rather than a task_play_count, unlike
    # its seven neighbours. Preserved as found.
    MissionRow("garbage_liver_Up_sel_count", 1, "empty_the_garbage_task_title", 100),

    MissionRow("stabilize_task_play_count", 1, "stabilize_nav_task_title", 125),
    MissionRow("electricity_wire_task_play_count", 1,
               "fix_electircity_wires_task_title", 150),
    MissionRow("divert_power_to_reactor_task_play_count", 1,
               "divert_power_to_reactor_task_title", 175),
    MissionRow("align_engine_output_task_play_count", 1,
               "align_engine_output_task_title", 200),
    MissionRow("fuel_engine_task_play_count", 1, "fuel_engine_task_title", 225),
    MissionRow("clear_asteroid_task_play_count", 1, "clear_asteroids_task_title", 250),
)


def mission_row_colours(game):
    """What the checklist says right now: [(text, colour, y), ...].

    Pure, so the colour rules can be tested without rendering anything.
    """
    rows = []
    for row in MISSION_ROWS:
        done = getattr(game, row.guard) == row.done_when
        rows.append((getattr(game.tasks, row.title),
                     WHITE if done else GREEN,
                     row.y))
    return rows


def draw_missions_box(game):
    """Blit the checklist over a dimmed panel."""
    font = pygame.font.Font(FONT, 18)
    panel = pg.Surface((415, 235)).convert_alpha()
    panel.fill((0, 0, 0, 96))
    game.screen.blit(panel, (10, 45))

    for text, colour, y in mission_row_colours(game):
        game.screen.blit(font.render(text, True, colour), (20, y))
