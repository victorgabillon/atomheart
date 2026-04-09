"""Checkpoint codec tests for Morpion states."""

from __future__ import annotations

import pytest

from atomheart.games.morpion import (
    MorpionDynamics,
    MorpionState,
    MorpionStateCheckpointCodec,
    Variant,
    initial_state,
)


def _segment(
    a: tuple[int, int], b: tuple[int, int]
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return normalized segment endpoints."""
    return (a, b) if a <= b else (b, a)


def _state_after_n_moves(variant: Variant, moves_to_play: int) -> MorpionState:
    """Build one deterministic nontrivial Morpion state."""
    dynamics = MorpionDynamics()
    state = initial_state(variant)
    for _ in range(moves_to_play):
        action = dynamics.legal_actions(state).get_all()[0]
        state = dynamics.step(state, action).next_state
    return state


def _legacy_state_without_history() -> MorpionState:
    """Build one handcrafted state that lacks a reversible move history."""
    return MorpionState(
        points=frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}),
        used_unit_segments=frozenset(
            {
                _segment((0, 0), (1, 0)),
                _segment((1, 0), (2, 0)),
                _segment((2, 0), (3, 0)),
                _segment((3, 0), (4, 0)),
            }
        ),
        dir_usage={((0, 0), 0): 1},
        moves=1,
        variant=Variant.TOUCHING_5T,
    )


def _assert_states_equivalent(left: MorpionState, right: MorpionState) -> None:
    """Assert semantic Morpion-state equality."""
    dynamics = MorpionDynamics()

    assert right is not left
    assert right.variant == left.variant
    assert right.moves == left.moves
    assert right.played_moves == left.played_moves
    assert right.points == left.points
    assert right.used_unit_segments == left.used_unit_segments
    assert dict(right.dir_usage) == dict(left.dir_usage)
    assert (
        dynamics.legal_actions(right).get_all()
        == dynamics.legal_actions(left).get_all()
    )
    assert right.tag == left.tag


@pytest.mark.parametrize("variant", [Variant.TOUCHING_5T, Variant.DISJOINT_5D])
def test_checkpoint_codec_round_trips_initial_state(variant: Variant) -> None:
    """Initial states should serialize and deserialize without loss."""
    codec = MorpionStateCheckpointCodec()
    state = initial_state(variant)

    payload = codec.dump_state_ref(state)
    restored = codec.load_state_ref(payload)

    assert payload == {"variant": variant.value, "played_moves": []}
    _assert_states_equivalent(state, restored)


@pytest.mark.parametrize("variant", [Variant.TOUCHING_5T, Variant.DISJOINT_5D])
def test_checkpoint_codec_round_trips_nontrivial_state(variant: Variant) -> None:
    """Replaying checkpoint payloads should restore full Morpion semantics."""
    codec = MorpionStateCheckpointCodec()
    state = _state_after_n_moves(variant, moves_to_play=8)

    payload = codec.dump_state_ref(state)
    restored = codec.load_state_ref(payload)

    assert isinstance(payload, dict)
    assert payload["variant"] == variant.value
    assert sorted(tuple(move) for move in payload["played_moves"]) == sorted(
        state.played_moves
    )
    _assert_states_equivalent(state, restored)


def test_checkpoint_payload_uses_reversible_variant_and_moves_not_tag() -> None:
    """Dumped payloads should carry reversible replay data rather than hashes."""
    codec = MorpionStateCheckpointCodec()
    state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=6)

    payload = codec.dump_state_ref(state)

    assert "variant" in payload
    assert "played_moves" in payload
    assert "tag" not in payload
    assert payload["variant"] == state.variant.value
    assert payload["played_moves"]


def test_checkpoint_dump_rejects_state_without_full_move_history() -> None:
    """States without reconstructable played-move history should fail clearly."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises(ValueError, match="complete played_moves history"):
        codec.dump_state_ref(_legacy_state_without_history())


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"played_moves": []}, "missing 'variant'"),
        ({"variant": "5T"}, "missing 'played_moves'"),
        (
            {"variant": "unknown", "played_moves": []},
            "Unknown Morpion checkpoint variant",
        ),
        (
            {"variant": "5T", "played_moves": [[0, 0, 4]]},
            "four-integer sequence",
        ),
    ],
)
def test_checkpoint_load_rejects_malformed_payload(
    payload: object,
    message: str,
) -> None:
    """Malformed checkpoint payloads should raise clear validation errors."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises(ValueError, match=message):
        codec.load_state_ref(payload)


def test_checkpoint_load_rejects_illegal_move_sequence() -> None:
    """Well-formed but illegal replay data should fail clearly."""
    codec = MorpionStateCheckpointCodec()
    payload = {"variant": "5T", "played_moves": [[10, 10, 14, 10]]}

    with pytest.raises(ValueError, match="Illegal Morpion checkpoint move at index 0"):
        codec.load_state_ref(payload)
