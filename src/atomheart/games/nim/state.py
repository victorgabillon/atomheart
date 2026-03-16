"""State objects for the Nim game."""

from __future__ import annotations

from dataclasses import dataclass

import valanga


def _turn_prefix(turn: valanga.Color) -> str:
    """Return the compact turn prefix used in string rendering."""
    return "W" if turn == valanga.Color.WHITE else "B"


@dataclass(frozen=True, slots=True, init=False)
class NimState(valanga.TurnState):
    """Immutable state for single-pile subtraction Nim."""

    stones: int
    _turn: valanga.Color

    def __init__(self, stones: int, turn: valanga.Color) -> None:
        """Initialize and validate the stored stone count and turn."""
        if stones.__class__ is not int:
            raise TypeError("Nim stones must be an int.")  # noqa: TRY003
        if stones < 0:
            raise ValueError("Nim stones must be >= 0.")  # noqa: TRY003
        if turn.__class__ is not valanga.Color:
            raise TypeError("Nim turn must be valanga.Color.")  # noqa: TRY003
        object.__setattr__(self, "stones", stones)
        object.__setattr__(self, "_turn", turn)

    @property
    def turn(self) -> valanga.Color:
        """Return the side to move."""
        return self._turn

    @property
    def tag(self) -> valanga.StateTag:
        """Return a stable tag covering both stones and side to move."""
        return (self.stones, self._turn)

    def is_game_over(self) -> bool:
        """Return whether the pile is empty."""
        return self.stones == 0

    def pprint(self) -> str:
        """Return a concise deterministic state string."""
        return f"{_turn_prefix(self._turn)}:{self.stones}"

    def __str__(self) -> str:
        """Return the compact canonical state form."""
        return self.pprint()
