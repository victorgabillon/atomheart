"""
Defines a factory for creating chess moves, supporting both standard and Rust-based implementations.
"""

from typing import Protocol

import chess
import shakmaty_python_binding

from atomheart.board.iboard import IBoard
from atomheart.move.imove import IMove

from .board import RustyBoardChi
from .move import MoveUci


class MoveFactory(Protocol):
    """Protocol for a move factory."""

    def __call__(self, move_uci: MoveUci, board: IBoard | None = None) -> IMove:
        """
        Create a move given its UCI string and an optional board.
        """
        ...


def create_move_factory(
    use_rust_boards: bool,
) -> MoveFactory:
    """Creates a move factory.

    Args:
        use_rust_boards (bool): Whether to use Rust-based boards.

    Returns:
        MoveFactory: The created move factory.
    """
    move_factory: MoveFactory

    # TODO(victor): can we go back to the not test version without the assert? generics or just typos? See issue #24 for more details.
    move_factory = create_rust_move_test_2 if use_rust_boards else create_move
    return move_factory


def create_rust_move(
    move_uci: MoveUci, board: RustyBoardChi | None = None
) -> shakmaty_python_binding.MyMove:
    """Creates a Rust-based move.
    Args:
        move_uci (moveUci): The UCI string of the move.
        board (RustyBoardChi | None, optional): The board on which the move is made. Defaults to None.
    Returns:
        shakmaty_python_binding.MyMove: The created Rust-based move.
    """
    assert board is not None
    return shakmaty_python_binding.MyMove(move_uci, board.chess_)


def create_rust_move_test_2(
    move_uci: MoveUci, board: IBoard | None = None
) -> shakmaty_python_binding.MyMove:
    """Creates a Rust-based move for testing purposes.
    Args:
        move_uci (moveUci): The UCI string of the move.
        board (IBoard | None, optional): The board on which the move is made. Defaults to None.
    Returns:
        shakmaty_python_binding.MyMove: The created Rust-based move.
    """
    assert isinstance(board, RustyBoardChi)
    return shakmaty_python_binding.MyMove(move_uci, board.chess_)



def create_rust_move_test(move_uci: MoveUci, board: IBoard | None = None) -> chess.Move:
    """Creates a Rust-based move for testing purposes.
    Args:
        move_uci (moveUci): The UCI string of the move.
        board (IBoard | None, optional): The board on which the move is made. Defaults to None.
    Returns:
        chess.Move: The created Rust-based move.
    """
    assert board is not None
    return chess.Move.from_uci(move_uci)


def create_move(move_uci: MoveUci, board: IBoard | None = None) -> chess.Move:  # pylint: disable=unused-argument
    """Creates a standard chess move.
    Args:
        move_uci (moveUci): The UCI string of the move.
        board (IBoard | None, optional): The board on which the move is made. Defaults to None.
    Returns:
        chess.Move: The created standard chess move.
    """
    return chess.Move.from_uci(move_uci)
