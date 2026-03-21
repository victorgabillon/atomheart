"""Valanga dynamics adapter for the integer reduction game."""

# pylint: disable=duplicate-code

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import valanga

from atomheart.games._branch_key_gen import TupleBranchKeyGen

from .state import IntegerReductionState

type IntegerReductionAction = Literal["dec1", "half"]

_NO_ACTIONS: tuple[IntegerReductionAction, ...] = ()
_ODD_ACTIONS: tuple[IntegerReductionAction, ...] = ("dec1",)
_EVEN_ACTIONS: tuple[IntegerReductionAction, ...] = ("dec1", "half")


class IntegerReductionIllegalActionError(ValueError):
    """Raised when an action is not legal in the current state."""

    @classmethod
    def for_state(
        cls,
        action: IntegerReductionAction,
        state: IntegerReductionState,
    ) -> IntegerReductionIllegalActionError:
        """Build an illegal-action error for a specific state."""
        return cls(
            f"Illegal integer reduction action {action!r} for value {state.value}."
        )


class IntegerReductionActionNameError(ValueError):
    """Raised when parsing an action name fails."""

    @classmethod
    def unknown(cls, name: str) -> IntegerReductionActionNameError:
        """Build an error for an unknown action name."""
        return cls(f"Unknown integer reduction action name: {name!r}.")

    @classmethod
    def illegal_for_state(
        cls,
        name: str,
        state: IntegerReductionState,
    ) -> IntegerReductionActionNameError:
        """Build an error for a known but illegal action name."""
        return cls(
            f"No legal integer reduction action named {name!r} for value {state.value}."
        )


class IntegerReductionActionTypeError(TypeError):
    """Raised when a branch key is not a valid integer reduction action."""

    @classmethod
    def not_string(cls) -> IntegerReductionActionTypeError:
        """Build an error for a non-string action key."""
        return cls("Integer reduction actions must be strings.")

    @classmethod
    def invalid_name(cls) -> IntegerReductionActionTypeError:
        """Build an error for a string outside the closed action set."""
        return cls("Integer reduction actions must be 'dec1' or 'half'.")


def _build_transition(
    next_state: IntegerReductionState,
    *,
    is_over: bool,
    over_event: valanga.OverEvent[valanga.SoloRole] | None,
    action: IntegerReductionAction,
) -> valanga.Transition[IntegerReductionState]:
    """Build transition metadata for integer reduction."""
    transition_info = {"action": action}
    return valanga.Transition(
        next_state,
        modifications=None,
        info=transition_info,
        is_over=is_over,
        over_event=over_event,  # type: ignore[arg-type]
    )


@dataclass(slots=True)
class IntegerReductionDynamics(valanga.Dynamics[IntegerReductionState]):
    """Rule engine for deterministic integer reduction transitions."""

    def legal_actions(
        self,
        state: IntegerReductionState,
    ) -> valanga.BranchKeyGeneratorP[IntegerReductionAction]:
        """Return legal actions for ``state`` in deterministic order."""
        return TupleBranchKeyGen(self._legal_actions_for_state(state))

    def step(
        self,
        state: IntegerReductionState,
        action: valanga.BranchKey,
    ) -> valanga.Transition[IntegerReductionState]:
        """Apply an action and return transition metadata."""
        normalized_action = self._as_action(action)
        if normalized_action not in self._legal_actions_for_state(state):
            raise IntegerReductionIllegalActionError.for_state(normalized_action, state)

        if normalized_action == "dec1":
            next_value = state.value - 1
        else:
            next_value = state.value // 2
        next_state = IntegerReductionState(next_value)
        is_over = next_state.is_game_over()

        over_event: valanga.OverEvent[valanga.SoloRole] | None = None
        if is_over:
            # Reaching one is a successful terminal state without a role winner.
            over_event = valanga.OverEvent[valanga.SoloRole](
                outcome=valanga.Outcome.WIN,
                termination="reached_one",  # type: ignore[arg-type]
                winner=None,
            )

        return _build_transition(
            next_state,
            is_over=is_over,
            over_event=over_event,
            action=normalized_action,
        )

    def action_name(
        self,
        state: IntegerReductionState,
        action: valanga.BranchKey,
    ) -> str:
        """Return the canonical string name for an action key."""
        _ = state
        return self._as_action(action)

    def action_from_name(
        self,
        state: IntegerReductionState,
        name: str,
    ) -> IntegerReductionAction:
        """Parse a canonical action name and validate it for ``state``."""
        if name not in _EVEN_ACTIONS:
            raise IntegerReductionActionNameError.unknown(name)

        action: IntegerReductionAction
        action = "dec1" if name == "dec1" else "half"
        if action not in self._legal_actions_for_state(state):
            raise IntegerReductionActionNameError.illegal_for_state(name, state)
        return action

    @staticmethod
    def _as_action(action: valanga.BranchKey) -> IntegerReductionAction:
        """Validate and normalize a generic branch key to an action string."""
        if not isinstance(action, str):
            raise IntegerReductionActionTypeError.not_string()
        if action not in _EVEN_ACTIONS:
            raise IntegerReductionActionTypeError.invalid_name()
        if action == "dec1":
            return "dec1"
        return "half"

    @staticmethod
    def _legal_actions_for_state(
        state: IntegerReductionState,
    ) -> tuple[IntegerReductionAction, ...]:
        """Return the legal action tuple for a state."""
        if state.value == 1:
            return _NO_ACTIONS
        if state.value % 2 == 0:
            return _EVEN_ACTIONS
        return _ODD_ACTIONS
