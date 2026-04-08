"""State objects for Morpion Solitaire (5T / 5D)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, cast

import valanga

from .canonical import Move, canonical_move_set_hash, canonical_move_set_tag

if TYPE_CHECKING:
    from collections.abc import Mapping

Point = tuple[int, int]
Dir = tuple[int, int]
Segment = tuple[Point, Point]


def _empty_played_moves() -> frozenset[Move]:
    """Return an explicitly typed empty move set."""
    return cast("frozenset[Move]", frozenset())


class Variant(StrEnum):
    """Morpion Solitaire ruleset variant."""

    TOUCHING_5T = "5T"
    DISJOINT_5D = "5D"


class NonAxisAlignedSegmentError(ValueError):
    """Raised when a segment is not horizontal or vertical."""

    def __init__(self) -> None:
        """Initialize the error with the canonical Morpion constraint message."""
        super().__init__("Classic Morpion start only uses axis-aligned segments.")


def norm_seg(a: Point, b: Point) -> Segment:
    """Return a normalized unit segment with deterministic endpoint ordering."""
    return (a, b) if a <= b else (b, a)


def _points_on_axis_aligned_segment(start: Point, end: Point) -> set[Point]:
    """Enumerate all lattice points on one horizontal or vertical segment."""
    x0, y0 = start
    x1, y1 = end
    if x0 == x1:
        return {(x0, y) for y in range(min(y0, y1), max(y0, y1) + 1)}
    if y0 == y1:
        return {(x, y0) for x in range(min(x0, x1), max(x0, x1) + 1)}
    raise NonAxisAlignedSegmentError


def standard_initial_points_classic() -> frozenset[Point]:
    """Return the canonical 36-point Greek-cross start position."""
    outline_segments: tuple[Segment, ...] = (
        ((-2, 4), (1, 4)),
        ((1, 4), (1, 1)),
        ((1, 1), (4, 1)),
        ((4, 1), (4, -2)),
        ((4, -2), (1, -2)),
        ((1, -2), (1, -5)),
        ((1, -5), (-2, -5)),
        ((-2, -5), (-2, -2)),
        ((-2, -2), (-5, -2)),
        ((-5, -2), (-5, 1)),
        ((-5, 1), (-2, 1)),
        ((-2, 1), (-2, 4)),
    )
    points: set[Point] = set()
    for segment in outline_segments:
        points.update(_points_on_axis_aligned_segment(*segment))
    return frozenset(points)


def standard_initial_points_a4() -> frozenset[Point]:
    """Return the standard 36-point ``A4`` Greek-cross start position."""
    return standard_initial_points_classic()


@dataclass(frozen=True, slots=True)
class MorpionState(valanga.State):
    """Immutable Morpion state."""

    points: frozenset[Point]
    used_unit_segments: frozenset[Segment]
    dir_usage: Mapping[tuple[Point, int], int]
    played_moves: frozenset[Move] = field(default_factory=_empty_played_moves)
    moves: int = 0
    variant: Variant = Variant.TOUCHING_5T

    @property
    def tag(self) -> int:
        """Return a stable raw hash tag for state caching.

        When ``played_moves`` is complete, it becomes the structural state
        identity. Legacy handcrafted states that omit ``played_moves`` keep the
        older geometry-based tag as a compatibility fallback.
        """
        if len(self.played_moves) == self.moves:
            return hash((self.variant, tuple(sorted(self.played_moves))))
        return self._legacy_geometry_tag

    @property
    def canonical_tag(self) -> tuple[Move, ...]:
        """Return the rooted D4-invariant move-set tag for the fixed start."""
        return canonical_move_set_tag(self.played_moves)

    @property
    def canonical_hash(self) -> int:
        """Return the hash of :attr:`canonical_tag`."""
        return canonical_move_set_hash(self.played_moves)

    @property
    def _legacy_geometry_tag(self) -> int:
        """Return the pre-refactor geometry-based state hash."""
        return hash(
            (
                self.variant,
                self.moves,
                tuple(sorted(self.points)),
                tuple(sorted(self.used_unit_segments)),
                tuple(sorted(self.dir_usage.items())),
            )
        )

    def is_game_over(self) -> bool:
        """Return a conservative game-over flag.

        Dynamics computes terminal state exactly by checking legal actions.
        """
        return False

    def pprint(self) -> str:
        """Pretty-print the occupied-point grid."""
        if not self.points:
            return "<empty>"

        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)

        lines: list[str] = []
        for y in range(maxy, miny - 1, -1):
            row = ["X" if (x, y) in self.points else "." for x in range(minx, maxx + 1)]
            lines.append("".join(row))
        return "\n".join(lines)


def initial_state(variant: Variant = Variant.TOUCHING_5T) -> MorpionState:
    """Build the default Morpion initial state."""
    return MorpionState(
        points=standard_initial_points_a4(),
        used_unit_segments=frozenset(),
        dir_usage={},
        played_moves=_empty_played_moves(),
        moves=0,
        variant=variant,
    )
