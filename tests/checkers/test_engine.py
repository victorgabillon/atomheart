"""Rule-engine tests for checkers."""

import pytest
import valanga

from atomheart.games.checkers.apply import apply_move
from atomheart.games.checkers.dynamics import CheckersDynamics
from atomheart.games.checkers.generation import generate_legal_moves
from atomheart.games.checkers.geometry import (
    CAPTURE_TABLES,
    NE,
    NW,
    ROW_OF_SQ32,
    SE,
    SW,
)
from atomheart.games.checkers.move import is_capture
from atomheart.games.checkers.reversible import CheckersReversibleDynamics
from atomheart.games.checkers.rules import CheckersRules
from atomheart.games.checkers.state import CheckersState


def test_initial_position_has_legal_moves() -> None:
    """Initial position should generate non-empty legal moves for white."""
    moves = generate_legal_moves(CheckersState.standard(), CheckersRules())
    assert len(moves) > 0


def test_forced_capture_filters_quiets() -> None:
    """When captures exist, legal actions should be captures only."""
    state = CheckersState(
        wm=1 << 13,
        wk=0,
        bm=1 << 17,
        bk=0,
        turn=valanga.Color.WHITE,
    )
    moves = generate_legal_moves(state, CheckersRules(forced_capture=True))
    assert len(moves) >= 1
    assert all(is_capture(move) for move in moves)


def test_promotion_on_quiet_move() -> None:
    """White man moving into last rank should carry promotes=True."""
    state = CheckersState(
        wm=1 << 27,
        wk=0,
        bm=0,
        bk=0,
        turn=valanga.Color.WHITE,
    )
    moves = generate_legal_moves(state, CheckersRules())
    assert any(move[-1] for move in moves)


def test_step_detects_no_moves_terminal() -> None:
    """A move that leaves opponent with no legal actions should end the game."""
    dynamics = CheckersDynamics()
    state = CheckersState(
        wm=1 << 13,
        wk=0,
        bm=1 << 0,
        bk=0,
        turn=valanga.Color.WHITE,
    )

    for move in dynamics.legal_actions(state).get_all():
        transition = dynamics.step(state, move)
        if transition.is_over:
            assert transition.over_event is not None
            return

    pytest.fail("Expected at least one legal move that ends the game.")


def test_step_rejects_illegal_move_geometry() -> None:
    """Engine should reject structurally valid but geometrically illegal moves."""
    dynamics = CheckersDynamics()
    state = CheckersState(
        wm=1 << 13,
        wk=0,
        bm=0,
        bk=0,
        turn=valanga.Color.WHITE,
    )
    with pytest.raises(ValueError):
        dynamics.step(state, (13, (20,), (), False))


def test_step_rejects_quiet_when_capture_forced() -> None:
    """Engine should reject quiet moves when a capture exists and is mandatory."""
    state = CheckersState(
        wm=1 << 13,
        wk=0,
        bm=1 << 17,
        bk=0,
        turn=valanga.Color.WHITE,
    )

    all_moves = generate_legal_moves(state, CheckersRules(forced_capture=False))
    quiet_move = next((move for move in all_moves if not is_capture(move)), None)
    assert quiet_move is not None

    dynamics = CheckersDynamics(rules=CheckersRules(forced_capture=True))
    with pytest.raises(ValueError, match="Capture is mandatory"):
        dynamics.step(state, quiet_move)


def test_apply_move_updates_bitboards_for_quiet_move() -> None:
    """Applying a legal quiet move should move only the active piece and flip turn."""
    state = CheckersState(
        wm=1 << 13,
        wk=0,
        bm=0,
        bk=0,
        turn=valanga.Color.WHITE,
    )
    rules = CheckersRules()
    legal_move = generate_legal_moves(state, rules)[0]

    next_state = apply_move(state, legal_move, rules)

    assert next_state.turn == valanga.Color.BLACK
    assert next_state.bm == 0 and next_state.bk == 0
    assert (next_state.wm | next_state.wk) == (1 << legal_move[1][-1])
    assert ((next_state.wm | next_state.wk) & (1 << legal_move[0])) == 0


def test_reversible_push_pop_roundtrip() -> None:
    """Push then pop should restore original state exactly."""
    dynamics = CheckersDynamics()
    start = CheckersState(
        wm=1 << 13,
        wk=0,
        bm=0,
        bk=0,
        turn=valanga.Color.WHITE,
    )
    move = generate_legal_moves(start, dynamics.rules)[0]

    reversible = CheckersReversibleDynamics(dynamics=dynamics, state=start)
    undo = reversible.push(move)
    reversible.pop(undo)

    assert reversible.state == start


def test_apply_move_removes_captured_piece() -> None:
    """Applying a generated capture should remove the jumped opponent piece."""
    rules = CheckersRules(forced_capture=True)
    state = CheckersState(
        wm=1 << 13,
        wk=0,
        bm=1 << 17,
        bk=0,
        turn=valanga.Color.WHITE,
    )
    capture = generate_legal_moves(state, rules)[0]
    assert is_capture(capture)

    next_state = apply_move(state, capture, rules)

    assert next_state.bm == 0 and next_state.bk == 0
    assert (next_state.wm | next_state.wk) == (1 << capture[1][-1])


def _find_crowning_continuation_case() -> CheckersState:
    """Build a position where white crowns on first capture and can continue only as king."""
    for start_sq in range(32):
        for first_dir in (SW, SE):
            first_edge = CAPTURE_TABLES[first_dir][start_sq]
            if first_edge.jumped == -1 or ROW_OF_SQ32[first_edge.landing] != 7:
                continue

            for second_dir in (NW, NE):
                second_edge = CAPTURE_TABLES[second_dir][first_edge.landing]
                if second_edge.jumped == -1:
                    continue

                occupied = {
                    start_sq,
                    first_edge.jumped,
                    second_edge.jumped,
                }
                if second_edge.landing in occupied:
                    continue

                return CheckersState(
                    wm=1 << start_sq,
                    wk=0,
                    bm=(1 << first_edge.jumped) | (1 << second_edge.jumped),
                    bk=0,
                    turn=valanga.Color.WHITE,
                )

    raise AssertionError("Could not construct crowning-continuation scenario.")


def test_crowning_ends_turn_rule_controls_capture_continuation() -> None:
    """Crowning rule should control whether post-crown capture continuation is legal."""
    state = _find_crowning_continuation_case()

    end_turn_moves = generate_legal_moves(
        state, CheckersRules(forced_capture=True, crowning_ends_turn=True)
    )
    continue_moves = generate_legal_moves(
        state, CheckersRules(forced_capture=True, crowning_ends_turn=False)
    )

    assert any(move[3] and len(move[2]) == 1 for move in end_turn_moves)
    assert any(move[3] and len(move[2]) >= 2 for move in continue_moves)
