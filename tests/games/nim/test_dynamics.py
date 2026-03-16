"""Tests for Nim dynamics."""

from __future__ import annotations

from functools import lru_cache

import pytest
import valanga
from valanga.over_event import HowOver, Winner

from atomheart.games.nim import NimDynamics, NimState


@pytest.mark.parametrize(
    ("stones", "turn", "expected_actions"),
    [
        (0, valanga.Color.WHITE, []),
        (1, valanga.Color.WHITE, [1]),
        (2, valanga.Color.WHITE, [1, 2]),
        (3, valanga.Color.WHITE, [1, 2, 3]),
        (10, valanga.Color.BLACK, [1, 2, 3]),
    ],
)
def test_legal_actions(
    stones: int,
    turn: valanga.Color,
    expected_actions: list[int],
) -> None:
    """Legal actions should match the available stone count."""
    dynamics = NimDynamics()
    state = NimState(stones, turn)
    generator = dynamics.legal_actions(state)

    assert list(generator.all_generated_keys or []) == expected_actions
    assert generator.get_all() == expected_actions
    assert generator.more_than_one() is (len(expected_actions) > 1)


def test_generator_copy_with_reset() -> None:
    """A copied generator should restart iteration from the beginning."""
    dynamics = NimDynamics()
    generator = dynamics.legal_actions(NimState(3, valanga.Color.WHITE))

    assert next(generator) == 1
    assert next(generator) == 2
    assert generator.copy_with_reset().get_all() == [1, 2, 3]


def test_action_name_roundtrip() -> None:
    """Legal actions should round-trip through canonical string names."""
    dynamics = NimDynamics()
    state = NimState(3, valanga.Color.WHITE)

    for action in dynamics.legal_actions(state).get_all():
        name = dynamics.action_name(state, action)
        parsed = dynamics.action_from_name(state, name)
        assert parsed == action


@pytest.mark.parametrize(
    (
        "state",
        "action",
        "expected_state",
        "expected_is_over",
        "expected_winner",
    ),
    [
        (
            NimState(4, valanga.Color.WHITE),
            1,
            NimState(3, valanga.Color.BLACK),
            False,
            None,
        ),
        (
            NimState(4, valanga.Color.WHITE),
            3,
            NimState(1, valanga.Color.BLACK),
            False,
            None,
        ),
        (
            NimState(1, valanga.Color.WHITE),
            1,
            NimState(0, valanga.Color.BLACK),
            True,
            Winner.WHITE,
        ),
        (
            NimState(2, valanga.Color.BLACK),
            2,
            NimState(0, valanga.Color.WHITE),
            True,
            Winner.BLACK,
        ),
    ],
)
def test_step_behavior(
    state: NimState,
    action: int,
    expected_state: NimState,
    expected_is_over: bool,
    expected_winner: Winner | None,
) -> None:
    """Transitions should update stones, turn, and winner metadata correctly."""
    dynamics = NimDynamics()
    transition = dynamics.step(state, action)

    assert transition.next_state == expected_state
    assert transition.modifications is None
    assert transition.is_over is expected_is_over
    assert transition.info == {"action": action}

    if expected_is_over:
        assert transition.over_event is not None
        assert transition.over_event.how_over == HowOver.WIN
        assert transition.over_event.who_is_winner == expected_winner
        assert transition.over_event.termination == "last_stone"
    else:
        assert transition.over_event is None


@pytest.mark.parametrize(
    ("state", "action"),
    [
        (NimState(1, valanga.Color.WHITE), 2),
        (NimState(2, valanga.Color.WHITE), 3),
    ],
)
def test_step_rejects_illegal_actions(state: NimState, action: int) -> None:
    """Illegal but well-formed actions should raise ``ValueError``."""
    dynamics = NimDynamics()
    with pytest.raises(ValueError, match="Illegal Nim action"):
        dynamics.step(state, action)


@pytest.mark.parametrize("action", ["1", 1.0, True, 4])
def test_step_rejects_malformed_action_keys(action: object) -> None:
    """Malformed branch keys should raise ``TypeError``."""
    dynamics = NimDynamics()
    with pytest.raises(TypeError, match="Nim actions must"):
        dynamics.step(NimState(3, valanga.Color.WHITE), action)


@pytest.mark.parametrize("name", ["4", "remove1"])
def test_action_from_name_rejects_unknown_names(name: str) -> None:
    """Unknown action names should be rejected."""
    dynamics = NimDynamics()
    with pytest.raises(ValueError, match="Unknown Nim action name"):
        dynamics.action_from_name(NimState(3, valanga.Color.WHITE), name)


def test_action_from_name_rejects_illegal_known_name() -> None:
    """Known action names should still be validated against the state."""
    dynamics = NimDynamics()
    with pytest.raises(ValueError, match="No legal Nim action named"):
        dynamics.action_from_name(NimState(2, valanga.Color.WHITE), "3")


def test_losing_positions_are_multiples_of_four() -> None:
    """Optimal play should lose exactly on multiples of four stones."""
    dynamics = NimDynamics()

    @lru_cache
    def is_winning(stones: int, turn: valanga.Color) -> bool:
        state = NimState(stones, turn)
        if state.is_game_over():
            return False

        for action in dynamics.legal_actions(state).get_all():
            next_state = dynamics.step(state, action).next_state
            if not is_winning(next_state.stones, next_state.turn):
                return True
        return False

    for turn in (valanga.Color.WHITE, valanga.Color.BLACK):
        for stones in range(13):
            assert is_winning(stones, turn) is (stones % 4 != 0)
