"""Bitboard helpers for 32-square checkers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .state import CheckersState

MASK32 = (1 << 32) - 1


def bit(sq: int) -> int:
    """Return a single-bit mask for square index ``sq``."""
    return 1 << sq


def iter_bits(bb: int) -> Iterator[int]:
    """Yield set bit indices from least-significant to most-significant."""
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def popcount(bb: int) -> int:
    """Return number of set bits in the bitboard."""
    return bb.bit_count()


def white(state: CheckersState) -> int:
    """Return all white-occupied squares."""
    return state.wm | state.wk


def black(state: CheckersState) -> int:
    """Return all black-occupied squares."""
    return state.bm | state.bk


def occupied(state: CheckersState) -> int:
    """Return all occupied squares."""
    return white(state) | black(state)


def empty(state: CheckersState) -> int:
    """Return all empty playable squares."""
    return (~occupied(state)) & MASK32
