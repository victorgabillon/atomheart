"""ReversibleDynamics scaffold for checkers."""

from __future__ import annotations

from dataclasses import dataclass

import valanga

from .dynamics import CheckersDynamics
from .move import MoveKey
from .state import CheckersState


@dataclass(frozen=True, slots=True)
class CheckersUndo:
    """Undo record for reversible checkers push/pop.

    This placeholder keeps the complete previous state. A future optimized version
    should store only incremental deltas (moved piece, captures, counters).
    """

    previous_state: CheckersState


@dataclass(slots=True)
class CheckersReversibleDynamics(valanga.ReversibleDynamics[MoveKey, CheckersUndo]):
    """Simple push/pop wrapper around :class:`CheckersDynamics`."""

    state: CheckersState
    dynamics: CheckersDynamics

    def legal_actions(self) -> valanga.BranchKeyGeneratorP[MoveKey]:
        """Return legal actions from current state."""
        return self.dynamics.legal_actions(self.state)

    def push(self, action: MoveKey) -> CheckersUndo:
        """Apply an action and return undo data."""
        undo = CheckersUndo(previous_state=self.state)
        self.state = self.dynamics.step(self.state, action).next_state
        return undo

    def pop(self, undo: CheckersUndo) -> None:
        """Restore state from undo data."""
        self.state = undo.previous_state

    def action_name(self, action: MoveKey) -> str:
        """Render a move name using state-aware dynamics."""
        return self.dynamics.action_name(self.state, action)

    def action_from_name(self, name: str) -> MoveKey:
        """Parse/resolve a move name from current state."""
        action = self.dynamics.action_from_name(self.state, name)
        if not isinstance(action, tuple):
            raise TypeError("Expected MoveKey tuple from dynamics.")
        return action
