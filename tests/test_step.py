"""Regression tests for ChessDynamics.step behavior.

These tests ensure:
1. step() does NOT call termination() on non-terminal positions.
2. step() correctly marks terminal transitions.
3. Behavior is consistent for both rust and python boards.
"""

import chess
import pytest

from atomheart import ChessDynamics, ChessState
from atomheart.board import IBoard, create_board
from atomheart.board.utils import FenPlusHistory


@pytest.mark.parametrize("use_rust_boards", [False, True])
def test_step_non_terminal_position(use_rust_boards: bool) -> None:
    """step() on a normal move must not crash and must not report termination."""
    board: IBoard = create_board(
        use_rust_boards=use_rust_boards,
        fen_with_history=FenPlusHistory(current_fen=chess.STARTING_FEN),
    )

    state = ChessState(board=board)
    dyn = ChessDynamics()

    action = dyn.action_from_name(state, "e2e4")

    # IMPORTANT: this used to crash due to termination() being called
    transition = dyn.step(state, action)

    assert transition.next_state is not None
    assert transition.is_over is False
    assert transition.over_event is None

    # Make sure resulting board is still non-terminal
    assert transition.next_state.board.is_game_over() is False


@pytest.mark.parametrize("use_rust_boards", [False, True])
def test_step_terminal_position_mate_in_one(use_rust_boards: bool) -> None:
    """step() must correctly mark terminal positions (mate in 1)."""
    fen_mate_in_one = (
        "1rb5/4r3/3p1npb/3kp1P1/1P3P1P/5nR1/2Q1BK2/bN4NR w - - 3 61"  # Qh7#
    )
    board: IBoard = create_board(
        use_rust_boards=use_rust_boards,
        fen_with_history=FenPlusHistory(current_fen=fen_mate_in_one),
    )

    state = ChessState(board=board)
    dyn = ChessDynamics()

    action = dyn.action_from_name(state, "c2c4")  # Qh7#

    transition = dyn.step(state, action)

    assert transition.next_state is not None
    assert transition.is_over is True
    assert transition.next_state.board.is_game_over() is True


@pytest.mark.parametrize("use_rust_boards", [False, True])
def test_step_multiple_moves_sequence(use_rust_boards: bool) -> None:
    """Ensure multiple successive steps behave correctly."""
    board: IBoard = create_board(
        use_rust_boards=use_rust_boards,
        fen_with_history=FenPlusHistory(current_fen=chess.STARTING_FEN),
    )

    state = ChessState(board=board)
    dyn = ChessDynamics()

    moves = ["e2e4", "e7e5", "g1f3", "b8c6"]

    current_state = state

    for move in moves:
        action = dyn.action_from_name(current_state, move)
        transition = dyn.step(current_state, action)

        assert transition.next_state is not None
        assert transition.is_over is False

        current_state = transition.next_state

    assert current_state.board.is_game_over() is False
