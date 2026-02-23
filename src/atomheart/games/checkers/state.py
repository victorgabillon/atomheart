"""State objects for the checkers game implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import valanga


_TEXT_RE = re.compile(
    r"^\s*([WB])\s*;\s*ply\s*=\s*(\d+)\s*;\s*W\s*=\s*([^;]*)\s*;\s*B\s*=\s*([^;]*)\s*$",
    re.IGNORECASE,
)


def _iter_set_bit_indices(bb: int) -> Iterable[int]:
    """Yield set bit indices in ascending order."""
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def _format_piece_list(men_bb: int, kings_bb: int) -> str:
    """Format men and kings as a stable piece list like ``1,2,K3``."""
    parts: list[str] = []
    all_pieces = men_bb | kings_bb
    for index in _iter_set_bit_indices(all_pieces):
        square = index + 1
        parts.append(f"K{square}" if (kings_bb >> index) & 1 else str(square))
    return ",".join(parts)


def _parse_piece_list(text: str) -> tuple[int, int]:
    """Parse ``1,2,K3`` into separate men/kings bitboards."""
    piece_text = text.strip()
    if not piece_text:
        return 0, 0

    men = 0
    kings = 0
    for token in piece_text.split(","):
        item = token.strip()
        if not item:
            raise ValueError("Empty token in piece list (double comma).")

        is_king = item.upper().startswith("K")
        square_text = item[1:] if is_king else item
        if not square_text.isdigit():
            raise ValueError(f"Invalid square token: {token!r}")

        square = int(square_text)
        if square < 1 or square > 32:
            raise ValueError(f"Square out of range 1..32: {square}")

        index = square - 1
        square_mask = 1 << index
        if (men | kings) & square_mask:
            raise ValueError(f"Duplicate square token: {token!r}")

        if is_king:
            kings |= square_mask
        else:
            men |= square_mask

    return men, kings


@dataclass(frozen=True, slots=True)
class CheckersState(valanga.TurnState):
    """Turn state for 32-square bitboard checkers."""

    wm: int
    wk: int
    bm: int
    bk: int
    turn: valanga.Color  # pyright: ignore[reportIncompatibleMethodOverride]
    ply_since_capture_or_man_move: int = 0

    @classmethod
    def standard(
        cls,
        *,
        turn: valanga.Color = valanga.Color.WHITE,
    ) -> CheckersState:
        """Return the canonical opening position for standard checkers."""
        return cls(
            wm=0x00000FFF,
            wk=0,
            bm=0xFFF00000,
            bk=0,
            turn=turn,
            ply_since_capture_or_man_move=0,
        )

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

    def to_text(self) -> str:
        """Return a strict and lossless text representation of the position."""
        turn_char = "W" if self.turn == valanga.Color.WHITE else "B"
        return (
            f"{turn_char};ply={self.ply_since_capture_or_man_move};"
            f"W={_format_piece_list(self.wm, self.wk)};"
            f"B={_format_piece_list(self.bm, self.bk)}"
        )

    @classmethod
    def from_text(cls, text: str) -> CheckersState:
        """Parse a state from ``to_text`` representation."""
        match = _TEXT_RE.match(text)
        if match is None:
            raise ValueError(f"Invalid checkers position text: {text!r}")

        turn_token, ply_text, white_text, black_text = match.groups()
        turn = valanga.Color.WHITE if turn_token.upper() == "W" else valanga.Color.BLACK
        ply = int(ply_text)

        white_men, white_kings = _parse_piece_list(white_text)
        black_men, black_kings = _parse_piece_list(black_text)

        if white_men & white_kings:
            raise ValueError("White square listed as both man and king.")
        if black_men & black_kings:
            raise ValueError("Black square listed as both man and king.")

        white_all = white_men | white_kings
        black_all = black_men | black_kings
        if white_all & black_all:
            raise ValueError("Square occupied by both white and black.")

        return cls(
            wm=white_men,
            wk=white_kings,
            bm=black_men,
            bk=black_kings,
            turn=turn,
            ply_since_capture_or_man_move=ply,
        )

    def __str__(self) -> str:
        """Return the canonical text format used for logs and round trips."""
        return self.to_text()

    def piece_at(self, sq32: int) -> int:
        """Return piece code at sq32 (1..32): 0, 1, 2, -1, -2."""
        if sq32 < 1 or sq32 > 32:
            raise ValueError("sq32 out of range 1..32")

        bit = 1 << (sq32 - 1)
        if self.wm & bit:
            return 1
        if self.wk & bit:
            return 2
        if self.bm & bit:
            return -1
        if self.bk & bit:
            return -2
        return 0

    def pieces_by_square(self) -> list[int]:
        """Return board as a length-32 list using ``piece_at`` encoding."""
        return [self.piece_at(square) for square in range(1, 33)]

