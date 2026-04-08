"""Canonical move-set utilities for Morpion Solitaire."""

from __future__ import annotations

from collections.abc import Callable, Iterable

Point = tuple[int, int]
Move = tuple[int, int, int, int]


def _norm_move_endpoints(p1: Point, p2: Point) -> Move:
    """Return one move with endpoints ordered lexicographically."""
    if p1 <= p2:
        return (p1[0], p1[1], p2[0], p2[1])
    return (p2[0], p2[1], p1[0], p1[1])


def _apply_origin_symmetry(p: Point, sym: int) -> Point:
    """Apply one of the eight D4 square symmetries around the origin."""
    x, y = p
    if sym == 0:
        return (x, y)
    if sym == 1:
        return (-y, x)
    if sym == 2:
        return (-x, -y)
    if sym == 3:
        return (y, -x)
    if sym == 4:
        return (x, -y)
    if sym == 5:
        return (-x, y)
    if sym == 6:
        return (y, x)
    if sym == 7:
        return (-y, -x)
    raise ValueError(f"Invalid symmetry index: {sym}")


def _apply_rooted_symmetry(p: Point, sym: int) -> Point:
    """Apply one rooted D4 symmetry around the fixed Morpion start center."""
    x, y = p
    if sym == 0:
        return (x, y)
    if sym == 1:
        return (-y - 1, x)
    if sym == 2:
        return (-x - 1, -y - 1)
    if sym == 3:
        return (y, -x - 1)
    if sym == 4:
        return (x, -y - 1)
    if sym == 5:
        return (-x - 1, y)
    if sym == 6:
        return (y, x)
    if sym == 7:
        return (-y - 1, -x - 1)
    raise ValueError(f"Invalid symmetry index: {sym}")


def _transform_move(
    move: Move,
    sym: int,
    point_transform: Callable[[Point, int], Point],
) -> Move:
    """Apply one symmetry to both endpoints of one move."""
    x1, y1, x2, y2 = move
    p1 = point_transform((x1, y1), sym)
    p2 = point_transform((x2, y2), sym)
    return _norm_move_endpoints(p1, p2)


def _translate_move(move: Move, dx: int, dy: int) -> Move:
    """Translate one move so ``(dx, dy)`` becomes the origin."""
    x1, y1, x2, y2 = move
    p1 = (x1 - dx, y1 - dy)
    p2 = (x2 - dx, y2 - dy)
    return _norm_move_endpoints(p1, p2)


def canonical_move_set_tag_d4(played_moves: Iterable[Move]) -> tuple[Move, ...]:
    """Return a D4-invariant canonical move-set tag for the fixed start."""
    base_moves = tuple(
        _norm_move_endpoints((x1, y1), (x2, y2))
        for (x1, y1, x2, y2) in played_moves
    )

    if not base_moves:
        return ()

    candidates: list[tuple[Move, ...]] = []

    for sym in range(8):
        transformed = tuple(
            _transform_move(move, sym, _apply_rooted_symmetry) for move in base_moves
        )
        candidates.append(tuple(sorted(transformed)))

    return min(candidates)


def canonical_move_set_tag_d4_translation(
    played_moves: Iterable[Move],
) -> tuple[Move, ...]:
    """Return a D4- and translation-invariant free-shape canonical tag."""
    base_moves = tuple(
        _norm_move_endpoints((x1, y1), (x2, y2))
        for (x1, y1, x2, y2) in played_moves
    )

    if not base_moves:
        return ()

    candidates: list[tuple[Move, ...]] = []

    for sym in range(8):
        transformed = tuple(
            _transform_move(move, sym, _apply_origin_symmetry) for move in base_moves
        )

        endpoints: list[Point] = []
        for x1, y1, x2, y2 in transformed:
            endpoints.append((x1, y1))
            endpoints.append((x2, y2))

        ax, ay = min(endpoints)
        normalized = tuple(
            sorted(_translate_move(move, ax, ay) for move in transformed)
        )
        candidates.append(normalized)

    return min(candidates)


def canonical_move_set_tag(played_moves: Iterable[Move]) -> tuple[Move, ...]:
    """Return the default rooted canonical tag for fixed-start Morpion."""
    return canonical_move_set_tag_d4(played_moves)


def canonical_move_set_hash(played_moves: Iterable[Move]) -> int:
    """Return the hash of the default canonical move-set tag."""
    return hash(canonical_move_set_tag(played_moves))


__all__ = [
    "Move",
    "Point",
    "_apply_rooted_symmetry",
    "canonical_move_set_hash",
    "canonical_move_set_tag",
    "canonical_move_set_tag_d4",
    "canonical_move_set_tag_d4_translation",
]
