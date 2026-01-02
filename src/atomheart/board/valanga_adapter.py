"""Adapter that makes an IBoard look like a valanga.State."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

import valanga

if TYPE_CHECKING:
    from atomheart.board.iboard import IBoard
    from atomheart.move.imove import MoveKey


@dataclass
class ValangaChessState(valanga.State):
    """Adapter that makes an IBoard look like a valanga.State."""

    board: "IBoard"

    @property
    def tag(self) -> valanga.StateTag:
        return self.board.tag

    @property
    def branch_keys(self) -> valanga.BranchKeyGeneratorP[valanga.BranchKey]:
        return self.board.branch_keys

    def branch_name_from_key(self, key: valanga.BranchKey) -> str:
        return self.board.get_uci_from_move_key(cast("MoveKey", key))

    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    def copy(self, stack: bool, deep_copy_legal_moves: bool = True) -> Self:
        return type(self)(
            self.board.copy(stack=stack, deep_copy_legal_moves=deep_copy_legal_moves)
        )

    def step(self, branch_key: valanga.BranchKey) -> valanga.StateModifications | None:
        return self.board.play_move_key(cast("MoveKey", branch_key))
