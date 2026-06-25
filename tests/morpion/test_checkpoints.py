"""Checkpoint codec tests for Morpion states."""

from __future__ import annotations

import pytest

from atomheart.games.morpion import (
    MorpionDynamics,
    MorpionState,
    MorpionStateCheckpointCodec,
    Variant,
    action_to_played_move,
    initial_state,
)
from atomheart.games.morpion.checkpoints import _decode_move_code, _encode_move_code


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


@pytest.mark.parametrize(
    "move",
    [
        (-5, 1, -1, 1),
        (-2, -5, -2, -1),
        (0, 0, 4, 0),
        (1, -4, 5, -4),
    ],
)
def test_checkpoint_move_code_round_trips_representative_moves(
    move: tuple[int, int, int, int],
) -> None:
    """Move codes should reversibly encode signed canonical Morpion moves."""
    code = _encode_move_code(move)

    assert isinstance(code, int)
    assert _decode_move_code(code) == move


@pytest.mark.parametrize("variant", [Variant.TOUCHING_5T, Variant.DISJOINT_5D])
def test_checkpoint_codec_anchor_round_trips_initial_state(variant: Variant) -> None:
    """Initial states should anchor round-trip without loss."""
    codec = MorpionStateCheckpointCodec()
    state = initial_state(variant)

    payload = codec.dump_anchor_ref(state)
    restored = codec.load_anchor_ref(payload)

    assert payload == (
        0 if variant == Variant.TOUCHING_5T else 1,
        (),
    )
    _assert_states_equivalent(state, restored)
    assert codec.dump_state_ref(state) == payload
    _assert_states_equivalent(state, codec.load_state_ref(payload))


@pytest.mark.parametrize("variant", [Variant.TOUCHING_5T, Variant.DISJOINT_5D])
def test_checkpoint_codec_anchor_round_trips_nontrivial_state(variant: Variant) -> None:
    """Anchor replay should restore full Morpion semantics."""
    codec = MorpionStateCheckpointCodec()
    state = _state_after_n_moves(variant, moves_to_play=8)

    payload = codec.dump_anchor_ref(state)
    restored = codec.load_anchor_ref(payload)

    assert isinstance(payload, tuple)
    assert payload[0] == (0 if variant == Variant.TOUCHING_5T else 1)
    assert all(isinstance(move_code, int) for move_code in payload[1])
    assert sorted(_decode_move_code(move_code) for move_code in payload[1]) == sorted(
        state.played_moves
    )
    _assert_states_equivalent(state, restored)


def test_checkpoint_anchor_payload_uses_reversible_variant_and_moves_not_tag() -> None:
    """Anchors should carry replay data rather than non-reversible hashes."""
    codec = MorpionStateCheckpointCodec()
    state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=6)

    payload = codec.dump_anchor_ref(state)

    assert isinstance(payload, tuple)
    assert payload[0] == (0 if state.variant == Variant.TOUCHING_5T else 1)
    assert payload[1]


def test_checkpoint_dump_anchor_rejects_state_without_full_move_history() -> None:
    """Anchor dumps should fail clearly without reconstructable move history."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises(ValueError, match="complete played_moves history"):
        codec.dump_anchor_ref(_legacy_state_without_history())


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"played_moves": []}, "two-item sequence"),
        ([0], "two-item sequence"),
        ([99, []], "variant code"),
        ([0, [[0, 0, 4, 0]]], "integer move code"),
    ],
)
def test_checkpoint_load_anchor_rejects_malformed_payload(
    payload: object,
    message: str,
) -> None:
    """Malformed anchor payloads should raise clear validation errors."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises((TypeError, ValueError), match=message):
        codec.load_anchor_ref(payload)


def test_checkpoint_load_anchor_rejects_illegal_move_sequence() -> None:
    """Well-formed but illegal anchor replay data should fail clearly."""
    codec = MorpionStateCheckpointCodec()
    payload = [0, [_encode_move_code((10, 10, 14, 10))]]

    with pytest.raises(ValueError, match="Illegal Morpion checkpoint move at index 0"):
        codec.load_anchor_ref(payload)


@pytest.mark.parametrize("variant", [Variant.TOUCHING_5T, Variant.DISJOINT_5D])
def test_checkpoint_delta_round_trip_uses_parent_and_one_move(variant: Variant) -> None:
    """One child delta should reconstruct the same concrete child from its parent."""
    codec = MorpionStateCheckpointCodec()
    dynamics = MorpionDynamics()
    parent_state = _state_after_n_moves(variant, moves_to_play=4)
    action = dynamics.legal_actions(parent_state).get_all()[0]
    child_state = dynamics.step(parent_state, action).next_state

    delta_payload = codec.dump_delta_from_parent(
        parent_state=parent_state,
        child_state=child_state,
        branch_from_parent=action,
    )
    restored_child = codec.load_child_from_delta(
        parent_state=parent_state,
        delta_ref=delta_payload,
        branch_from_parent=action,
    )

    assert isinstance(delta_payload, int)
    assert _decode_move_code(delta_payload) == action_to_played_move(action)
    _assert_states_equivalent(child_state, restored_child)


def test_checkpoint_delta_payload_is_move_based_not_whole_state() -> None:
    """Deltas should encode exactly one move instead of duplicating anchor state."""
    codec = MorpionStateCheckpointCodec()
    dynamics = MorpionDynamics()
    parent_state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=5)
    action = dynamics.legal_actions(parent_state).get_all()[0]
    child_state = dynamics.step(parent_state, action).next_state

    delta_payload = codec.dump_delta_from_parent(
        parent_state=parent_state,
        child_state=child_state,
    )

    assert isinstance(delta_payload, int)
    assert _decode_move_code(delta_payload) == action_to_played_move(action)


def test_checkpoint_summary_contains_tag_and_terminal_flag() -> None:
    """Checkpoint summaries should expose stable Morpion metadata."""
    codec = MorpionStateCheckpointCodec()
    dynamics = MorpionDynamics()
    state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=6)

    summary = codec.dump_state_summary(state)

    assert summary == (state.tag, dynamics.is_terminal_state(state))


def test_checkpoint_summary_marks_terminal_state() -> None:
    """Terminal summaries should preserve the exact terminal flag."""
    codec = MorpionStateCheckpointCodec()
    dynamics = MorpionDynamics()
    state = initial_state(Variant.TOUCHING_5T)

    while True:
        actions = dynamics.legal_actions(state).get_all()
        if not actions:
            break
        state = dynamics.step(state, actions[0]).next_state

    summary = codec.dump_state_summary(state)

    assert summary == (state.tag, True)


def test_checkpoint_load_anchor_accepts_json_list_compact_form() -> None:
    """Anchor loader should accept compact payloads after JSON tuple-to-list decode."""
    codec = MorpionStateCheckpointCodec()
    state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=3)
    payload = codec.dump_anchor_ref(state)

    restored = codec.load_anchor_ref([payload[0], list(payload[1])])

    _assert_states_equivalent(state, restored)


def test_checkpoint_load_delta_accepts_compact_integer_form() -> None:
    """Delta loader should accept compact integer move-code payloads."""
    codec = MorpionStateCheckpointCodec()
    dynamics = MorpionDynamics()
    parent_state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=4)
    action = dynamics.legal_actions(parent_state).get_all()[0]
    child_state = dynamics.step(parent_state, action).next_state
    payload = codec.dump_delta_from_parent(
        parent_state=parent_state,
        child_state=child_state,
        branch_from_parent=action,
    )

    restored = codec.load_child_from_delta(
        parent_state=parent_state,
        delta_ref=payload,
        branch_from_parent=action,
    )

    _assert_states_equivalent(child_state, restored)


@pytest.mark.parametrize(
    ("anchor_payload", "anchor_message"),
    [
        ([0], "two-item sequence"),
        ([99, []], "variant code"),
        ((1, [[0, 0, 4, 0]]), "integer move code"),
    ],
)
def test_checkpoint_load_anchor_rejects_invalid_compact_shapes(
    anchor_payload: object,
    anchor_message: str,
) -> None:
    """Compact anchor payload shape errors should stay clear and specific."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises((TypeError, ValueError), match=anchor_message):
        codec.load_anchor_ref(anchor_payload)


def test_checkpoint_load_delta_rejects_invalid_move_code_shape() -> None:
    """Compact delta payload shape errors should stay clear and specific."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises((TypeError, ValueError), match="integer move code"):
        codec.load_child_from_delta(
            parent_state=_state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=1),
            delta_ref=[0, 0, 4, 0],
        )


def test_checkpoint_load_delta_rejects_invalid_move_code_value() -> None:
    """Invalid move-code integers should fail before replay."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises(ValueError, match="Invalid Morpion checkpoint move code"):
        codec.load_child_from_delta(
            parent_state=_state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=1),
            delta_ref=-1,
        )


def test_checkpoint_anchor_plus_delta_chain_matches_direct_reconstruction() -> None:
    """One anchor followed by a short delta chain should rebuild the same state."""
    codec = MorpionStateCheckpointCodec()
    dynamics = MorpionDynamics()
    root_state = initial_state(Variant.TOUCHING_5T)
    root_anchor = codec.dump_anchor_ref(root_state)

    direct_state = root_state
    delta_payloads: list[object] = []
    branch_history: list[object] = []
    for _ in range(4):
        action = dynamics.legal_actions(direct_state).get_all()[0]
        child_state = dynamics.step(direct_state, action).next_state
        delta_payloads.append(
            codec.dump_delta_from_parent(
                parent_state=direct_state,
                child_state=child_state,
                branch_from_parent=action,
            )
        )
        branch_history.append(action)
        direct_state = child_state

    restored_state = codec.load_anchor_ref(root_anchor)
    for branch, delta_payload in zip(branch_history, delta_payloads, strict=True):
        restored_state = codec.load_child_from_delta(
            parent_state=restored_state,
            delta_ref=delta_payload,
            branch_from_parent=branch,
        )

    _assert_states_equivalent(direct_state, restored_state)


def test_checkpoint_codec_profile_snapshot_counts_public_dumps() -> None:
    """Optional codec profiling should count public checkpoint dump methods."""
    codec = MorpionStateCheckpointCodec(profile_checkpoint=True)
    dynamics = MorpionDynamics()
    parent_state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=4)
    action = dynamics.legal_actions(parent_state).get_all()[0]
    child_state = dynamics.step(parent_state, action).next_state

    codec.dump_anchor_ref(parent_state)
    codec.dump_delta_from_parent(
        parent_state=parent_state,
        child_state=child_state,
        branch_from_parent=action,
    )
    codec.dump_state_summary(child_state)
    snapshot = codec.checkpoint_profile_snapshot()

    assert snapshot["morpion_anchor_calls"] == 1
    assert snapshot["morpion_delta_calls"] == 1
    assert snapshot["morpion_summary_calls"] == 1
    assert snapshot["morpion_anchor_total_s"] >= 0.0
    assert snapshot["morpion_delta_total_s"] >= 0.0
    assert snapshot["morpion_summary_total_s"] >= 0.0


def test_checkpoint_codec_profile_reset_clears_counts() -> None:
    """Optional codec profiling should reset between checkpoint builds."""
    codec = MorpionStateCheckpointCodec(profile_checkpoint=True)
    codec.dump_anchor_ref(initial_state(Variant.TOUCHING_5T))

    codec.reset_checkpoint_profile()
    snapshot = codec.checkpoint_profile_snapshot()

    assert snapshot["morpion_anchor_calls"] == 0
    assert snapshot["morpion_delta_calls"] == 0
    assert snapshot["morpion_summary_calls"] == 0


def test_checkpoint_codec_profile_defaults_to_zero_when_disabled() -> None:
    """Snapshot access should stay safe even when profiling is disabled."""
    snapshot = MorpionStateCheckpointCodec().checkpoint_profile_snapshot()

    assert snapshot["morpion_anchor_calls"] == 0
    assert snapshot["morpion_delta_calls"] == 0
    assert snapshot["morpion_summary_calls"] == 0
