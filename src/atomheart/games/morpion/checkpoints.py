"""Incremental checkpoint codec for Morpion states.

This codec uses a replayable move-history anchor for the first incremental
implementation. For Morpion, that keeps the anchor payload explicit,
self-sufficient, and domain-meaningful without serializing a large opaque
Python object or duplicating the board geometry fields directly. The
parent-based delta path is kept separate and efficient: one child delta is just
the single move that transforms a concrete parent state into its child.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, TypedDict, cast, runtime_checkable

import valanga

try:
    from valanga.checkpoints import StateCheckpointCodec as ValangaStateCheckpointCodec
except ImportError:

    @runtime_checkable
    class ValangaStateCheckpointCodec[StateT: valanga.State = valanga.State](Protocol):
        """Fallback mirror of Valanga's basic checkpoint codec protocol."""

        def dump_state_ref(self, state: StateT) -> object:
            """Return a checkpoint payload for one state."""
            ...

        def load_state_ref(self, payload: object) -> StateT:
            """Rebuild one state from a checkpoint payload."""
            ...


try:
    from valanga.checkpoints import (
        IncrementalStateCheckpointCodec as ValangaIncrementalStateCheckpointCodec,
    )
    from valanga.checkpoints import (
        StateCheckpointSummaryCodec as ValangaStateCheckpointSummaryCodec,
    )
except ImportError:

    @runtime_checkable
    class ValangaIncrementalStateCheckpointCodec[
        StateT: valanga.State = valanga.State
    ](Protocol):
        """Fallback mirror of Valanga's incremental checkpoint protocol."""

        def dump_anchor_ref(self, state: StateT) -> object:
            """Serialize one anchor snapshot reference for ``state``."""
            ...

        def dump_delta_from_parent(
            self,
            *,
            parent_state: StateT,
            child_state: StateT,
            branch_from_parent: valanga.BranchKey | None = None,
        ) -> object:
            """Serialize one child delta relative to a concrete parent state."""
            ...

        def load_anchor_ref(self, anchor_ref: object) -> StateT:
            """Restore one concrete state from an anchor snapshot reference."""
            ...

        def load_child_from_delta(
            self,
            *,
            parent_state: StateT,
            delta_ref: object,
            branch_from_parent: valanga.BranchKey | None = None,
        ) -> StateT:
            """Restore one child state by applying ``delta_ref`` to ``parent_state``."""
            ...


    @runtime_checkable
    class ValangaStateCheckpointSummaryCodec[
        StateT: valanga.State = valanga.State
    ](Protocol):
        """Fallback mirror of Valanga's summary codec protocol."""

        def dump_state_summary(self, state: StateT) -> object:
            """Serialize lightweight checkpoint metadata for ``state``."""
            ...

from .dynamics import (
    DIRECTIONS,
    MorpionDynamics,
    action_to_played_move,
    played_move_to_action,
)
from .state import MorpionState, Variant, initial_state

if TYPE_CHECKING:
    from .canonical import Move
    from .state import Point

type MorpionMovePayload = list[int]


class MorpionAnchorPayload(TypedDict):
    """Self-sufficient Morpion anchor payload.

    The first incremental implementation keeps anchors as ordered move history.
    That is slower to restore than a direct geometry snapshot, but it is clean,
    stable, and already matches the domain's reversible representation.
    """

    variant: str
    played_moves: list[MorpionMovePayload]


class MorpionDeltaPayload(TypedDict):
    """Parent-relative Morpion delta payload."""

    move: MorpionMovePayload


@dataclass(frozen=True, slots=True)
class MorpionCheckpointStateSummary:
    """Small checkpoint summary for Morpion states."""

    tag: int
    is_terminal: bool


class MorpionCheckpointError(ValueError):
    """Raised when a Morpion checkpoint is semantically invalid."""

    @classmethod
    def move_must_span_four_steps(cls, move: Move) -> MorpionCheckpointError:
        """Return the invalid move-span error."""
        return cls(f"Morpion checkpoint move must span four unit steps: {move!r}")

    @classmethod
    def unsupported_move_direction(cls, move: Move) -> MorpionCheckpointError:
        """Return the invalid move-direction error."""
        return cls(f"Unsupported Morpion checkpoint move direction: {move!r}")

    @classmethod
    def invalid_move_payload(cls, index: int) -> MorpionCheckpointError:
        """Return the malformed move-payload error."""
        return cls(
            f"Morpion checkpoint move at index {index} must be a four-integer sequence."
        )

    @classmethod
    def move_not_replayable(cls, move: Move) -> MorpionCheckpointError:
        """Return the unreplayable-move error."""
        return cls(
            "Morpion checkpoint move is not replayable from the current state: "
            f"{move!r}"
        )

    @classmethod
    def incomplete_history(cls) -> MorpionCheckpointError:
        """Return the incomplete-history error."""
        return cls("Morpion checkpoint codec requires a complete played_moves history.")

    @classmethod
    def could_not_derive_replay_order(cls) -> MorpionCheckpointError:
        """Return the replay-order reconstruction error."""
        return cls(
            "Morpion checkpoint codec could not derive a replay order from "
            "state.played_moves."
        )

    @classmethod
    def could_not_reconstruct_state(cls) -> MorpionCheckpointError:
        """Return the exact-reconstruction error."""
        return cls(
            "Morpion checkpoint codec could not reconstruct the provided state "
            "exactly from played_moves."
        )

    @classmethod
    def missing_variant(cls) -> MorpionCheckpointError:
        """Return the missing-variant error."""
        return cls("Morpion checkpoint payload is missing 'variant'.")

    @classmethod
    def unknown_variant(cls, raw_variant: str) -> MorpionCheckpointError:
        """Return the unknown-variant error."""
        return cls(f"Unknown Morpion checkpoint variant: {raw_variant!r}")

    @classmethod
    def missing_played_moves(cls) -> MorpionCheckpointError:
        """Return the missing move-sequence error."""
        return cls("Morpion checkpoint payload is missing 'played_moves'.")

    @classmethod
    def missing_delta_move(cls) -> MorpionCheckpointError:
        """Return the missing delta-move error."""
        return cls("Morpion checkpoint delta payload is missing 'move'.")

    @classmethod
    def illegal_move(cls, index: int, move: Move) -> MorpionCheckpointError:
        """Return the illegal-move replay error."""
        return cls(f"Illegal Morpion checkpoint move at index {index}: {move!r}")

    @classmethod
    def child_must_extend_parent_by_one_move(cls) -> MorpionCheckpointError:
        """Return the invalid parent-child relation error."""
        return cls(
            "Morpion checkpoint delta requires child_state to extend "
            "parent_state by exactly one move."
        )

    @classmethod
    def branch_does_not_match_delta(
        cls, *, move: Move, branch_from_parent: valanga.BranchKey
    ) -> MorpionCheckpointError:
        """Return the inconsistent branch/delta error."""
        return cls(
            "Morpion checkpoint delta move does not match branch_from_parent: "
            f"{move!r} vs {branch_from_parent!r}"
        )

    @classmethod
    def child_does_not_match_delta(cls) -> MorpionCheckpointError:
        """Return the inconsistent concrete-child error."""
        return cls(
            "Morpion checkpoint delta could not reconstruct the provided child_state "
            "from parent_state."
        )


class MorpionCheckpointTypeError(TypeError):
    """Raised when a Morpion checkpoint payload has the wrong type."""

    @classmethod
    def payload_must_be_mapping(cls) -> MorpionCheckpointTypeError:
        """Return the payload-type error."""
        return cls("Morpion checkpoint payload must be a mapping.")

    @classmethod
    def variant_must_be_string(cls) -> MorpionCheckpointTypeError:
        """Return the variant-type error."""
        return cls("Morpion checkpoint payload field 'variant' must be a string.")

    @classmethod
    def played_moves_must_be_sequence(cls) -> MorpionCheckpointTypeError:
        """Return the move-sequence-type error."""
        return cls(
            "Morpion checkpoint payload field 'played_moves' must be a sequence."
        )

    @classmethod
    def move_payload_must_be_sequence(cls, index: int) -> MorpionCheckpointTypeError:
        """Return the move-payload-type error."""
        return cls(
            f"Morpion checkpoint move at index {index} must be a four-integer sequence."
        )

    @classmethod
    def transition_must_expose_next_state(cls) -> MorpionCheckpointTypeError:
        """Return the transition-shape error."""
        return cls("Morpion dynamics transition must expose a MorpionState next_state.")


_DYNAMICS = MorpionDynamics()


def _is_int(value: object) -> bool:
    """Return whether ``value`` is an integer but not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _payload_int(value: object, *, index: int) -> int:
    """Validate one serialized integer payload field."""
    if not _is_int(value):
        raise MorpionCheckpointError.invalid_move_payload(index)
    return cast("int", value)


def _transition_next_state(transition: object) -> MorpionState:
    """Return the typed Morpion successor state from one dynamics transition."""
    next_state = getattr(transition, "next_state", None)
    if not isinstance(next_state, MorpionState):
        raise MorpionCheckpointTypeError.transition_must_expose_next_state()
    return next_state


def _move_points(move: Move) -> tuple[Point, Point, Point, Point, Point]:
    """Expand one endpoint move into the five lattice points on its line."""
    x1, y1, x2, y2 = move
    dx = x2 - x1
    dy = y2 - y1
    if dx % 4 != 0 or dy % 4 != 0:
        raise MorpionCheckpointError.move_must_span_four_steps(move)

    step = (dx // 4, dy // 4)
    if step not in DIRECTIONS:
        raise MorpionCheckpointError.unsupported_move_direction(move)

    return (
        (x1, y1),
        (x1 + step[0], y1 + step[1]),
        (x1 + 2 * step[0], y1 + 2 * step[1]),
        (x1 + 3 * step[0], y1 + 3 * step[1]),
        (x2, y2),
    )


def _dump_move(move: Move) -> MorpionMovePayload:
    """Serialize one Morpion move into a JSON-friendly payload."""
    return [move[0], move[1], move[2], move[3]]


def _load_move(payload: object, *, index: int) -> Move:
    """Deserialize and validate one Morpion move payload."""
    if not isinstance(payload, Sequence) or isinstance(
        payload, str | bytes | bytearray
    ):
        raise MorpionCheckpointTypeError.move_payload_must_be_sequence(index)

    validated_payload = cast("Sequence[object]", payload)
    values: list[object] = list(validated_payload)
    if len(values) != 4 or not all(_is_int(value) for value in values):
        raise MorpionCheckpointError.invalid_move_payload(index)

    x1 = _payload_int(values[0], index=index)
    y1 = _payload_int(values[1], index=index)
    x2 = _payload_int(values[2], index=index)
    y2 = _payload_int(values[3], index=index)
    move = (x1, y1, x2, y2) if (x1, y1) <= (x2, y2) else (x2, y2, x1, y1)
    _move_points(move)
    return move


def _apply_move(state: MorpionState, move: Move, *, index: int) -> MorpionState:
    """Apply one serialized move to ``state`` and return the concrete child."""
    try:
        action = played_move_to_action(state, move)
        transition_object = cast("object", _DYNAMICS.step(state, action))
        return _transition_next_state(transition_object)
    except ValueError as exc:
        raise MorpionCheckpointError.illegal_move(index, move) from exc


def _ordered_played_moves(state: MorpionState) -> tuple[Move, ...]:
    """Recover one deterministic replay order for the state's played moves."""
    if len(state.played_moves) != state.moves:
        raise MorpionCheckpointError.incomplete_history()

    replay_state: MorpionState = initial_state(state.variant)
    remaining_moves = set(state.played_moves)
    ordered_moves: list[Move] = []

    while remaining_moves:
        for move in sorted(remaining_moves):
            try:
                next_state = _apply_move(replay_state, move, index=len(ordered_moves))
            except MorpionCheckpointError:
                continue
            ordered_moves.append(move)
            replay_state = next_state
            remaining_moves.remove(move)
            break
        else:
            raise MorpionCheckpointError.could_not_derive_replay_order()

    if replay_state != state:
        raise MorpionCheckpointError.could_not_reconstruct_state()

    return tuple(ordered_moves)


def _payload_mapping(payload: object) -> dict[str, object]:
    """Validate that one checkpoint payload is mapping-shaped."""
    if not isinstance(payload, Mapping):
        raise MorpionCheckpointTypeError.payload_must_be_mapping()

    raw_payload = cast("Mapping[object, object]", payload)
    data: dict[str, object] = {}
    for key_obj, value_obj in raw_payload.items():
        if not isinstance(key_obj, str):
            raise MorpionCheckpointTypeError.payload_must_be_mapping()
        data[key_obj] = value_obj
    return data


def _payload_variant(data: Mapping[str, object]) -> Variant:
    """Extract and validate the Morpion variant from one payload."""
    if "variant" not in data:
        raise MorpionCheckpointError.missing_variant()

    raw_variant = data["variant"]
    if not isinstance(raw_variant, str):
        raise MorpionCheckpointTypeError.variant_must_be_string()

    try:
        return Variant(raw_variant)
    except ValueError as exc:
        raise MorpionCheckpointError.unknown_variant(raw_variant) from exc


def _payload_played_moves(data: Mapping[str, object]) -> list[object]:
    """Extract and validate the serialized move sequence from one payload."""
    if "played_moves" not in data:
        raise MorpionCheckpointError.missing_played_moves()

    raw_moves = data["played_moves"]
    if not isinstance(raw_moves, Sequence) or isinstance(
        raw_moves, str | bytes | bytearray
    ):
        raise MorpionCheckpointTypeError.played_moves_must_be_sequence()
    validated_moves = cast("Sequence[object]", raw_moves)
    return list(validated_moves)


def _payload_delta_move(data: Mapping[str, object]) -> object:
    """Extract the serialized move from one delta payload."""
    if "move" not in data:
        raise MorpionCheckpointError.missing_delta_move()
    return data["move"]


def _dump_anchor_payload(state: MorpionState) -> MorpionAnchorPayload:
    """Serialize one Morpion state as a self-sufficient anchor snapshot."""
    return {
        "variant": state.variant.value,
        "played_moves": [_dump_move(move) for move in _ordered_played_moves(state)],
    }


def _replay_anchor_payload(payload: object) -> MorpionState:
    """Restore one concrete Morpion state from an anchor payload."""
    data = _payload_mapping(payload)
    variant = _payload_variant(data)
    serialized_moves = _payload_played_moves(data)

    state: MorpionState = initial_state(variant)
    for index, serialized_move in enumerate(serialized_moves):
        move = _load_move(serialized_move, index=index)
        state = _apply_move(state, move, index=index)
    return state


def _validate_branch_matches_move(
    *, move: Move, branch_from_parent: valanga.BranchKey | None
) -> None:
    """Ensure a provided parent branch encodes the same Morpion move."""
    if branch_from_parent is None:
        return
    branch_move = action_to_played_move(branch_from_parent)
    if branch_move != move:
        raise MorpionCheckpointError.branch_does_not_match_delta(
            move=move,
            branch_from_parent=branch_from_parent,
        )


def _child_move_from_parent(
    *,
    parent_state: MorpionState,
    child_state: MorpionState,
    branch_from_parent: valanga.BranchKey | None,
) -> Move:
    """Derive the single replayable child move relative to ``parent_state``."""
    if len(parent_state.played_moves) != parent_state.moves:
        raise MorpionCheckpointError.incomplete_history()
    if len(child_state.played_moves) != child_state.moves:
        raise MorpionCheckpointError.incomplete_history()
    if child_state.variant != parent_state.variant:
        raise MorpionCheckpointError.child_must_extend_parent_by_one_move()
    if child_state.moves != parent_state.moves + 1:
        raise MorpionCheckpointError.child_must_extend_parent_by_one_move()
    if not parent_state.played_moves < child_state.played_moves:
        raise MorpionCheckpointError.child_must_extend_parent_by_one_move()

    new_moves = child_state.played_moves - parent_state.played_moves
    if len(new_moves) != 1:
        raise MorpionCheckpointError.child_must_extend_parent_by_one_move()
    move = next(iter(new_moves))

    _validate_branch_matches_move(
        move=move,
        branch_from_parent=branch_from_parent,
    )

    reconstructed_child = _apply_move(parent_state, move, index=0)
    if reconstructed_child != child_state:
        raise MorpionCheckpointError.child_does_not_match_delta()
    return move


class MorpionStateCheckpointCodec(
    ValangaStateCheckpointCodec[MorpionState],
    ValangaIncrementalStateCheckpointCodec[MorpionState],
    ValangaStateCheckpointSummaryCodec[MorpionState],
):
    """Serialize Morpion states via replay anchors plus one-move deltas.

    The anchor format intentionally remains replay-based for this first
    incremental codec version:

    - anchors store ``variant`` plus a deterministic ordered ``played_moves``
      sequence, which is explicit and self-sufficient;
    - deltas store exactly one serialized move relative to a concrete parent;
    - summaries stay tiny and only expose stable checkpoint metadata.

    A direct geometry snapshot could later replace or supplement the anchor if
    restore speed becomes the priority, but the move-history anchor is the
    cleanest long-term-compatible first step because it reuses Morpion's native
    reversible identity.
    """

    def dump_state_ref(self, state: MorpionState) -> object:
        """Return the legacy state-ref payload as an anchor snapshot alias."""
        return self.dump_anchor_ref(state)

    def load_state_ref(self, payload: object) -> MorpionState:
        """Rebuild the legacy state-ref payload through the anchor path."""
        return self.load_anchor_ref(payload)

    def dump_anchor_ref(self, state: MorpionState) -> MorpionAnchorPayload:
        """Serialize one self-sufficient Morpion anchor snapshot."""
        return _dump_anchor_payload(state)

    def dump_delta_from_parent(
        self,
        *,
        parent_state: MorpionState,
        child_state: MorpionState,
        branch_from_parent: valanga.BranchKey | None = None,
    ) -> MorpionDeltaPayload:
        """Serialize one concrete Morpion child as a parent-relative delta."""
        move = _child_move_from_parent(
            parent_state=parent_state,
            child_state=child_state,
            branch_from_parent=branch_from_parent,
        )
        return {"move": _dump_move(move)}

    def load_anchor_ref(self, anchor_ref: object) -> MorpionState:
        """Restore one Morpion state from its self-sufficient anchor snapshot."""
        return _replay_anchor_payload(anchor_ref)

    def load_child_from_delta(
        self,
        *,
        parent_state: MorpionState,
        delta_ref: object,
        branch_from_parent: valanga.BranchKey | None = None,
    ) -> MorpionState:
        """Restore one Morpion child by applying a serialized move to its parent."""
        data = _payload_mapping(delta_ref)
        move = _load_move(_payload_delta_move(data), index=0)
        _validate_branch_matches_move(
            move=move,
            branch_from_parent=branch_from_parent,
        )
        return _apply_move(parent_state, move, index=0)

    def dump_state_summary(self, state: MorpionState) -> MorpionCheckpointStateSummary:
        """Serialize a small stable checkpoint summary for ``state``."""
        return MorpionCheckpointStateSummary(
            tag=state.tag,
            is_terminal=_DYNAMICS.is_terminal_state(state),
        )


__all__ = [
    "MorpionCheckpointStateSummary",
    "MorpionStateCheckpointCodec",
]
