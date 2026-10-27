"""Pure chess factory introspection with optional native annotations."""

from annotationlib import Format, get_annotations
from typing import get_type_hints

import chess

from atomheart.games.chess.board import BoardChi
from atomheart.games.chess.board.factory import create_board_chi, create_rust_board
from atomheart.games.chess.move.move_factory import MoveFactory, create_move
from atomheart.games.chess.state import ChessState


def test_pure_chess_annotations_resolve() -> None:
    """Pure factories and state wrappers expose runtime-resolvable types."""
    assert get_type_hints(create_board_chi)["return"] is BoardChi
    assert get_type_hints(create_move)["return"] is chess.Move
    assert "board" in get_type_hints(ChessState)
    assert "move_uci" in get_type_hints(MoveFactory.__call__)


def test_optional_factory_keeps_string_annotations() -> None:
    """Inspecting a lazy Rust factory need not evaluate optional native names."""
    assert create_rust_board.__annotations__["return"] == "RustyBoardChi"
    assert (
        get_annotations(create_rust_board, format=Format.STRING)["return"]
        == "RustyBoardChi"
    )
