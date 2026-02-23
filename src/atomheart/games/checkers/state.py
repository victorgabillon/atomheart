"""State objects for the checkers game implementation."""

from __future__ import annotations

from dataclasses import dataclass

import valanga


@dataclass(frozen=True, slots=True)
class CheckersState(valanga.TurnState):
    """Turn state for 32-square bitboard checkers."""

    wm: int
    wk: int
    bm: int
    bk: int
    turn: valanga.Color
    ply_since_capture_or_man_move: int = 0

    @property
    def tag(self) -> valanga.StateTag:
        """Return a hashable tag reflecting all rule-relevant fields."""
        return (
            self.wm,
            self.wk,
            self.bm,
            self.bk,
            self.turn,
            self.ply_since_capture_or_man_move,
        )

    def is_game_over(self) -> bool:
        """Return whether either side has no remaining pieces."""
        white_pieces = self.wm | self.wk
        black_pieces = self.bm | self.bk
        return white_pieces == 0 or black_pieces == 0

    def pprint(self) -> str:
        """Return a concise debug representation of the state."""
        return (
            "CheckersState("
            f"turn={self.turn}, "
            f"wm=0x{self.wm:08x}, wk=0x{self.wk:08x}, "
            f"bm=0x{self.bm:08x}, bk=0x{self.bk:08x}, "
            f"ply={self.ply_since_capture_or_man_move}"
            ")"
        )


def initial_state() -> CheckersState:
    """Return the canonical 8x8 checkers opening state on 32 dark squares.

    Square indexing uses the 32 playable dark squares as ``0..31`` in row-major
    order from top to bottom. This layout places white men on bits ``0..11`` and
    black men on bits ``20..31``.
    """
    return CheckersState(
        wm=0x00000FFF,
        wk=0,
        bm=0xFFF00000,
        bk=0,
        turn=valanga.Color.WHITE,
        ply_since_capture_or_man_move=0,
    )
