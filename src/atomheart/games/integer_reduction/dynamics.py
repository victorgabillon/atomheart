"""Valanga dynamics adapter for the integer reduction game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import valanga
from valanga.over_event import HowOver, Winner

from .state import IntegerReductionState

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

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


class _ActionBranchKeyGen(valanga.BranchKeyGeneratorP[IntegerReductionAction]):
    """Small resettable in-memory branch-key generator."""

    sort_branch_keys: bool = False

    def __init__(self, actions: Sequence[IntegerReductionAction]) -> None:
        """Store action keys for deterministic iteration."""
        self._actions = tuple(actions)
        self._index = 0

    @property
    def all_generated_keys(self) -> Sequence[IntegerReductionAction] | None:
        """Return all action keys known to this generator."""
        return self._actions

    def __iter__(self) -> Iterator[IntegerReductionAction]:
        """Return the iterator protocol self."""
        return self

    def __next__(self) -> IntegerReductionAction:
        """Return the next action key or raise ``StopIteration``."""
        if self._index >= len(self._actions):
            raise StopIteration
        action = self._actions[self._index]
        self._index += 1
        return action

    def more_than_one(self) -> bool:
        """Return whether more than one action is available."""
        return len(self._actions) > 1

    def get_all(self) -> Sequence[IntegerReductionAction]:
        """Return all action keys as a new list."""
        return list(self._actions)

    def copy_with_reset(self) -> _ActionBranchKeyGen:
        """Return a fresh generator reset to the first action."""
        return _ActionBranchKeyGen(self._actions)


def _build_transition(
    next_state: IntegerReductionState,
    *,
    is_over: bool,
    over_event: valanga.OverEvent | None,
    action: IntegerReductionAction,
) -> valanga.Transition[IntegerReductionState]:
    """Build transition metadata for integer reduction."""
    transition_info = {"action": action}
    return valanga.Transition(
        next_state,
        modifications=None,
        info=transition_info,
        is_over=is_over,
        over_event=over_event,
    )


@dataclass(slots=True)
class IntegerReductionDynamics(valanga.Dynamics[IntegerReductionState]):
    """Rule engine for deterministic integer reduction transitions."""

    def legal_actions(
        self,
        state: IntegerReductionState,
    ) -> valanga.BranchKeyGeneratorP[IntegerReductionAction]:
        """Return legal actions for ``state`` in deterministic order."""
        return _ActionBranchKeyGen(self._legal_actions_for_state(state))

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

        over_event: valanga.OverEvent | None = None
        if is_over:
            # Valanga's OverEvent is two-player-oriented; we encode one-player
            # completion as a draw with no winner and a simple termination tag.
            over_event = valanga.OverEvent(
                HowOver.DRAW,
                Winner.NO_KNOWN_WINNER,
                "reached_one",  # type: ignore[arg-type]
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
