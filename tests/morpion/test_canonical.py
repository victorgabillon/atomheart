"""Symmetry-aware move-set tests for Morpion."""

from atomheart.games.morpion import (
    MorpionDynamics,
    Variant,
    action_to_played_move,
    apply_rooted_symmetry,
    canonical_move_set_tag,
    canonical_move_set_tag_d4_translation,
    initial_state,
)
from atomheart.games.morpion.state import standard_initial_points_a4


def test_canonical_move_set_tag_empty_state() -> None:
    """An empty move-set should have the empty canonical tag."""
    assert canonical_move_set_tag(()) == ()


def test_canonical_move_set_tag_translation_invariance() -> None:
    """Translated move-sets should share the same free-shape canonical tag."""
    moves1 = {(0, 0, 4, 0), (4, 0, 4, 4)}
    moves2 = {(10, 10, 14, 10), (14, 10, 14, 14)}

    assert canonical_move_set_tag_d4_translation(moves1) == (
        canonical_move_set_tag_d4_translation(moves2)
    )


def test_rooted_canonical_tag_keeps_translation_distinct() -> None:
    """Translated move-sets should stay distinct for the fixed-start game."""
    moves1 = {(0, 0, 4, 0), (4, 0, 4, 4)}
    moves2 = {(10, 10, 14, 10), (14, 10, 14, 14)}

    assert canonical_move_set_tag(moves1) != canonical_move_set_tag(moves2)


def test_rooted_symmetries_preserve_initial_cross() -> None:
    """Rooted symmetries should preserve the fixed initial Morpion cross."""
    points = standard_initial_points_a4()

    for sym in range(8):
        transformed = {apply_rooted_symmetry(p, sym) for p in points}
        assert transformed == set(points)


def test_canonical_move_set_tag_rotation_invariance() -> None:
    """Rotated move-sets should share the same canonical tag."""
    moves1 = {(0, 0, 4, 0), (4, 0, 4, 4)}
    rotated = {
        apply_rooted_symmetry((x1, y1), 1) + apply_rooted_symmetry((x2, y2), 1)
        for (x1, y1, x2, y2) in moves1
    }

    assert canonical_move_set_tag(moves1) == canonical_move_set_tag(rotated)


def test_canonical_move_set_tag_reflection_invariance() -> None:
    """Reflected move-sets should share the same canonical tag."""
    moves1 = {(0, 0, 4, 0), (4, 0, 4, 4)}
    reflected = {
        apply_rooted_symmetry((x1, y1), 4) + apply_rooted_symmetry((x2, y2), 4)
        for (x1, y1, x2, y2) in moves1
    }

    assert canonical_move_set_tag(moves1) == canonical_move_set_tag(reflected)


def test_action_to_played_move_returns_line_endpoints() -> None:
    """Action conversion should keep only the normalized line endpoints."""
    assert action_to_played_move((0, 3, 2, 1)) == (3, 2, 7, 2)
    assert action_to_played_move((1, 3, 2, 1)) == (3, 2, 3, 6)
    assert action_to_played_move((2, 3, 2, 1)) == (3, 2, 7, 6)
    assert action_to_played_move((3, 3, 2, 1)) == (3, 2, 7, -2)


def test_step_updates_played_moves() -> None:
    """Applying one legal move should record its played-line identity."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)
    action = dynamics.legal_actions(state).get_all()[0]

    transition = dynamics.step(state, action)
    played_move = action_to_played_move(action)

    assert len(transition.next_state.played_moves) == len(state.played_moves) + 1
    assert played_move in transition.next_state.played_moves
    assert transition.next_state.canonical_tag == canonical_move_set_tag(
        transition.next_state.played_moves
    )
