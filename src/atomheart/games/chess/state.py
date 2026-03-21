"""Chess state wrapper for Valanga."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

import valanga

if TYPE_CHECKING:
    from atomheart.games.chess.board.iboard import IBoard

    _ColorTurnState: TypeAlias = valanga.TurnState[valanga.Color]  # noqa: UP040
else:
    _ColorTurnState = object


@dataclass(frozen=True, slots=True)
class ChessState(_ColorTurnState):
    """Pure observation wrapper around an :class:`IBoard`."""

    board: "IBoard"

    @property
    def tag(self) -> valanga.StateTag:
        """Return the board tag."""
        return self.board.tag

    def is_game_over(self) -> bool:
        """Return whether the game is over."""
        return self.board.is_game_over()

    def pprint(self) -> str:
        """Return a pretty-printed board string."""
        return self.board.print_chess_board()

    @property
    def turn(self) -> valanga.Color:
        """Return the current turn color."""
        return self.board.turn
