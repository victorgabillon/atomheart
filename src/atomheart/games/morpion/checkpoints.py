"""Checkpoint codec for Morpion states."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, cast

from .dynamics import DIRECTIONS, MorpionDynamics
from .state import MorpionState, Variant, initial_state

if TYPE_CHECKING:
    from .canonical import Move
    from .state import Point


class StateCheckpointCodecBase[StateT](Protocol):
    """Structural checkpoint protocol matching Valanga's state codec interface."""

    def dump_state_ref(self, state: StateT) -> object:
        """Return a checkpoint payload for one state."""
        ...

    def load_state_ref(self, payload: object) -> StateT:
        """Rebuild one state from a checkpoint payload."""
        ...


type MorpionMovePayload = list[int]
type MorpionAction = tuple[int, int, int, int]


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
    def illegal_move(cls, index: int, move: Move) -> MorpionCheckpointError:
        """Return the illegal-move replay error."""
        return cls(f"Illegal Morpion checkpoint move at index {index}: {move!r}")


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


def _action_for_move(state: MorpionState, move: Move) -> MorpionAction:
    """Return the Morpion action that plays ``move`` from ``state``."""
    points = _move_points(move)
    missing_indexes = [
        index for index, point in enumerate(points) if point not in state.points
    ]
    if len(missing_indexes) != 1:
        raise MorpionCheckpointError.move_not_replayable(move)

    direction = (
        points[1][0] - points[0][0],
        points[1][1] - points[0][1],
    )
    return (
        DIRECTIONS.index(direction),
        points[0][0],
        points[0][1],
        missing_indexes[0],
    )


def _ordered_played_moves(state: MorpionState) -> tuple[Move, ...]:
    """Recover one deterministic replay order for the state's played moves."""
    if len(state.played_moves) != state.moves:
        raise MorpionCheckpointError.incomplete_history()

    dynamics = MorpionDynamics()
    replay_state: MorpionState = initial_state(state.variant)
    remaining_moves = set(state.played_moves)
    ordered_moves: list[Move] = []

    while remaining_moves:
        for move in sorted(remaining_moves):
            try:
                action = _action_for_move(replay_state, move)
                transition_object = cast("object", dynamics.step(replay_state, action))
                next_state = _transition_next_state(transition_object)
            except ValueError:
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


class MorpionStateCheckpointCodec(StateCheckpointCodecBase[MorpionState]):
    """Serialize Morpion states through a replayable move sequence."""

    def dump_state_ref(self, state: MorpionState) -> object:
        """Return a reversible checkpoint payload for one Morpion state."""
        return {
            "variant": state.variant.value,
            "played_moves": [_dump_move(move) for move in _ordered_played_moves(state)],
        }

    def load_state_ref(self, payload: object) -> MorpionState:
        """Rebuild one Morpion state by replaying checkpointed moves."""
        data = _payload_mapping(payload)
        variant = _payload_variant(data)
        serialized_moves = _payload_played_moves(data)

        dynamics = MorpionDynamics()
        state: MorpionState = initial_state(variant)
        for index, serialized_move in enumerate(serialized_moves):
            move = _load_move(serialized_move, index=index)
            try:
                action = _action_for_move(state, move)
                transition_object = cast("object", dynamics.step(state, action))
                next_state = _transition_next_state(transition_object)
                state = next_state
            except ValueError as exc:
                raise MorpionCheckpointError.illegal_move(index, move) from exc

        return state


__all__ = ["MorpionStateCheckpointCodec"]
