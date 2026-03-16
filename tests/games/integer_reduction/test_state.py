"""Tests for integer reduction state objects."""

import pytest

from atomheart.games.integer_reduction import IntegerReductionState


def test_state_accepts_positive_values() -> None:
    """Positive integers should build valid states."""
    state = IntegerReductionState(10)
    assert state.value == 10


@pytest.mark.parametrize("value", [0, -1])
def test_state_rejects_non_positive_values(value: int) -> None:
    """Values below one should be rejected."""
    with pytest.raises(ValueError, match=">= 1"):
        IntegerReductionState(value)


@pytest.mark.parametrize("value", [True, False, 1.5, "3"])
def test_state_rejects_non_int_values(value: object) -> None:
    """Non-integer values, including bools, should be rejected."""
    with pytest.raises(TypeError, match="must be an int"):
        IntegerReductionState(value)  # type: ignore[arg-type]


def test_tag_matches_value() -> None:
    """The state tag should be the integer value itself."""
    state = IntegerReductionState(7)
    assert state.tag == 7


def test_game_over_only_at_one() -> None:
    """Only value one should be terminal."""
    assert IntegerReductionState(1).is_game_over() is True
    assert IntegerReductionState(2).is_game_over() is False
