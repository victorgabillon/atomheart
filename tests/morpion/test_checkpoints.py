"""Checkpoint codec tests for Morpion states."""

from __future__ import annotations

import pytest

from atomheart.games.morpion import (
    MorpionCheckpointStateSummary,
    MorpionDynamics,
    MorpionState,
    MorpionStateCheckpointCodec,
    Variant,
    action_to_played_move,
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
def test_checkpoint_codec_anchor_round_trips_initial_state(variant: Variant) -> None:
    """Initial states should anchor round-trip without loss."""
    codec = MorpionStateCheckpointCodec()
    state = initial_state(variant)

    payload = codec.dump_anchor_ref(state)
    restored = codec.load_anchor_ref(payload)

    assert payload == {"variant": variant.value, "played_moves": []}
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

    assert isinstance(payload, dict)
    assert payload["variant"] == variant.value
    assert sorted(tuple(move) for move in payload["played_moves"]) == sorted(
        state.played_moves
    )
    _assert_states_equivalent(state, restored)


def test_checkpoint_anchor_payload_uses_reversible_variant_and_moves_not_tag() -> None:
    """Anchors should carry replay data rather than non-reversible hashes."""
    codec = MorpionStateCheckpointCodec()
    state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=6)

    payload = codec.dump_anchor_ref(state)

    assert "variant" in payload
    assert "played_moves" in payload
    assert "tag" not in payload
    assert payload["variant"] == state.variant.value
    assert payload["played_moves"]


def test_checkpoint_dump_anchor_rejects_state_without_full_move_history() -> None:
    """Anchor dumps should fail clearly without reconstructable move history."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises(ValueError, match="complete played_moves history"):
        codec.dump_anchor_ref(_legacy_state_without_history())


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
def test_checkpoint_load_anchor_rejects_malformed_payload(
    payload: object,
    message: str,
) -> None:
    """Malformed anchor payloads should raise clear validation errors."""
    codec = MorpionStateCheckpointCodec()

    with pytest.raises(ValueError, match=message):
        codec.load_anchor_ref(payload)


def test_checkpoint_load_anchor_rejects_illegal_move_sequence() -> None:
    """Well-formed but illegal anchor replay data should fail clearly."""
    codec = MorpionStateCheckpointCodec()
    payload = {"variant": "5T", "played_moves": [[10, 10, 14, 10]]}

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

    assert delta_payload == {"move": list(action_to_played_move(action))}
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

    assert set(delta_payload) == {"move"}
    assert delta_payload["move"] == list(action_to_played_move(action))
    assert "variant" not in delta_payload
    assert "played_moves" not in delta_payload


def test_checkpoint_summary_contains_tag_and_terminal_flag() -> None:
    """Checkpoint summaries should expose stable Morpion metadata."""
    codec = MorpionStateCheckpointCodec()
    dynamics = MorpionDynamics()
    state = _state_after_n_moves(Variant.TOUCHING_5T, moves_to_play=6)

    summary = codec.dump_state_summary(state)

    assert isinstance(summary, MorpionCheckpointStateSummary)
    assert summary.tag == state.tag
    assert summary.is_terminal is dynamics.is_terminal_state(state)


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

    assert summary == MorpionCheckpointStateSummary(tag=state.tag, is_terminal=True)


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
