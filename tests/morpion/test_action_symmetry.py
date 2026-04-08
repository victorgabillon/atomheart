"""Symmetry-reduced action-space tests for Morpion."""

from atomheart.games.morpion import MorpionDynamics, Variant, initial_state
from atomheart.games.morpion.dynamics import (
    canonical_action_in_state,
    state_rooted_symmetry_stabilizer,
    transform_action_rooted,
)


def test_initial_state_has_28_raw_and_4_unique_actions() -> None:
    """The fixed Morpion start should reduce 28 raw actions to 4 representatives."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)

    raw_actions = dynamics.all_legal_actions(state)
    unique_actions = dynamics.legal_actions(state).get_all()

    assert len(raw_actions) == 28
    assert len(unique_actions) == 4


def test_initial_raw_actions_map_to_exactly_four_representatives() -> None:
    """Every raw initial action should canonicalize to one of the 4 representatives."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)

    raw_actions = dynamics.all_legal_actions(state)
    unique_actions = set(dynamics.legal_actions(state).get_all())
    representatives = {
        canonical_action_in_state(state, action) for action in raw_actions
    }

    assert representatives == unique_actions
    assert len(representatives) == 4


def test_initial_state_stabilizer_has_all_rooted_symmetries() -> None:
    """The fixed Greek cross should preserve the full rooted D4 group at move 0."""
    state = initial_state(variant=Variant.TOUCHING_5T)

    assert state_rooted_symmetry_stabilizer(state) == tuple(range(8))


def test_stabilizer_shrinks_after_an_asymmetric_move() -> None:
    """A generic non-diagonal opening move should break the initial symmetries."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)

    transition = dynamics.step(state, (0, -6, -2, 0))

    assert len(state_rooted_symmetry_stabilizer(transition.next_state)) < 8


def test_transform_action_rooted_normalizes_all_direction_families() -> None:
    """Rooted action transforms should stay in the canonical action representation."""
    assert transform_action_rooted((0, -6, -2, 0), 1) == (1, 1, -6, 0)
    assert transform_action_rooted((1, -5, -3, 0), 1) == (0, -2, -5, 4)
    assert transform_action_rooted((2, -5, 0, 2), 1) == (3, -5, -1, 2)
    assert transform_action_rooted((3, -5, -1, 2), 1) == (2, 0, -5, 2)


def test_legal_action_orbits_partition_initial_raw_actions() -> None:
    """Initial Morpion legal-action orbits should cover all 28 raw actions in 4 groups."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)

    raw_actions = dynamics.all_legal_actions(state)
    orbits = dynamics.legal_action_orbits(state)

    assert len(orbits) == 4
    assert sum(len(orbit) for orbit in orbits) == len(raw_actions) == 28
    assert sorted(action for orbit in orbits for action in orbit) == list(raw_actions)


def test_step_accepts_unique_representatives_and_records_played_moves() -> None:
    """The reduced legal-action API should still feed valid concrete steps."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)

    for action in dynamics.legal_actions(state).get_all():
        transition = dynamics.step(state, action)
        assert transition.next_state.moves == 1
        assert len(transition.next_state.played_moves) == 1


def test_symmetric_successor_states_share_the_same_canonical_tag() -> None:
    """Raw actions in the same initial orbit should lead to canonically equal successors."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)

    action_a = (0, -6, -2, 0)
    action_b = (1, 1, -6, 0)
    next_state_a = dynamics.step(state, action_a).next_state
    next_state_b = dynamics.step(state, action_b).next_state

    assert canonical_action_in_state(state, action_a) == canonical_action_in_state(
        state, action_b
    )
    assert next_state_a.canonical_tag == next_state_b.canonical_tag
