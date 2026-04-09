"""Checkpoint codec for Morpion states."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import valanga

from .canonical import Move
from .dynamics import DIRECTIONS, MorpionDynamics
from .state import MorpionState, Point, Variant, initial_state

try:
    from valanga import StateCheckpointCodec
except ImportError:
    from typing import Protocol

    class StateCheckpointCodec[StateT: valanga.State](Protocol):
        """Fallback checkpoint protocol for older ``valanga`` releases."""

        def dump_state_ref(self, state: StateT) -> object:
            """Return a checkpoint payload for one state."""
            ...

        def load_state_ref(self, payload: object) -> StateT:
            """Rebuild one state from a checkpoint payload."""
            ...


type MorpionMovePayload = list[int]
type MorpionAction = tuple[int, int, int, int]


def _is_int(value: object) -> bool:
    """Return whether ``value`` is an integer but not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _move_points(move: Move) -> tuple[Point, Point, Point, Point, Point]:
    """Expand one endpoint move into the five lattice points on its line."""
    x1, y1, x2, y2 = move
    dx = x2 - x1
    dy = y2 - y1
    if dx % 4 != 0 or dy % 4 != 0:
        raise ValueError(f"Morpion checkpoint move must span four unit steps: {move!r}")

    step = (dx // 4, dy // 4)
    if step not in DIRECTIONS:
        raise ValueError(f"Unsupported Morpion checkpoint move direction: {move!r}")

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
    if not isinstance(payload, Sequence) or isinstance(payload, str | bytes | bytearray):
        raise ValueError(
            f"Morpion checkpoint move at index {index} must be a four-integer sequence."
        )

    values = tuple(payload)
    if len(values) != 4 or not all(_is_int(value) for value in values):
        raise ValueError(
            f"Morpion checkpoint move at index {index} must be a four-integer sequence."
        )

    x1, y1, x2, y2 = values
    move = (x1, y1, x2, y2) if (x1, y1) <= (x2, y2) else (x2, y2, x1, y1)
    _move_points(move)
    return move


def _action_for_move(state: MorpionState, move: Move) -> MorpionAction:
    """Return the Morpion action that plays ``move`` from ``state``."""
    points = _move_points(move)
    missing_indexes = [index for index, point in enumerate(points) if point not in state.points]
    if len(missing_indexes) != 1:
        raise ValueError(
            f"Morpion checkpoint move is not replayable from the current state: {move!r}"
        )

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
        raise ValueError(
            "Morpion checkpoint codec requires a complete played_moves history."
        )

    dynamics = MorpionDynamics()
    replay_state = initial_state(state.variant)
    remaining_moves = set(state.played_moves)
    ordered_moves: list[Move] = []

    while remaining_moves:
        for move in sorted(remaining_moves):
            try:
                action = _action_for_move(replay_state, move)
                next_state = dynamics.step(replay_state, action).next_state
            except ValueError:
                continue
            ordered_moves.append(move)
            replay_state = next_state
            remaining_moves.remove(move)
            break
        else:
            raise ValueError(
                "Morpion checkpoint codec could not derive a replay order from "
                "state.played_moves."
            )

    if replay_state != state:
        raise ValueError(
            "Morpion checkpoint codec could not reconstruct the provided state "
            "exactly from played_moves."
        )

    return tuple(ordered_moves)


def _payload_mapping(payload: object) -> Mapping[str, object]:
    """Validate that one checkpoint payload is mapping-shaped."""
    if not isinstance(payload, Mapping):
        raise ValueError("Morpion checkpoint payload must be a mapping.")
    return payload


def _payload_variant(data: Mapping[str, object]) -> Variant:
    """Extract and validate the Morpion variant from one payload."""
    if "variant" not in data:
        raise ValueError("Morpion checkpoint payload is missing 'variant'.")

    raw_variant = data["variant"]
    if not isinstance(raw_variant, str):
        raise ValueError("Morpion checkpoint payload field 'variant' must be a string.")

    try:
        return Variant(raw_variant)
    except ValueError as exc:
        raise ValueError(f"Unknown Morpion checkpoint variant: {raw_variant!r}") from exc


def _payload_played_moves(data: Mapping[str, object]) -> Sequence[object]:
    """Extract and validate the serialized move sequence from one payload."""
    if "played_moves" not in data:
        raise ValueError("Morpion checkpoint payload is missing 'played_moves'.")

    raw_moves = data["played_moves"]
    if not isinstance(raw_moves, Sequence) or isinstance(
        raw_moves, str | bytes | bytearray
    ):
        raise ValueError(
            "Morpion checkpoint payload field 'played_moves' must be a sequence."
        )
    return raw_moves


class MorpionStateCheckpointCodec(StateCheckpointCodec[MorpionState]):
    """Serialize Morpion states through a replayable move sequence."""

    def dump_state_ref(self, state: MorpionState) -> object:
        """Return a reversible checkpoint payload for one Morpion state."""
        return {
            "variant": state.variant.value,
            "played_moves": [
                _dump_move(move) for move in _ordered_played_moves(state)
            ],
        }

    def load_state_ref(self, payload: object) -> MorpionState:
        """Rebuild one Morpion state by replaying checkpointed moves."""
        data = _payload_mapping(payload)
        variant = _payload_variant(data)
        serialized_moves = _payload_played_moves(data)

        dynamics = MorpionDynamics()
        state = initial_state(variant)
        for index, serialized_move in enumerate(serialized_moves):
            move = _load_move(serialized_move, index=index)
            try:
                action = _action_for_move(state, move)
                state = dynamics.step(state, action).next_state
            except ValueError as exc:
                raise ValueError(
                    f"Illegal Morpion checkpoint move at index {index}: {move!r}"
                ) from exc

        return state


__all__ = ["MorpionStateCheckpointCodec"]
