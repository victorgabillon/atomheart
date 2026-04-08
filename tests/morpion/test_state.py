"""State-shape tests for Morpion initial configurations."""

from atomheart.games.morpion import Variant, initial_state
from atomheart.games.morpion.state import standard_initial_points_a4


def _expected_classic_points() -> frozenset[tuple[int, int]]:
    """Return the canonical 36-point Greek-cross outline."""
    row_to_xs = {
        4: (-2, -1, 0, 1),
        3: (-2, 1),
        2: (-2, 1),
        1: (-5, -4, -3, -2, 1, 2, 3, 4),
        0: (-5, 4),
        -1: (-5, 4),
        -2: (-5, -4, -3, -2, 1, 2, 3, 4),
        -3: (-2, 1),
        -4: (-2, 1),
        -5: (-2, -1, 0, 1),
    }
    return frozenset((x, y) for y, xs in row_to_xs.items() for x in xs)


def test_standard_initial_points_match_classic_greek_cross() -> None:
    """The default A4 setup should be the canonical hollow Greek cross."""
    points = standard_initial_points_a4()

    assert points == _expected_classic_points()
    assert len(points) == 36


def test_initial_state_uses_classic_greek_cross() -> None:
    """The default initial state should expose the same corrected geometry."""
    state = initial_state(variant=Variant.TOUCHING_5T)

    assert state.points == _expected_classic_points()
    assert state.played_moves == frozenset()
    assert state.canonical_tag == ()
    assert state.moves == 0
