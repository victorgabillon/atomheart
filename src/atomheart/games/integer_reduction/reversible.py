"""Reversible dynamics for the integer reduction game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import valanga

from .state import IntegerReductionState

if TYPE_CHECKING:
    from .dynamics import IntegerReductionAction, IntegerReductionDynamics


@dataclass(frozen=True, slots=True)
class IntegerReductionUndo:
    """Compact undo data storing the previous integer value."""

    previous_value: int


class IntegerReductionReversibleDynamics(
    valanga.ReversibleDynamics[IntegerReductionState, IntegerReductionUndo]
):
    """In-place reversible dynamics for integer reduction search."""

    dynamics: IntegerReductionDynamics
    _value: int

    def __init__(
        self,
        dynamics: IntegerReductionDynamics,
        state: IntegerReductionState,
    ) -> None:
        """Initialize reversible dynamics with a starting state."""
        self.dynamics = dynamics
        self._value = state.value

    @property
    def state(self) -> IntegerReductionState:
        """Build an immutable snapshot of the current integer value."""
        return IntegerReductionState(self._value)

    @state.setter
    def state(self, value: IntegerReductionState) -> None:
        self._value = value.value

    def legal_actions(self) -> valanga.BranchKeyGeneratorP[IntegerReductionAction]:
        """Return legal actions from the current mutable state."""
        return self.dynamics.legal_actions(self.state)

    def push(self, action: valanga.BranchKey) -> IntegerReductionUndo:
        """Apply an action in-place and return undo data."""
        current_state = self.state
        undo = IntegerReductionUndo(previous_value=current_state.value)
        self._value = self.dynamics.step(current_state, action).next_state.value
        return undo

    def pop(self, undo: IntegerReductionUndo) -> None:
        """Restore the previous value from an undo token."""
        self._value = undo.previous_value

    def action_name(self, action: valanga.BranchKey) -> str:
        """Render the canonical action name from the current state."""
        return self.dynamics.action_name(self.state, action)

    def action_from_name(self, name: str) -> IntegerReductionAction:
        """Resolve an action name using the current state."""
        return self.dynamics.action_from_name(self.state, name)
