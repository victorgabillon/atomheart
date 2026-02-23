"""Valanga Dynamics adapter for checkers."""

from __future__ import annotations

from dataclasses import dataclass

import valanga
from valanga.over_event import HowOver, Winner

from .move import CheckersMoveGenerator, MoveKey, move_name
from .rules import CheckersRules
from .state import CheckersState


@dataclass(slots=True)
class CheckersDynamics(valanga.Dynamics[CheckersState]):
    """Protocol-correct scaffold dynamics for checkers."""

    rules: CheckersRules = CheckersRules()

    def legal_actions(self, state: CheckersState) -> valanga.BranchKeyGeneratorP[MoveKey]:
        """Return legal move keys for the state.

        This scaffold intentionally returns an empty move list until move generation
        is implemented.
        """
        _ = (state, self.rules)
        return CheckersMoveGenerator([], sort_branch_keys=True)

    def step(self, state: CheckersState, action: MoveKey) -> valanga.Transition[CheckersState]:
        """Apply an action and return a transition.

        The current scaffold leaves board mutation unimplemented and returns the
        original state. It still wires piece-exhaustion terminal over-event
        semantics in a protocol-compliant way.
        """
        move = self._as_move_key(action)
        next_state = self._apply_move(state, move)

        is_over = next_state.is_game_over()
        over_event: valanga.OverEvent | None = None
        if is_over:
            winner = (
                Winner.BLACK
                if (next_state.wm | next_state.wk) == 0
                else Winner.WHITE
            )
            over_event = valanga.OverEvent(HowOver.WIN, winner, "piece_exhaustion")

        return valanga.Transition(
            next_state=next_state,
            modifications=None,
            is_over=is_over,
            over_event=over_event,
            info={"move": move_name(move)},
        )

    def action_name(self, state: CheckersState, action: MoveKey) -> str:
        """Return a stable text form for an action."""
        _ = state
        return move_name(self._as_move_key(action))

    def action_from_name(self, state: CheckersState, name: str) -> MoveKey:
        """Resolve an action by matching the generated move names."""
        for move in self.legal_actions(state).get_all():
            if move_name(move) == name:
                return move

        msg = f"No legal checkers move named {name!r}."
        raise ValueError(msg)

    @staticmethod
    def _as_move_key(action: MoveKey) -> MoveKey:
        """Type-check and normalize branch key to a checkers move key."""
        if not isinstance(action, tuple) or len(action) != 4:
            raise TypeError("Checkers actions must be MoveKey tuples.")

        start_sq, landings, jumped, promotes = action
        if not isinstance(start_sq, int):
            raise TypeError("MoveKey start square must be int.")
        if not isinstance(landings, tuple) or not landings:
            raise TypeError("MoveKey landings must be a non-empty tuple.")
        if not all(isinstance(landing_sq, int) for landing_sq in landings):
            raise TypeError("MoveKey landings must contain ints.")
        if not isinstance(jumped, tuple):
            raise TypeError("MoveKey jumped must be a tuple.")
        if not all(isinstance(jumped_sq, int) for jumped_sq in jumped):
            raise TypeError("MoveKey jumped must contain ints.")
        if jumped and len(jumped) != len(landings):
            raise TypeError("Capture MoveKey must satisfy len(jumped) == len(landings).")
        if not jumped and len(landings) != 1:
            raise TypeError("Quiet MoveKey must contain exactly one landing square.")
        if len(set(jumped)) != len(jumped):
            raise TypeError("Capture MoveKey cannot repeat jumped squares.")
        if start_sq in landings:
            raise TypeError("MoveKey start square cannot appear in landings.")
        if not isinstance(promotes, bool):
            raise TypeError("MoveKey promote flag must be bool.")

        return action

    def _apply_move(self, state: CheckersState, move: MoveKey) -> CheckersState:
        """Apply a move and return the next state.

        This placeholder only flips side to move. Piece updates are intentionally
        left for the concrete move generator/bitboard implementation.
        """
        _ = move
        return CheckersState(
            wm=state.wm,
            wk=state.wk,
            bm=state.bm,
            bk=state.bk,
            turn=(
                valanga.Color.BLACK
                if state.turn == valanga.Color.WHITE
                else valanga.Color.WHITE
            ),
            ply_since_capture_or_man_move=state.ply_since_capture_or_man_move + 1,
        )
