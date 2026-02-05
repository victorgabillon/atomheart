"""Interface for a chess board."""

import typing
from collections.abc import Iterator, Sequence
from dataclasses import asdict
from typing import Any, Protocol, Self

import chess
import valanga
import yaml

from atomheart.board.board_modification import BoardModificationP
from atomheart.move import MoveUci
from atomheart.move.imove import MoveKey

from .utils import Fen, FenPlusHistory, FenPlusMoveHistory

# identifier that should be unique to any position
BoardKey = tuple[
    int, int, int, int, int, int, bool, int, int | None, int, int, int, int, int
]

# identifier that removes the info (such as rounds) to count easily repeating position at difference round of the game
BoardKeyWithoutCounters = tuple[
    int, int, int, int, int, int, bool, int, int | None, int, int, int
]


class BoardInvariantError(RuntimeError):
    """Raised when there is an invariant error in the board, such as an inconsistent legal moves / UCI relation."""

    def __init__(self) -> None:
        """Initialize the board invariant error."""
        super().__init__(
            "internal error: inconsistent legal-moves / UCI relation in boards object"
        )


class LegalMoveKeyGeneratorP(valanga.BranchKeyGeneratorP[MoveKey], Protocol):
    """Protocol for a legal move generator that yields move keys."""

    # whether to sort the legal_moves by their respective uci for easy comparison of various implementations
    sort_legal_moves: bool = False

    @property
    def all_generated_keys(self) -> Sequence[MoveKey] | None:
        """Return a sequence of all generated move keys, or None if not available."""
        ...

    def __iter__(self) -> Iterator[MoveKey]:
        """Return an iterator over the legal move keys."""
        ...

    def __next__(self) -> MoveKey:
        """Return the next legal move key."""
        ...

    def more_than_one(self) -> bool:
        """Check if there is more than one legal move available.

        Returns:
            bool: True if there is more than one legal move, False otherwise.

        """
        ...

    def get_all(self) -> Sequence[MoveKey]:
        """Return a list of all legal move keys."""
        ...

    def get_uci_from_move_key(self, move_key: MoveKey) -> MoveUci:
        """Return the UCI string corresponding to the given move key.

        Args:
            move_key (MoveKey): The move key to convert to UCI.

        Returns:
            moveUci: The UCI string corresponding to the given move key.

        """
        ...

    def copy_with_reset(self) -> Self:
        """Create a copy of the legal move generator with an optional reset of generated moves.

        Returns:
            Self: A new instance of the legal move generator with the specified generated moves.

        """
        ...

    @property
    def fen(self) -> Fen:
        """Return the FEN string representation of the board."""
        ...


def compute_key(
    pawns: int,
    knights: int,
    bishops: int,
    rooks: int,
    queens: int,
    kings: int,
    turn: bool,
    castling_rights: int,
    ep_square: int | None,
    white: int,
    black: int,
    promoted: int,
    fullmove_number: int,
    halfmove_clock: int,
) -> BoardKey:
    """Compute and return a unique key representing the current state of the chess board.

    The key is computed by concatenating various attributes of the board, including the positions of pawns, knights,
    bishops, rooks, queens, and kings, as well as the current turn, castling rights, en passant square, halfmove clock,
    occupied squares for each color, promoted pieces, and the fullmove number.
    It is faster than calling the fen.

    Returns:
        str: A unique key representing the current state of the chess board.

    """
    string: BoardKey = (
        pawns,
        knights,
        bishops,
        rooks,
        queens,
        kings,
        turn,
        castling_rights,
        ep_square,
        white,
        black,
        promoted,
        fullmove_number,
        halfmove_clock,
    )
    return string


# Note that we do not use Dict[Square, Piece] because of the rust version that would need to transform
# tuple[chess.PieceType, chess.Color] into Piece and would lose time
PieceMap = typing.Annotated[
    dict[chess.Square, tuple[chess.PieceType, chess.Color]],
    "a dictionary that list the pieces on the board",
]


class IBoard(Protocol):
    """Interface for a chess board."""

    fast_representation_: BoardKey

    def get_uci_from_move_key(self, move_key: MoveKey) -> MoveUci:
        """Return the UCI string corresponding to the given move key.

        Args:
            move_key (MoveKey): The move key to convert to UCI.

        Returns:
            moveUci: The UCI string corresponding to the given move key.

        """
        return self.legal_moves.get_uci_from_move_key(move_key)

    def get_move_key_from_uci(self, move_uci: MoveUci) -> MoveKey:
        """Return the move key corresponding to the given UCI string.

        Args:
            move_uci (moveUci): The UCI string to convert to a move key.

        Returns:
            MoveKey: The move key corresponding to the given UCI string.

        Raises:
                KeyError: If the UCI string is not found in the legal moves.

        """
        number_moves: int = len(self.legal_moves.get_all())
        i: int

        for i in range(number_moves):
            if self.legal_moves.get_uci_from_move_key(i) == move_uci:
                return i

        raise BoardInvariantError

    def play_move_key(self, move: MoveKey) -> BoardModificationP | None:
        """Plays the move corresponding to the given move key.

        Args:
            move (MoveKey): The move key to play.

        Returns:
            BoardModificationP | None: The result of the move, or None if the move is illegal.

        """
        ...

    def play_move_uci(self, move_uci: MoveUci) -> BoardModificationP | None:
        """Plays the move corresponding to the given UCI string.

        Args:
            move_uci (moveUci): The UCI string to play.

        Returns:
            BoardModificationP | None: The result of the move, or None if the move is illegal.

        """
        ...

    @property
    def fen(self) -> Fen:
        """Returns the FEN string representation of the board.

        Returns:
            fen: The FEN string representation of the board.

        """
        ...

    @property
    def move_history_stack(
        self,
    ) -> list[MoveUci]:
        """Returns the move history stack.

        Returns:
            list[moveUci]: The move history stack.

        """
        ...

    def ply(self) -> int:
        """Return the number of half-moves (plies) that have been played on the board.

        :return: The number of half-moves played on the board.
        :rtype: int
        """
        ...

    @property
    def turn(self) -> valanga.Color:
        """Get the current turn color.

        Returns:
            chess.Color: The color of the current turn.

        """
        ...

    def copy(self, stack: bool, deep_copy_legal_moves: bool = True) -> Self:
        """Create a copy of the current board.

        Args:
            stack (bool): Whether to copy the move stack as well.
            deep_copy_legal_moves (bool): Whether to deep copy the legal moves generator.

        Returns:
            BoardChi: A new instance of the BoardChi class with the copied board.

        """
        ...

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            bool: True if the game is over, False otherwise.

        """
        ...

    @property
    def pawns(self) -> chess.Bitboard:
        """Returns the bitboard representing the pawns on the board."""
        ...

    @property
    def knights(self) -> chess.Bitboard:
        """Returns the bitboard representing the knights on the board."""
        ...

    @property
    def bishops(self) -> chess.Bitboard:
        """Returns the bitboard representing the bishops on the board."""
        ...

    @property
    def rooks(self) -> chess.Bitboard:
        """Returns the bitboard representing the rooks on the board."""
        ...

    @property
    def queens(self) -> chess.Bitboard:
        """Returns the bitboard representing the queens on the board."""
        ...

    @property
    def kings(self) -> chess.Bitboard:
        """Returns the bitboard representing the kings on the board."""
        ...

    @property
    def white(self) -> chess.Bitboard:
        """Returns the bitboard representing the white pieces on the board."""
        ...

    @property
    def black(self) -> chess.Bitboard:
        """Returns the bitboard representing the black pieces on the board."""
        ...

    @property
    def halfmove_clock(self) -> int:
        """Returns the halfmove clock of the board."""
        ...

    @property
    def promoted(self) -> chess.Bitboard:
        """Returns the bitboard representing the promoted pieces on the board."""
        ...

    @property
    def fullmove_number(self) -> int:
        """Returns the fullmove number of the board."""
        ...

    @property
    def castling_rights(self) -> chess.Bitboard:
        """Returns the bitboard representing the castling rights on the board."""
        ...

    @property
    def occupied(self) -> chess.Bitboard:
        """Returns the bitboard representing all occupied squares on the board."""
        ...

    def occupied_color(self, color: chess.Color) -> chess.Bitboard:
        """Return the bitboard representing the occupied squares for the given color."""
        ...

    def result(self, claim_draw: bool = False) -> str:
        """Return the result of the game as a string."""
        ...

    def termination(self) -> chess.Termination | None:
        """Return the termination status of the game."""
        ...

    def dump(self, file: Any) -> None:
        """Dump the current board state to a file in YAML format.

        Args:
            file (Any): The file object to write the board state to.

        """
        # create minimal info for reconstruction that is the class FenPlusMoveHistory

        current_fen: Fen = self.fen
        fen_plus_moves: FenPlusMoveHistory = FenPlusMoveHistory(
            current_fen=current_fen, historical_moves=self.move_history_stack
        )

        yaml.dump(asdict(fen_plus_moves), file, default_flow_style=False)

    @property
    def ep_square(self) -> int | None:
        """Returns the en passant square if it exists, otherwise None."""
        ...

    @property
    def tag(self) -> BoardKey:
        """Returns a fast representation of the board.

        This method computes and returns a string representation of the board
        that can be quickly generated and used for various purposes.

        :return: A string representation of the board.
        :rtype: str
        """
        return self.fast_representation_

    @property
    def fast_representation_without_counters(self) -> BoardKeyWithoutCounters:
        """Returns a fast representation of the board.

        This method computes and returns a string representation of the board
        that can be quickly generated and used for various purposes.

        :return: A string representation of the board.
        :rtype: str
        """
        assert self.fast_representation_ is not None
        return self.fast_representation_[:-2]

    def is_zeroing(self, move: MoveKey) -> bool:
        """Check if a move is a zeroing move (i.e., checks if the given move is a capture or pawn move.

        Args:
            move (MoveKey): The move to check.

        Returns:
            bool: True if the move is a zeroing move, False otherwise.

        """
        ...

    def is_attacked(self, a_color: chess.Color) -> bool:
        """Check if the given color is attacked.

        Args:
            a_color (chess.Color): The color to check.

        Returns:
            bool: True if the color is attacked, False otherwise.

        """
        ...

    @property
    def legal_moves(self) -> LegalMoveKeyGeneratorP:
        """Returns the legal moves generator."""
        ...

    # to comply with anemone interface for State (seems hacky but avoid to create another wrapper for now)
    @property
    def branch_keys(self) -> LegalMoveKeyGeneratorP:
        """Returns the legal moves generator."""
        return self.legal_moves

    def number_of_pieces_on_the_board(self) -> int:
        """Return the number of pieces currently on the board."""
        ...

    def piece_map(self) -> dict[chess.Square, tuple[chess.PieceType, chess.Color]]:
        """Return a mapping from squares to pieces on the board."""
        ...

    def has_kingside_castling_rights(self, color: chess.Color) -> bool:
        """Return whether the given color has kingside castling rights."""
        ...

    def has_queenside_castling_rights(self, color: chess.Color) -> bool:
        """Return whether the given color has queenside castling rights."""
        ...

    def print_chess_board(self) -> str:
        """Return a string representation of the chess board."""
        ...

    def tell_result(self) -> None:
        """Print the result of the game."""
        ...

    def into_fen_plus_history(self) -> FenPlusHistory:
        """Convert the current board state into a FenPlusHistory object."""
        ...
