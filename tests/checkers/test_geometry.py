"""Geometry and table tests for checkers."""

from atomheart.games.checkers.geometry import (
    CAP_SE,
    ROW_OF_SQ32,
    STEP_SE,
    STEP_SW,
    is_dark_square,
    rc_to_sq32,
    sq32_to_rc,
)


def test_sq32_roundtrip() -> None:
    """All playable squares should roundtrip between sq32 and (row, col)."""
    for sq in range(32):
        row, col = sq32_to_rc(sq)
        assert is_dark_square(row, col)
        assert rc_to_sq32(row, col) == sq


def test_top_row_has_white_forward_steps() -> None:
    """Playable top-row squares should have at least one white-forward step."""
    top_row_squares = [sq for sq in range(32) if ROW_OF_SQ32[sq] == 0]
    for sq in top_row_squares:
        assert STEP_SE[sq] != -1 or STEP_SW[sq] != -1


def test_capture_se_table_shape() -> None:
    """SE captures should move one jumped row and two landing rows down."""
    for sq, edge in enumerate(CAP_SE):
        if edge.jumped == -1:
            continue
        row, _ = sq32_to_rc(sq)
        jumped_row, _ = sq32_to_rc(edge.jumped)
        landing_row, _ = sq32_to_rc(edge.landing)
        assert jumped_row == row + 1
        assert landing_row == row + 2
