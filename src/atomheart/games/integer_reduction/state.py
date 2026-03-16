"""State objects for the integer reduction game."""

from __future__ import annotations

from dataclasses import dataclass

import valanga


class IntegerReductionStateTypeError(TypeError):
    """Raised when the state value is not a valid integer."""

    def __init__(self) -> None:
        """Build a consistent type validation error."""
        super().__init__("Integer reduction state value must be an int.")


class IntegerReductionStateValueError(ValueError):
    """Raised when the state value is outside the valid range."""

    def __init__(self) -> None:
        """Build a consistent range validation error."""
        super().__init__("Integer reduction state value must be >= 1.")


@dataclass(frozen=True, slots=True)
class IntegerReductionState(valanga.State):
    """Immutable state for the single-player integer reduction game."""

    value: int

    def __post_init__(self) -> None:
        """Validate the stored integer value."""
        if self.value.__class__ is not int:
            raise IntegerReductionStateTypeError
        if self.value < 1:
            raise IntegerReductionStateValueError

    @property
    def tag(self) -> valanga.StateTag:
        """Return a stable tag suitable for caching."""
        return self.value

    def is_game_over(self) -> bool:
        """Return whether the terminal goal has been reached."""
        return self.value == 1

    def pprint(self) -> str:
        """Return a concise human-readable state string."""
        return f"n={self.value}"

    def __str__(self) -> str:
        """Return the compact canonical state form."""
        return self.pprint()
