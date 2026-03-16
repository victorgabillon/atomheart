"""Tests for Nim state objects."""

import pytest
import valanga

from atomheart.games.nim import NimState


def test_state_accepts_valid_values() -> None:
    """Valid stones and turn should build a state."""
    state = NimState(4, valanga.Color.WHITE)
    assert state.stones == 4
    assert state.turn == valanga.Color.WHITE


@pytest.mark.parametrize("stones", [-1, -3])
def test_state_rejects_negative_stones(stones: int) -> None:
    """Negative stone counts should be rejected."""
    with pytest.raises(ValueError, match=">= 0"):
        NimState(stones, valanga.Color.WHITE)


@pytest.mark.parametrize("stones", [True, False, 1.5, "3"])
def test_state_rejects_non_int_stones(stones: object) -> None:
    """Non-integer stones, including bools, should be rejected."""
    with pytest.raises(TypeError, match="must be an int"):
        NimState(stones, valanga.Color.WHITE)  # type: ignore[arg-type]


def test_state_rejects_invalid_turn() -> None:
    """Turn must be a Valanga color."""
    with pytest.raises(TypeError, match=r"turn must be valanga\.Color"):
        NimState(3, "WHITE")  # type: ignore[arg-type]


def test_terminal_detection() -> None:
    """Only zero stones should be terminal."""
    assert NimState(0, valanga.Color.WHITE).is_game_over() is True
    assert NimState(1, valanga.Color.BLACK).is_game_over() is False


def test_tag_includes_stones_and_turn() -> None:
    """The tag should distinguish states with the same stones and different turns."""
    white_state = NimState(4, valanga.Color.WHITE)
    black_state = NimState(4, valanga.Color.BLACK)

    assert white_state.tag == (4, valanga.Color.WHITE)
    assert black_state.tag == (4, valanga.Color.BLACK)
    assert white_state.tag != black_state.tag
