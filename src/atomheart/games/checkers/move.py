"""Move encoding helpers for checkers.

Pattern B is used: move keys are structural and hashable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeAlias

from valanga import BranchKeyGeneratorP

if TYPE_CHECKING:
    from collections.abc import Sequence

MoveKey: TypeAlias = tuple[int, tuple[int, ...], tuple[int, ...], bool]
"""(start_sq, landings, jumped, promotes).

`promotes` is True only when a man is crowned during this move.
"""


@dataclass(slots=True)
class CheckersMoveGenerator(BranchKeyGeneratorP[MoveKey]):
    """Materialized move-key generator that satisfies Valanga's protocol."""

    moves: list[MoveKey]
    sort_branch_keys: bool = False
    _i: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        """Normalize ordering and reset iteration pointer."""
        if self.sort_branch_keys:
            self.moves.sort(key=move_name)
        self._i = 0

    @property
    def all_generated_keys(self) -> Sequence[MoveKey] | None:
        """Return all generated keys (already fully materialized)."""
        return tuple(self.moves)

    def __iter__(self) -> CheckersMoveGenerator:
        """Return self as an iterator."""
        return self

    def __next__(self) -> MoveKey:
        """Return the next move key."""
        if self._i >= len(self.moves):
            raise StopIteration

        value = self.moves[self._i]
        self._i += 1
        return value

    def more_than_one(self) -> bool:
        """Tell whether this generator contains at least two actions."""
        return len(self.moves) > 1

    def get_all(self) -> Sequence[MoveKey]:
        """Return all move keys."""
        return tuple(self.moves)

    def copy_with_reset(self) -> CheckersMoveGenerator:
        """Create a new generator with the same moves and reset iteration."""
        return CheckersMoveGenerator(
            self.moves.copy(),
            sort_branch_keys=self.sort_branch_keys,
        )


def move_name(move: MoveKey) -> str:
    """Render a move key to a stable textual format."""
    start_sq, landings, jumped, promotes = move
    if jumped:
        path = "x".join(str(sq) for sq in (start_sq, *landings))
    else:
        path = f"{start_sq}-{landings[0]}"

    return f"{path}{'K' if promotes else ''}"


def is_capture(move: MoveKey) -> bool:
    """Return whether the move key represents a capture sequence."""
    return len(move[2]) > 0


def end_sq(move: MoveKey) -> int:
    """Return the final landing square of a move key."""
    return move[1][-1]
