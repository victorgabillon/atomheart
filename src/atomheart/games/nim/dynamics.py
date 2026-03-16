"""Valanga dynamics adapter for the Nim game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import valanga
from valanga.over_event import HowOver, Winner

from atomheart.games._branch_key_gen import TupleBranchKeyGen

from .state import NimState

type NimAction = Literal[1, 2, 3]

_NO_ACTIONS: tuple[NimAction, ...] = ()
_ONE_ACTION: tuple[NimAction, ...] = (1,)
_TWO_ACTIONS: tuple[NimAction, ...] = (1, 2)
_ALL_ACTIONS: tuple[NimAction, ...] = (1, 2, 3)


def _other_turn(turn: valanga.Color) -> valanga.Color:
    """Return the opposite side to move."""
    return valanga.Color.BLACK if turn == valanga.Color.WHITE else valanga.Color.WHITE


def _winner_for_turn(turn: valanga.Color) -> Winner:
    """Return the Valanga winner enum for the moving side."""
    return Winner.WHITE if turn == valanga.Color.WHITE else Winner.BLACK


@dataclass(slots=True)
class NimDynamics(valanga.Dynamics[NimState]):
    """Rule engine for deterministic single-pile Nim transitions."""

    def legal_actions(
        self,
        state: NimState,
    ) -> valanga.BranchKeyGeneratorP[NimAction]:
        """Return legal actions for ``state`` in increasing order."""
        return TupleBranchKeyGen(self._legal_actions_for_state(state))

    def step(
        self,
        state: NimState,
        action: valanga.BranchKey,
    ) -> valanga.Transition[NimState]:
        """Apply an action and return transition metadata."""
        normalized_action = self._as_action(action)
        if normalized_action not in self._legal_actions_for_state(state):
            raise ValueError(  # noqa: TRY003
                f"Illegal Nim action {normalized_action!r} for {state.pprint()}."
            )

        next_state = NimState(
            stones=state.stones - normalized_action,
            turn=_other_turn(state.turn),
        )
        is_over = next_state.is_game_over()

        over_event: valanga.OverEvent | None = None
        if is_over:
            # The player who just moved takes the last stone and wins, even
            # though ``next_state.turn`` already points to the opponent.
            over_event = valanga.OverEvent(
                HowOver.WIN,
                _winner_for_turn(state.turn),
                "last_stone",  # type: ignore[arg-type]
            )

        transition_info = {"action": normalized_action}
        return valanga.Transition(
            next_state=next_state,
            is_over=is_over,
            over_event=over_event,
            modifications=None,
            info=transition_info,
        )

    def action_name(self, state: NimState, action: valanga.BranchKey) -> str:
        """Return the canonical string name for an action key."""
        _ = state
        return str(self._as_action(action))

    def action_from_name(self, state: NimState, name: str) -> NimAction:
        """Parse a canonical action name and validate it for ``state``."""
        if name not in ("1", "2", "3"):
            raise ValueError(f"Unknown Nim action name: {name!r}.")  # noqa: TRY003

        action: NimAction
        if name == "1":
            action = 1
        elif name == "2":
            action = 2
        else:
            action = 3

        if action not in self._legal_actions_for_state(state):
            raise ValueError(  # noqa: TRY003
                f"No legal Nim action named {name!r} for {state.pprint()}."
            )
        return action

    @staticmethod
    def _as_action(action: valanga.BranchKey) -> NimAction:
        """Validate and normalize a generic branch key to a Nim action."""
        if action.__class__ is not int:
            raise TypeError("Nim actions must be ints.")  # noqa: TRY003
        if action not in _ALL_ACTIONS:
            raise TypeError("Nim actions must be 1, 2, or 3.")  # noqa: TRY003
        if action == 1:
            return 1
        if action == 2:
            return 2
        return 3

    @staticmethod
    def _legal_actions_for_state(state: NimState) -> tuple[NimAction, ...]:
        """Return the legal action tuple for a state."""
        if state.stones == 0:
            return _NO_ACTIONS
        if state.stones == 1:
            return _ONE_ACTION
        if state.stones == 2:
            return _TWO_ACTIONS
        return _ALL_ACTIONS
