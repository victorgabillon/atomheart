"""Geometry tables for 32-square checkers coordinates."""

from __future__ import annotations

from dataclasses import dataclass

N_ROWS = 8
N_COLS = 8
N_SQUARES = 32

NW = "NW"
NE = "NE"
SW = "SW"
SE = "SE"


@dataclass(frozen=True, slots=True)
class CaptureEdge:
    """Capture edge data from source square."""

    jumped: int
    landing: int


def is_dark_square(row: int, col: int) -> bool:
    """Return whether ``(row, col)`` is a playable dark square."""
    return (row + col) % 2 == 1


SQ32_TO_RC: tuple[tuple[int, int], ...] = tuple(
    (row, col)
    for row in range(N_ROWS)
    for col in range(N_COLS)
    if is_dark_square(row, col)
)

_RC_TO_SQ32: list[list[int]] = [[-1 for _ in range(N_COLS)] for _ in range(N_ROWS)]
for sq, (row, col) in enumerate(SQ32_TO_RC):
    _RC_TO_SQ32[row][col] = sq

ROW_OF_SQ32: tuple[int, ...] = tuple(row for row, _ in SQ32_TO_RC)


def sq32_to_rc(sq: int) -> tuple[int, int]:
    """Convert 0..31 playable-square index to (row, col) on 8x8 board."""
    return SQ32_TO_RC[sq]


def rc_to_sq32(row: int, col: int) -> int | None:
    """Convert board coordinate to playable-square index or None."""
    if not (0 <= row < N_ROWS and 0 <= col < N_COLS):
        return None
    sq = _RC_TO_SQ32[row][col]
    return sq if sq != -1 else None


def _step_from(sq: int, dr: int, dc: int) -> int:
    row, col = sq32_to_rc(sq)
    return _RC_TO_SQ32[row + dr][col + dc] if 0 <= row + dr < N_ROWS and 0 <= col + dc < N_COLS else -1


def _capture_from(sq: int, dr: int, dc: int) -> CaptureEdge:
    row, col = sq32_to_rc(sq)
    jumped_sq = rc_to_sq32(row + dr, col + dc)
    landing_sq = rc_to_sq32(row + 2 * dr, col + 2 * dc)
    if jumped_sq is None or landing_sq is None:
        return CaptureEdge(-1, -1)
    return CaptureEdge(jumped_sq, landing_sq)


STEP_NW: tuple[int, ...] = tuple(_step_from(sq, -1, -1) for sq in range(N_SQUARES))
STEP_NE: tuple[int, ...] = tuple(_step_from(sq, -1, 1) for sq in range(N_SQUARES))
STEP_SW: tuple[int, ...] = tuple(_step_from(sq, 1, -1) for sq in range(N_SQUARES))
STEP_SE: tuple[int, ...] = tuple(_step_from(sq, 1, 1) for sq in range(N_SQUARES))

CAP_NW: tuple[CaptureEdge, ...] = tuple(
    _capture_from(sq, -1, -1) for sq in range(N_SQUARES)
)
CAP_NE: tuple[CaptureEdge, ...] = tuple(
    _capture_from(sq, -1, 1) for sq in range(N_SQUARES)
)
CAP_SW: tuple[CaptureEdge, ...] = tuple(
    _capture_from(sq, 1, -1) for sq in range(N_SQUARES)
)
CAP_SE: tuple[CaptureEdge, ...] = tuple(
    _capture_from(sq, 1, 1) for sq in range(N_SQUARES)
)

WHITE_FORWARD_DIRECTIONS: tuple[str, str] = (SW, SE)
BLACK_FORWARD_DIRECTIONS: tuple[str, str] = (NW, NE)
ALL_DIRECTIONS: tuple[str, str, str, str] = (NW, NE, SW, SE)

STEP_TABLES: dict[str, tuple[int, ...]] = {
    NW: STEP_NW,
    NE: STEP_NE,
    SW: STEP_SW,
    SE: STEP_SE,
}

CAPTURE_TABLES: dict[str, tuple[CaptureEdge, ...]] = {
    NW: CAP_NW,
    NE: CAP_NE,
    SW: CAP_SW,
    SE: CAP_SE,
}
