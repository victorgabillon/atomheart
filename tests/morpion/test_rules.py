"""Rule-focused tests for Morpion 5T/5D behavior."""

import pytest

from atomheart.games.morpion import MorpionDynamics, MorpionState, Variant


def _segment(
    a: tuple[int, int], b: tuple[int, int]
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return normalized segment endpoints."""
    return (a, b) if a <= b else (b, a)


def _state_with_one_horizontal_line(variant: Variant) -> MorpionState:
    """Build a state where one horizontal line from x=0..4 has already been drawn."""
    points = frozenset((x, 0) for x in range(8))
    used_unit_segments = frozenset(_segment((x, 0), (x + 1, 0)) for x in range(4))
    dir_usage = {
        ((0, 0), 0): 1,
        ((1, 0), 0): 2,
        ((2, 0), 0): 2,
        ((3, 0), 0): 2,
        ((4, 0), 0): 1,
    }
    return MorpionState(
        points=points,
        used_unit_segments=used_unit_segments,
        dir_usage=dir_usage,
        moves=1,
        variant=variant,
    )


def test_touching_5t_allows_parallel_endpoint_sharing() -> None:
    """5T should allow same-direction lines to share one endpoint."""
    dynamics = MorpionDynamics()
    state = _state_with_one_horizontal_line(Variant.TOUCHING_5T)

    action = (0, 4, 0, 4)  # line 4..8, missing point is (8,0)
    transition = dynamics.step(state, action)

    assert (8, 0) in transition.next_state.points
    assert transition.next_state.moves == 2


def test_disjoint_5d_forbids_parallel_endpoint_sharing() -> None:
    """5D should reject any same-direction point sharing."""
    dynamics = MorpionDynamics()
    state = _state_with_one_horizontal_line(Variant.DISJOINT_5D)

    action = (0, 4, 0, 4)  # line 4..8 shares point (4,0)

    with pytest.raises(ValueError, match="5T/5D"):
        dynamics.step(state, action)


def test_action_name_roundtrip() -> None:
    """Text action serialization should round-trip to the same key."""
    dynamics = MorpionDynamics()
    state = _state_with_one_horizontal_line(Variant.TOUCHING_5T)
    action = (0, 4, 0, 4)

    as_name = dynamics.action_name(state, action)
    parsed = dynamics.action_from_name(state, as_name)

    assert parsed == action


def test_tag_changes_when_dir_usage_changes() -> None:
    """State tag must include dir_usage because it is rule-relevant state."""
    points = frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)})
    segs = frozenset(
        {
            _segment((0, 0), (1, 0)),
            _segment((1, 0), (2, 0)),
            _segment((2, 0), (3, 0)),
            _segment((3, 0), (4, 0)),
        }
    )

    state_a = MorpionState(
        points=points,
        used_unit_segments=segs,
        dir_usage={((0, 0), 0): 1},
        moves=3,
        variant=Variant.TOUCHING_5T,
    )
    state_b = MorpionState(
        points=points,
        used_unit_segments=segs,
        dir_usage={((4, 0), 0): 1},
        moves=3,
        variant=Variant.TOUCHING_5T,
    )

    assert state_a.tag != state_b.tag
