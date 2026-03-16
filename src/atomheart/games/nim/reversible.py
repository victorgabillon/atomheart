"""Reversible dynamics for the Nim game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import valanga

from .state import NimState

if TYPE_CHECKING:
    from .dynamics import NimAction, NimDynamics


@dataclass(frozen=True, slots=True)
class NimUndo:
    """Compact undo data storing the previous stones and turn."""

    previous_stones: int
    previous_turn: valanga.Color


class NimReversibleDynamics(valanga.ReversibleDynamics[NimState, NimUndo]):
    """In-place reversible dynamics for Nim search."""

    dynamics: NimDynamics
    _stones: int
    _turn: valanga.Color

    def __init__(self, dynamics: NimDynamics, state: NimState) -> None:
        """Initialize reversible dynamics with a starting state."""
        self.dynamics = dynamics
        self._stones = state.stones
        self._turn = state.turn

    @property
    def state(self) -> NimState:
        """Build an immutable snapshot of the current Nim state."""
        return NimState(stones=self._stones, turn=self._turn)

    @state.setter
    def state(self, value: NimState) -> None:
        self._stones = value.stones
        self._turn = value.turn

    def legal_actions(self) -> valanga.BranchKeyGeneratorP[NimAction]:
        """Return legal actions from the current mutable state."""
        return self.dynamics.legal_actions(self.state)

    def push(self, action: valanga.BranchKey) -> NimUndo:
        """Apply an action in-place and return undo data."""
        current_state = self.state
        undo = NimUndo(
            previous_stones=current_state.stones,
            previous_turn=current_state.turn,
        )
        next_state = self.dynamics.step(current_state, action).next_state
        self._stones = next_state.stones
        self._turn = next_state.turn
        return undo

    def pop(self, undo: NimUndo) -> None:
        """Restore the previous state from an undo token."""
        self._stones = undo.previous_stones
        self._turn = undo.previous_turn

    def action_name(self, action: valanga.BranchKey) -> str:
        """Render the canonical action name from the current state."""
        return self.dynamics.action_name(self.state, action)

    def action_from_name(self, name: str) -> NimAction:
        """Resolve an action name using the current state."""
        return self.dynamics.action_from_name(self.state, name)
