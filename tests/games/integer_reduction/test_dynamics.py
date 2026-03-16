"""Tests for integer reduction dynamics."""

from __future__ import annotations

from functools import lru_cache

import pytest
from valanga.over_event import HowOver, Winner

from atomheart.games.integer_reduction import (
    IntegerReductionDynamics,
    IntegerReductionState,
)


@pytest.mark.parametrize(
    ("value", "expected_actions"),
    [
        (1, []),
        (2, ["dec1", "half"]),
        (3, ["dec1"]),
        (10, ["dec1", "half"]),
    ],
)
def test_legal_actions(
    value: int,
    expected_actions: list[str],
) -> None:
    """Legal actions should match the parity-sensitive rules."""
    dynamics = IntegerReductionDynamics()
    state = IntegerReductionState(value)
    generator = dynamics.legal_actions(state)

    assert list(generator.all_generated_keys or []) == expected_actions
    assert generator.get_all() == expected_actions
    assert generator.more_than_one() is (len(expected_actions) > 1)


def test_branch_key_generator_copy_with_reset() -> None:
    """A copied generator should restart iteration from the beginning."""
    dynamics = IntegerReductionDynamics()
    generator = dynamics.legal_actions(IntegerReductionState(2))

    assert next(generator) == "dec1"
    assert generator.copy_with_reset().get_all() == ["dec1", "half"]


@pytest.mark.parametrize(
    ("value", "action", "expected_value", "expected_is_over"),
    [
        (10, "dec1", 9, False),
        (10, "half", 5, False),
        (2, "half", 1, True),
        (2, "dec1", 1, True),
    ],
)
def test_step_behavior(
    value: int,
    action: str,
    expected_value: int,
    expected_is_over: bool,
) -> None:
    """Transitions should update the integer and terminal metadata correctly."""
    dynamics = IntegerReductionDynamics()
    transition = dynamics.step(IntegerReductionState(value), action)

    assert transition.next_state == IntegerReductionState(expected_value)
    assert transition.modifications is None
    assert transition.is_over is expected_is_over
    assert transition.info == {"action": action}

    if expected_is_over:
        assert transition.over_event is not None
        assert transition.over_event.how_over == HowOver.DRAW
        assert transition.over_event.who_is_winner == Winner.NO_KNOWN_WINNER
        assert transition.over_event.termination == "reached_one"
    else:
        assert transition.over_event is None


def test_step_rejects_illegal_action() -> None:
    """Illegal but well-formed actions should raise ``ValueError``."""
    dynamics = IntegerReductionDynamics()
    with pytest.raises(ValueError, match="Illegal integer reduction action"):
        dynamics.step(IntegerReductionState(3), "half")


def test_action_from_name_rejects_unknown_name() -> None:
    """Unknown action names should be rejected."""
    dynamics = IntegerReductionDynamics()
    with pytest.raises(ValueError, match="Unknown integer reduction action name"):
        dynamics.action_from_name(IntegerReductionState(10), "triple")


def test_action_from_name_rejects_illegal_known_name() -> None:
    """Known action names should still be validated against the state."""
    dynamics = IntegerReductionDynamics()
    with pytest.raises(ValueError, match="No legal integer reduction action named"):
        dynamics.action_from_name(IntegerReductionState(3), "half")


def test_step_rejects_malformed_action_key() -> None:
    """Malformed branch keys should raise ``TypeError``."""
    dynamics = IntegerReductionDynamics()
    with pytest.raises(TypeError, match="must be strings"):
        dynamics.step(IntegerReductionState(10), 123)


@pytest.mark.parametrize("value", [2, 3, 10])
def test_action_name_roundtrip(value: int) -> None:
    """Legal actions should round-trip through their canonical string names."""
    dynamics = IntegerReductionDynamics()
    state = IntegerReductionState(value)

    for action in dynamics.legal_actions(state).get_all():
        name = dynamics.action_name(state, action)
        parsed = dynamics.action_from_name(state, name)
        assert parsed == action


def test_known_optimal_step_counts() -> None:
    """The game tree should match known exact distances to value one."""
    dynamics = IntegerReductionDynamics()

    @lru_cache
    def exact_steps(value: int) -> int:
        state = IntegerReductionState(value)
        if state.is_game_over():
            return 0
        return 1 + min(
            exact_steps(dynamics.step(state, action).next_state.value)
            for action in dynamics.legal_actions(state).get_all()
        )

    assert exact_steps(1) == 0
    assert exact_steps(2) == 1
    assert exact_steps(3) == 2
    assert exact_steps(4) == 2
    assert exact_steps(5) == 3
    assert exact_steps(6) == 3
    assert exact_steps(7) == 4
    assert exact_steps(8) == 3
    assert exact_steps(10) == 4
