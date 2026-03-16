"""Tests for reversible integer reduction dynamics."""

from atomheart.games.integer_reduction import (
    IntegerReductionDynamics,
    IntegerReductionReversibleDynamics,
    IntegerReductionState,
)


def test_reversible_push_pop_roundtrip() -> None:
    """Push then pop should restore the original integer state."""
    dynamics = IntegerReductionDynamics()
    start = IntegerReductionState(10)
    reversible = IntegerReductionReversibleDynamics(dynamics=dynamics, state=start)

    undo = reversible.push("half")
    assert reversible.state == IntegerReductionState(5)

    reversible.pop(undo)
    assert reversible.state == start


def test_reversible_legal_actions_follow_current_state() -> None:
    """Reversible legal actions should track the mutable current value."""
    dynamics = IntegerReductionDynamics()
    reversible = IntegerReductionReversibleDynamics(
        dynamics=dynamics,
        state=IntegerReductionState(2),
    )

    assert reversible.legal_actions().get_all() == ["dec1", "half"]

    undo = reversible.push("half")
    assert reversible.state == IntegerReductionState(1)
    assert reversible.legal_actions().get_all() == []

    reversible.pop(undo)
    assert reversible.state == IntegerReductionState(2)


def test_reversible_action_name_roundtrip() -> None:
    """Reversible dynamics should expose the same canonical action names."""
    dynamics = IntegerReductionDynamics()
    reversible = IntegerReductionReversibleDynamics(
        dynamics=dynamics,
        state=IntegerReductionState(10),
    )

    assert reversible.action_name("half") == "half"
    assert reversible.action_from_name("half") == "half"
