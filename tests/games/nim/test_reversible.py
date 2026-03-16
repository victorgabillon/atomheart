"""Tests for reversible Nim dynamics."""

import valanga

from atomheart.games.nim import NimDynamics, NimReversibleDynamics, NimState


def test_reversible_push_pop_roundtrip() -> None:
    """Push then pop should restore the full original Nim state."""
    dynamics = NimDynamics()
    start = NimState(4, valanga.Color.WHITE)
    reversible = NimReversibleDynamics(dynamics=dynamics, state=start)

    first_undo = reversible.push(3)
    assert reversible.state == NimState(1, valanga.Color.BLACK)

    second_undo = reversible.push(1)
    assert reversible.state == NimState(0, valanga.Color.WHITE)

    reversible.pop(second_undo)
    assert reversible.state == NimState(1, valanga.Color.BLACK)

    reversible.pop(first_undo)
    assert reversible.state == start


def test_reversible_legal_actions_track_current_state() -> None:
    """Reversible legal actions should follow the mutable current state."""
    dynamics = NimDynamics()
    reversible = NimReversibleDynamics(
        dynamics=dynamics,
        state=NimState(2, valanga.Color.BLACK),
    )

    assert reversible.legal_actions().get_all() == [1, 2]

    undo = reversible.push(2)
    assert reversible.state == NimState(0, valanga.Color.WHITE)
    assert reversible.legal_actions().get_all() == []

    reversible.pop(undo)
    assert reversible.state == NimState(2, valanga.Color.BLACK)


def test_reversible_action_name_roundtrip() -> None:
    """Reversible dynamics should expose canonical action names and parsing."""
    dynamics = NimDynamics()
    reversible = NimReversibleDynamics(
        dynamics=dynamics,
        state=NimState(4, valanga.Color.WHITE),
    )

    assert reversible.action_name(3) == "3"
    assert reversible.action_from_name("3") == 3
