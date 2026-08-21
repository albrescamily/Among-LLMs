"""Every attribute the wire touches still exists on a real Game.

multiplayer/world_sync.py reaches into about forty-six Game attributes by name.
Its own tests run against a SimpleNamespace, which will happily accept whatever
name it is given -- so renaming an attribute on Game leaves world_sync's tests
green and breaks multiplayer only, at the point where a second player joins.

This is the check that makes that rename visible, by asserting the names
world_sync uses against an actual constructed Game.
"""

import ast
from os import path

import pytest

SRC = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'src')
WORLD_SYNC = path.join(SRC, "multiplayer", "world_sync.py")

# Locals of apply_row, not attributes of the game it was handed.
NOT_GAME_ATTRIBUTES = {"Players"}


def attributes_used_on(source, parameter="self"):
    """Every `<parameter>.<name>` in the module, as a set of names."""
    tree = ast.parse(source)
    return {node.attr for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == parameter}


def wire_attributes():
    used = attributes_used_on(open(WORLD_SYNC, encoding="utf-8").read())
    return sorted(used - NOT_GAME_ATTRIBUTES)


def test_world_sync_touches_the_surface_we_think_it_does():
    """A canary on the count, so a big change here is noticed rather than absorbed."""
    assert len(wire_attributes()) > 30


@pytest.mark.parametrize("name", wire_attributes())
def test_a_real_game_has_the_attribute_the_wire_writes(booted_game, name):
    assert hasattr(booted_game, name), (
        f"multiplayer/world_sync.py writes game.{name}, but a constructed Game "
        f"has no such attribute -- multiplayer will break on the frame this runs"
    )
