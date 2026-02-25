"""State objects for Morpion Solitaire (5T / 5D)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

import valanga

Point = tuple[int, int]
Dir = tuple[int, int]
Segment = tuple[Point, Point]


class Variant(str, Enum):
    """Morpion Solitaire ruleset variant."""

    TOUCHING_5T = "5T"
    DISJOINT_5D = "5D"


def _norm_seg(a: Point, b: Point) -> Segment:
    """Return a normalized unit segment with deterministic endpoint ordering."""
    return (a, b) if a <= b else (b, a)


def standard_initial_points_A4() -> frozenset[Point]:
    """Return the standard 36-point ``A4`` cross start position."""
    pts: set[Point] = set()
    for y in (-1, 0):
        for x in range(-5, 5):
            pts.add((x, y))
    for x in (-1, 0):
        for y in range(-5, 5):
            pts.add((x, y))
    return frozenset(pts)


@dataclass(frozen=True, slots=True)
class MorpionState(valanga.State):
    """Immutable Morpion state."""

    points: frozenset[Point]
    used_unit_segments: frozenset[Segment]
    dir_usage: Mapping[tuple[Point, int], int]
    moves: int = 0
    variant: Variant = Variant.TOUCHING_5T

    @property
    def tag(self) -> int:
        """Return a stable hash tag suitable for state caching."""
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
            row = []
            for x in range(minx, maxx + 1):
                row.append("X" if (x, y) in self.points else ".")
            lines.append("".join(row))
        return "\n".join(lines)


def initial_state(variant: Variant = Variant.TOUCHING_5T) -> MorpionState:
    """Build the default Morpion initial state."""
    return MorpionState(
        points=standard_initial_points_A4(),
        used_unit_segments=frozenset(),
        dir_usage={},
        moves=0,
        variant=variant,
    )
