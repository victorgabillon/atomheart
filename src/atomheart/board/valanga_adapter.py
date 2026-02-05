"""Adapter that makes an IBoard look like a valanga.State."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self, cast

import valanga

if TYPE_CHECKING:
    from atomheart.board.iboard import IBoard
    from atomheart.move.imove import MoveKey


@dataclass
class ValangaChessState(valanga.State):
    """Wrapper that makes an IBoard look like a valanga.State."""

    board: "IBoard"

    @property
    def tag(self) -> valanga.StateTag:
        """Return the state tag from the underlying board."""
        return self.board.tag

    @property
    def branch_keys(self) -> valanga.BranchKeyGeneratorP[valanga.BranchKey]:
        """Return the branch key generator from the underlying board."""
        return self.board.branch_keys

    def branch_name_from_key(self, key: valanga.BranchKey) -> str:
        """Return the move name for a branch key."""
        return self.board.get_uci_from_move_key(cast("MoveKey", key))

    def is_game_over(self) -> bool:
        """Return whether the game is over."""
        return self.board.is_game_over()

    def copy(self, stack: bool, deep_copy_legal_moves: bool = True) -> Self:
        """Return a copy of the wrapped board state."""
        return type(self)(
            self.board.copy(stack=stack, deep_copy_legal_moves=deep_copy_legal_moves)
        )

    def step(self, branch_key: valanga.BranchKey) -> valanga.StateModifications | None:
        """Advance the state by playing the move for the given branch key."""
        return self.board.play_move_key(cast("MoveKey", branch_key))

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes/methods to the underlying board.

        Called only if `name` wasn't found on the wrapper itself.
        """
        return getattr(self.board, name)

    def pprint(self) -> str:
        """Return a pretty-printed string representation of the content.

        Returns:
            str: A pretty-printed string representation of the content.

        """
        return self.board.print_chess_board()

    def branch_key_from_name(self, name: str) -> valanga.BranchKey:
        """Get the branch key from a move name in UCI format."""
        return self.board.get_move_key_from_uci(name)

    @property
    def turn(self) -> valanga.Color:
        """Return the current turn color."""
        return self.board.turn
