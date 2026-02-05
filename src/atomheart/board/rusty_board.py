"""Module: rusty_board.

Defines a Rust-based chess board implementation using shakmaty_python_binding.
"""

from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any, Self, no_type_check

import chess
import shakmaty_python_binding
from valanga import Color

from atomheart.board.board_modification import (
    BoardModificationP,
    BoardModificationRust,
)
from atomheart.move.imove import MoveKey
from atomheart.move.utils import MoveUci

from .iboard import (
    BoardKey,
    BoardKeyWithoutCounters,
    IBoard,
    LegalMoveKeyGeneratorP,
    compute_key,
)
from .utils import Fen, FenPlusHistory


class LegalMoveKeyGeneratorRust(LegalMoveKeyGeneratorP):
    """LegalMoveKeyGeneratorRust is a Rust-compatible implementation of the LegalMoveKeyGeneratorP interface."""

    # whether to sort the legal_moves by their respective uci for easy comparison of various implementations
    sort_legal_moves: bool

    all_generated_keys_: list[MoveKey] | None

    chess_rust_binding: shakmaty_python_binding.MyChess

    @property
    def all_generated_keys(self) -> Sequence[MoveKey] | None:
        """Return the cached sequence of generated move keys, if available."""
        return self.all_generated_keys_

    def get_uci_from_move_key(self, move_key: MoveKey) -> MoveUci:
        """Return the UCI string corresponding to the given move key.

        Args:
            move_key (MoveKey): The move key to convert to UCI.

        Returns:
            moveUci: The UCI string corresponding to the given move key.

        """
        assert self.generated_moves is not None
        chess_move: shakmaty_python_binding.MyMove = self.generated_moves[move_key]
        return chess_move.uci()

    def __init__(
        self,
        sort_legal_moves: bool,
        chess_rust_binding: shakmaty_python_binding.MyChess,
        generated_moves: list[shakmaty_python_binding.MyMove] | None = None,
    ) -> None:
        """Initialize the Rust-compatible legal move generator.

        Args:
            sort_legal_moves (bool): Whether to sort the legal moves.
            chess_rust_binding (shakmaty_python_binding.MyChess): The Rust chess binding.
            generated_moves (list[shakmaty_python_binding.MyMove] | None, optional): The generated moves. Defaults to None.

        """
        self.chess_rust_binding = chess_rust_binding
        self.generated_moves = generated_moves
        if generated_moves is not None:
            self.number_moves = len(generated_moves)
            self.it: Iterator[int] = iter(range(self.number_moves))
            self.all_generated_keys_ = list(range(self.number_moves))
            if sort_legal_moves:

                def f(i: int) -> MoveUci:
                    assert self.generated_moves is not None
                    return self.generated_moves[i].uci()

                self.all_generated_keys_ = sorted(
                    list(range(self.number_moves)),
                    key=f,
                )
            else:
                self.all_generated_keys_ = list(range(self.number_moves))
        else:
            self.all_generated_keys_ = None
        self.sort_legal_moves = sort_legal_moves

    @property
    def fen(self) -> Fen:
        """Return the FEN string of the current chess position."""
        return self.chess_rust_binding.fen()

    def reset(self, generated_moves: list[shakmaty_python_binding.MyMove]) -> None:
        """Reset the legal move generator with a new list of generated moves."""
        self.generated_moves = generated_moves
        self.number_moves = len(generated_moves)
        self.it = iter(range(self.number_moves))
        self.all_generated_keys_ = list(range(self.number_moves))

    def copy_with_reset(self) -> "LegalMoveKeyGeneratorRust":
        """Create a copy of the legal move generator with reset state."""
        return LegalMoveKeyGeneratorRust(
            chess_rust_binding=self.chess_rust_binding,
            generated_moves=None,
            sort_legal_moves=self.sort_legal_moves,
        )

    def set_legal_moves(
        self, generated_moves: list[shakmaty_python_binding.MyMove]
    ) -> None:
        """Set the legal moves for the generator."""
        self.generated_moves = generated_moves
        self.number_moves = len(generated_moves)

    def __iter__(self) -> Iterator[MoveKey]:
        """Return an iterator over the legal move keys."""
        if self.generated_moves is None:
            self.generated_moves = self.chess_rust_binding.legal_moves()
        if self.sort_legal_moves:
            assert self.generated_moves is not None

            def f(i: int) -> MoveUci:
                assert self.generated_moves is not None
                return self.generated_moves[i].uci()

            self.it = iter(
                sorted(
                    list(range(self.number_moves)),
                    key=f,
                )
            )
        else:
            self.it = iter(range(self.number_moves))
        return self

    def __next__(self) -> MoveKey:
        """Return the next legal move key in the iteration."""
        return self.it.__next__()

    def copy(
        self, copied_chess_rust_binding: shakmaty_python_binding.MyChess | None = None
    ) -> "LegalMoveKeyGeneratorRust":
        """Create a copy of the legal move generator.

        Args:
            copied_chess_rust_binding (shakmaty_python_binding.MyChess | None, optional): The Rust chess binding to use in the copy. Defaults to None.

        Returns:
            LegalMoveKeyGeneratorRust: A copy of the legal move generator.

        """
        if copied_chess_rust_binding is None:
            copied_chess_rust_binding_ = self.chess_rust_binding
        else:
            copied_chess_rust_binding_ = copied_chess_rust_binding
        legal_move_copy = LegalMoveKeyGeneratorRust(
            chess_rust_binding=copied_chess_rust_binding_,
            generated_moves=(
                self.generated_moves.copy()
                if self.generated_moves is not None
                else None
            ),
            sort_legal_moves=self.sort_legal_moves,
        )
        if self.all_generated_keys_ is not None:
            legal_move_copy.all_generated_keys_ = self.all_generated_keys_.copy()
        else:
            legal_move_copy.all_generated_keys_ = legal_move_copy.all_generated_keys_
        return legal_move_copy

    def get_all(self) -> Sequence[MoveKey]:
        """Return a sequence of all legal move keys.

        Returns:
            Sequence[MoveKey]: A sequence of all legal move keys.

        """
        if self.generated_moves is None:
            self.generated_moves = self.chess_rust_binding.legal_moves()
            self.number_moves = len(self.generated_moves)
            self.all_generated_keys_ = None

        if self.all_generated_keys_ is None:
            if self.sort_legal_moves:

                def f(i: int) -> MoveUci:
                    assert self.generated_moves is not None
                    return self.generated_moves[i].uci()

                return sorted(
                    list(range(self.number_moves)),
                    key=f,
                )
            return list(range(self.number_moves))
        return self.all_generated_keys_

    def more_than_one(self) -> bool:
        """Check if there is more than one legal move available."""
        if self.generated_moves is None:
            self.generated_moves = self.chess_rust_binding.legal_moves()
            self.number_moves = len(self.generated_moves)
            self.all_generated_keys_ = None
        return len(self.generated_moves) > 0


# TODO(victor): implement rewind (and a test for it). See issue #24 for more details.


def _move_stack_factory() -> list[MoveUci]:
    return []


@dataclass
class RustyBoardChi(IBoard):
    """Rusty Board Chipiron.

    Object that describes the current board. It wraps the chess Board from the chess package so it can have more in it
    but im not sure its really necessary.i keep it for potential usefulness.

    This is the Rust version for speedy execution
    It is based on the binding library shakmaty_python_binding to use the rust library shakmaty
    """

    # the shakmaty implementation of the board that we wrap here
    chess_: shakmaty_python_binding.MyChess

    compute_board_modification: bool

    # to count the number of occurrence of each board to be able to compute
    # three-fold repetition as shakmaty does not do it atm
    rep_to_count: Counter[BoardKeyWithoutCounters]

    fast_representation_: BoardKey

    # storing the info here for fast access as it seems calls to rust bingings can be costy
    pawns_: int
    kings_: int
    queens_: int
    rooks_: int
    bishops_: int
    knights_: int
    white_: int
    black_: int
    turn_: bool
    ep_square_: int | None
    promoted_: int
    castling_rights_: int

    legal_moves_: LegalMoveKeyGeneratorRust

    # the move history is kept here because shakmaty_python_binding.MyChess does not have a move stack at the moment
    move_stack: list[MoveUci] = field(default_factory=_move_stack_factory)

    def __post_init__(self) -> None:
        """Initialize repetition counters after dataclass creation."""
        self.rep_to_count[self.fast_representation_without_counters] = 1

    def __str__(self) -> str:
        """Return a string representation of the board.

        Returns:
            str: A string representation of the board.

        """
        return self.fen

    def play_min_2(self, move: shakmaty_python_binding.MyMove) -> None:
        """Plays a move on the board without returning any modifications."""
        (
            self.castling_rights_,
            self.pawns_,
            self.knights_,
            self.bishops_,
            self.rooks_,
            self.queens_,
            self.kings_,
            self.white_,
            self.black_,
            turn_int,
            ep_square_int,
            self.promoted_,
        ) = self.chess_.play_and_return_o(move)
        self.turn_ = bool(turn_int)
        if ep_square_int == -1:
            self.ep_square_ = None
        else:
            self.ep_square_ = ep_square_int

    def play_min_3(self, move: shakmaty_python_binding.MyMove) -> BoardModificationRust:
        """Plays a move on the board and returns the board modifications."""
        (
            (
                self.castling_rights_,
                self.pawns_,
                self.knights_,
                self.bishops_,
                self.rooks_,
                self.queens_,
                self.kings_,
                self.white_,
                self.black_,
                turn_int,
                ep_square_int,
                self.promoted_,
            ),
            appearances,
            removals,
        ) = self.chess_.play_and_return_modifications(move)
        self.turn_ = bool(turn_int)
        if ep_square_int == -1:
            self.ep_square_ = None
        else:
            self.ep_square_ = ep_square_int

        board_modifications: BoardModificationRust = self.convert(appearances, removals)
        return board_modifications

    def convert(
        self,
        appearances: set[tuple[int, int, int]],
        removals: set[tuple[int, int, int]],
    ) -> BoardModificationRust:
        """Convert appearances and removals into a BoardModificationRust object.

        Args:
            appearances (set[tuple[int, int, int]]): The set of appearances.
            removals (set[tuple[int, int, int]]): The set of removals.

        Returns:
            BoardModificationRust: The board modification object.

        """
        board_modifications: BoardModificationRust = BoardModificationRust(
            appearances_=appearances, removals_=removals
        )

        return board_modifications

    def play_move(
        self, move: shakmaty_python_binding.MyMove
    ) -> BoardModificationP | None:
        """Plays a move on the board and returns the board modification.

        Args:
            move: The move to play.

        Returns:
            The board modification resulting from the move or None.

        """
        # TODO(victor): illegal moves seem accepted, do we care? if we dont write it in the doc. See issue #24 for more details.
        board_modifications: BoardModificationRust | None = None

        if self.compute_board_modification:
            board_modifications = self.play_min_3(move)
        else:
            self.play_min_2(move)

        # update after move
        self.legal_moves_ = (
            self.legal_moves_.copy_with_reset()
        )  # the legals moves needs to be recomputed as the board has changed

        fast_representation: BoardKey = compute_key(
            pawns=self.pawns_,
            knights=self.knights_,
            bishops=self.bishops_,
            rooks=self.rooks_,
            queens=self.queens_,
            kings=self.kings_,
            turn=self.turn_,
            castling_rights=self.castling_rights_,
            ep_square=self.ep_square_,
            white=self.white_,
            black=self.black_,
            promoted=self.promoted_,
            fullmove_number=self.chess_.fullmove_number(),
            halfmove_clock=self.chess_.halfmove_clock(),
        )
        self.fast_representation_ = fast_representation
        self.rep_to_count.update([self.fast_representation_without_counters])
        self.move_stack.append(move.uci())

        return board_modifications

    def play_move_uci(self, move_uci: MoveUci) -> BoardModificationP | None:
        """Play a move in UCI format."""
        chess_move: shakmaty_python_binding.MyMove = shakmaty_python_binding.MyMove(
            uci=move_uci, my_chess=self.chess_
        )
        return self.play_move(move=chess_move)

    # TODO(victor): look like this function might move to iboard when the dust settle. See issue #24 for more details.
    def play_move_key(self, move: MoveKey) -> BoardModificationP | None:
        """Play a move using its key."""
        assert self.legal_moves_.generated_moves is not None
        my_move: shakmaty_python_binding.MyMove = self.legal_moves_.generated_moves[
            move
        ]
        return self.play_move(move=my_move)

    def ply(self) -> int:
        """Return the number of half-moves (plies) that have been played on the board.

        :return: The number of half-moves played on the board.
        :rtype: int
        """
        ply: int = self.chess_.ply()
        return ply

    @property
    def turn(self) -> Color:
        """Get the current turn color.

        Returns:
            chess.Color: The color of the current turn.

        """
        return Color(int(self.turn_))

    @no_type_check
    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            bool: True if the game is over, False otherwise.

        """
        claim_draw: bool = len(self.move_stack) >= 5
        three_fold_repetition: bool = (
            max(self.rep_to_count.values()) > 2 if claim_draw else False
        )
        # TODO(victor): check the move stack : check for repetition as the rust version not do it. See issue #24 for more details. This is a temporary solution to avoid the cost of calling the rust binding for is_game_over when we can compute it in python with the move stack and the rep_to_count.
        # TODO(victor): remove this hasatrribute at some point. See issue #24 for more details. This is a temporary solution to avoid the cost of calling the rust binding for is_game_over when we can compute it in python with the move stack and the rep_to_count.

        chess_game_over: bool = False

        if hasattr(self, "is_game_over_"):
            attr_value: Any = self.is_game_over_
            chess_game_over = bool(attr_value)
        else:
            engine_result: Any = self.chess_.is_game_over()
            chess_game_over = bool(engine_result)

        return three_fold_repetition or chess_game_over

    def copy(self, stack: bool, deep_copy_legal_moves: bool = True) -> Self:
        """Create a copy of the current board.

        Args:
            stack (bool): Whether to copy the move stack as well.
            deep_copy_legal_moves (bool): Whether to deep copy the legal moves generator.

        Returns:
            RustyBoardChi: A new instance of the BoardChi class with the copied board.

        """
        chess_copy: shakmaty_python_binding.MyChess = self.chess_.copy()
        move_stack_ = self.move_stack.copy() if stack else []

        legal_moves_copy: LegalMoveKeyGeneratorRust
        if deep_copy_legal_moves:
            legal_moves_copy = self.legal_moves_.copy(
                copied_chess_rust_binding=chess_copy
            )
        else:
            legal_moves_copy = self.legal_moves_
            legal_moves_copy.chess_rust_binding = chess_copy

        return type(self)(
            chess_=chess_copy,
            move_stack=move_stack_,
            compute_board_modification=self.compute_board_modification,
            rep_to_count=self.rep_to_count.copy(),
            fast_representation_=self.fast_representation_,
            pawns_=self.pawns_,
            knights_=self.knights_,
            kings_=self.kings_,
            rooks_=self.rooks_,
            queens_=self.queens_,
            bishops_=self.bishops_,
            black_=self.black_,
            white_=self.white_,
            turn_=self.turn_,
            ep_square_=self.ep_square_,
            promoted_=self.promoted_,
            castling_rights_=self.castling_rights_,
            legal_moves_=legal_moves_copy,
        )

    @property
    def legal_moves(self) -> LegalMoveKeyGeneratorRust:
        """Returns the legal move generator for the current board state.

        Returns:
            LegalMoveKeyGeneratorRust: The legal move generator for the current board state.

        """
        # TODO(victor): minimize this call and understand when the role of the variable all legal move generated. See issue #24 for more details.
        return self.legal_moves_

    def number_of_pieces_on_the_board(self) -> int:
        """Return the number of pieces currently on the board.

        Returns:
            int: The number of pieces on the board.

        """
        return self.chess_.number_of_pieces_on_the_board()

    @property
    def fen(self) -> Fen:
        """Returns the Forsyth-Edwards Notation (FEN) representation of the chess board.

        :return: The FEN string representing the current state of the board.
        """
        return self.chess_.fen()

    def piece_at(self, square: chess.Square) -> chess.Piece | None:
        """Return the piece at the specified square on the chess board.

        Args:
            square (chess.Square): The square on the chess board.

        Returns:
            chess.Piece | None: The piece at the specified square, or None if there is no piece.

        """
        piece_or_none = self.chess_.piece_at(square)
        piece: chess.Piece | None
        if piece_or_none is None:
            piece = None
        else:
            piece = chess.Piece(piece_type=piece_or_none[1], color=piece_or_none[0])
        return piece

    def piece_map(self) -> dict[chess.Square, tuple[int, bool]]:
        """Return a mapping of squares to piece type and color."""
        return self.chess_.piece_map()

    def has_kingside_castling_rights(self, color: chess.Color) -> bool:
        """Check if the specified color has kingside castling rights.

        Args:
            color (chess.Color): The color to check for kingside castling rights.

        Returns:
            bool: True if the specified color has kingside castling rights, False otherwise.

        """
        return self.chess_.has_kingside_castling_rights(color)

    def has_queenside_castling_rights(self, color: chess.Color) -> bool:
        """Check if the specified color has queenside castling rights.

        Args:
            color (chess.Color): The color to check for queenside castling rights.

        Returns:
            bool: True if the specified color has kingside castling rights, False otherwise.

        """
        return self.chess_.has_queenside_castling_rights(color)

    def print_chess_board(self) -> str:
        """Print the current state of the chess board.

        This method prints the current state of the chess board, including the position of all the pieces.
        It also prints the FEN (Forsyth-Edwards Notation) representation of the board.

        Returns:
            None

        """
        return str(self.chess_.fen())

    def tell_result(self) -> None:
        """Log the result for the current board state."""
        ...

    @property
    def move_history_stack(self) -> list[MoveUci]:
        """Return the history of moves made in the game."""
        return self.move_stack


    def dump(self, file: Any) -> None:
        """Dump the current state of the board to the specified file."""

    def is_attacked(self, a_color: chess.Color) -> bool:
        """Check if any piece of the color `a_color` is attacked.

        Args:
            a_color (chess.Color): The color of the pieces to check.

        Returns:
            bool: True if any piece of the specified color is attacked, False otherwise.

        """
        return self.chess_.is_attacked(a_color)

    @property
    def pawns(self) -> chess.Bitboard:
        """Return the pawns bitboard."""
        return self.chess_.pawns()

    @property
    def knights(self) -> chess.Bitboard:
        """Return the knights bitboard."""
        return self.knights_

    @property
    def bishops(self) -> chess.Bitboard:
        """Return the bishops bitboard."""
        return self.bishops_

    @property
    def rooks(self) -> chess.Bitboard:
        """Return the rooks bitboard."""
        return self.rooks_

    @property
    def queens(self) -> chess.Bitboard:
        """Return the queens bitboard."""
        return self.queens_


    @property
    def kings(self) -> chess.Bitboard:
        """Return the kings bitboard."""
        return self.kings_


    @property
    def white(self) -> chess.Bitboard:
        """Return the white pieces bitboard."""
        return self.white_

    @property
    def black(self) -> chess.Bitboard:
        """Return the black pieces bitboard."""
        return self.black_

    @property
    def occupied(self) -> chess.Bitboard:
        """Return the occupied squares bitboard."""
        return self.chess_.occupied()

    def result(self, claim_draw: bool = False) -> str:
        """Return the game result as a string."""
        claim_draw_: bool = len(self.move_stack) >= 5 and claim_draw
        three_fold_repetition: bool = (
            max(self.rep_to_count.values()) > 2 if claim_draw_ else False
        )

        if three_fold_repetition:
            return "1/2-1/2"
        return self.chess_.result()

    @property
    def castling_rights(self) -> chess.Bitboard:
        """Return the castling rights bitboard."""
        return self.castling_rights_

    def termination(self) -> None:
        """Return the termination status for the game (not available in Rust binding)."""
        return None

    def occupied_color(self, color: chess.Color) -> chess.Bitboard:
        """Return the occupied squares bitboard for a given color."""
        if color == chess.WHITE:
            return self.chess_.white()
        return self.chess_.black()

    @property
    def halfmove_clock(self) -> int:
        """Return the halfmove clock value."""
        return self.chess_.halfmove_clock()

    @property
    def promoted(self) -> chess.Bitboard:
        """Return the promoted pieces bitboard."""
        return self.promoted_

    @property
    def fullmove_number(self) -> int:
        """Return the fullmove number."""
        return self.chess_.fullmove_number()

    @property
    def ep_square(self) -> int | None:
        """Return the en passant square, if any."""
        return self.ep_square_

    def is_zeroing(self, move: MoveKey) -> bool:
        """Check if a move is a zeroing move (i.e., checks if the given move is a capture or pawn move.

        Args:
            move (MoveKey): The move to check.

        Returns:
            bool: True if the move is a zeroing move, False otherwise.

        """
        assert self.legal_moves_.generated_moves is not None
        chess_move: shakmaty_python_binding.MyMove = self.legal_moves_.generated_moves[
            move
        ]
        return chess_move.is_zeroing()

    def into_fen_plus_history(self) -> FenPlusHistory:
        """Convert the current board state into a FenPlusHistory object."""
        return FenPlusHistory(
            current_fen=self.fen, historical_moves=self.move_history_stack
        )
