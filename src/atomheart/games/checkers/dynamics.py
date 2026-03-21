"""Valanga Dynamics adapter for checkers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

import valanga

from .apply import apply_move
from .generation import generate_legal_moves
from .move import CheckersMoveGenerator, MoveKey, move_name
from .rules import CheckersRules
from .state import CheckersState


@dataclass(slots=True)
class CheckersDynamics(valanga.Dynamics[CheckersState]):
    """Checkers dynamics with legal move generation and state transitions."""

    rules: CheckersRules = field(default_factory=CheckersRules)

    def legal_actions(
        self, state: CheckersState
    ) -> valanga.BranchKeyGeneratorP[MoveKey]:
        """Return legal move keys for the state."""
        moves = generate_legal_moves(state=state, rules=self.rules)
        return CheckersMoveGenerator(moves, sort_branch_keys=True)

    def step(
        self, state: CheckersState, action: valanga.BranchKey
    ) -> valanga.Transition[CheckersState]:
        """Apply an action and return a transition."""
        move = self._as_move_key(action)
        next_state = self._apply_move(state, move)

        over_event: valanga.OverEvent[valanga.Role] | None = None
        is_over = False

        if next_state.is_game_over():
            is_over = True
            winner = (
                valanga.Color.BLACK
                if (next_state.wm | next_state.wk) == 0
                else valanga.Color.WHITE
            )
            over_event = valanga.OverEvent(
                outcome=valanga.Outcome.WIN,
                termination="piece_exhaustion",  # type: ignore[arg-type]
                winner=winner,
            )
        else:
            next_moves = self.legal_actions(next_state).get_all()
            if len(next_moves) == 0:
                is_over = True
                winner = (
                    valanga.Color.BLACK
                    if next_state.turn == valanga.Color.WHITE
                    else valanga.Color.WHITE
                )
                over_event = valanga.OverEvent(
                    outcome=valanga.Outcome.WIN,
                    termination="no_moves",  # type: ignore[arg-type]
                    winner=winner,
                )

        return valanga.Transition(
            next_state=next_state,
            modifications=None,
            is_over=is_over,
            over_event=over_event,
            info={"move": move_name(move)},
        )

    def action_name(self, state: CheckersState, action: valanga.BranchKey) -> str:
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
    def _as_move_key(action: valanga.BranchKey) -> MoveKey:
        """Type-check and normalize branch key to a checkers move key."""
        if not isinstance(action, tuple) or len(action) != 4:  # pyright: ignore[reportUnknownArgumentType]
            raise TypeError("Checkers actions must be MoveKey tuples.")  # noqa: TRY003

        move_key = cast("MoveKey", action)
        start_sq, landings, jumped, promotes = move_key

        if not isinstance(start_sq, int):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("MoveKey start square must be int.")  # noqa: TRY003
        if not isinstance(landings, tuple) or not landings:  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("MoveKey landings must be a non-empty tuple.")  # noqa: TRY003
        if not all(isinstance(landing_sq, int) for landing_sq in landings):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("MoveKey landings must contain ints.")  # noqa: TRY003
        if not isinstance(jumped, tuple):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("MoveKey jumped must be a tuple.")  # noqa: TRY003
        if not all(isinstance(jumped_sq, int) for jumped_sq in jumped):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("MoveKey jumped must contain ints.")  # noqa: TRY003
        if jumped and len(jumped) != len(landings):
            raise TypeError(  # noqa: TRY003
                "Capture MoveKey must satisfy len(jumped) == len(landings)."
            )
        if not jumped and len(landings) != 1:
            raise TypeError("Quiet MoveKey must contain exactly one landing square.")  # noqa: TRY003
        if len(set(jumped)) != len(jumped):
            raise TypeError("Capture MoveKey cannot repeat jumped squares.")  # noqa: TRY003
        if start_sq in landings:
            raise TypeError("MoveKey start square cannot appear in landings.")  # noqa: TRY003
        if not isinstance(promotes, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("MoveKey promote flag must be bool.")  # noqa: TRY003

        return move_key

    def _apply_move(self, state: CheckersState, move: MoveKey) -> CheckersState:
        """Apply a move and return the next state."""
        return apply_move(state=state, move=move, rules=self.rules)
