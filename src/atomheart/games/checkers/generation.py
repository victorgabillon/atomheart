"""Legal move generation for checkers."""

from __future__ import annotations

import valanga

from .bitboard import bit, iter_bits
from .geometry import (
    ALL_DIRECTIONS,
    BLACK_FORWARD_DIRECTIONS,
    CAPTURE_TABLES,
    ROW_OF_SQ32,
    STEP_TABLES,
    WHITE_FORWARD_DIRECTIONS,
)
from .move import MoveKey
from .rules import CheckersRules
from .state import CheckersState


def generate_legal_moves(state: CheckersState, rules: CheckersRules) -> list[MoveKey]:
    """Generate all legal move keys for ``state`` according to ``rules``."""
    captures = _generate_capture_moves(state, rules)
    if captures and rules.forced_capture:
        return captures
    quiets = _generate_quiet_moves(state)
    return captures + quiets


def _dirs_for_piece(is_king: bool, turn: valanga.Color) -> tuple[str, ...]:
    if is_king:
        return ALL_DIRECTIONS
    if turn == valanga.Color.WHITE:
        return WHITE_FORWARD_DIRECTIONS
    return BLACK_FORWARD_DIRECTIONS


def _promotion_row(turn: valanga.Color) -> int:
    return 7 if turn == valanga.Color.WHITE else 0


def _side_bitboards(state: CheckersState) -> tuple[int, int, int, int]:
    if state.turn == valanga.Color.WHITE:
        return state.wm, state.wk, state.bm, state.bk
    return state.bm, state.bk, state.wm, state.wk


def _generate_quiet_moves(state: CheckersState) -> list[MoveKey]:
    own_men, own_kings, opp_men, opp_kings = _side_bitboards(state)
    occ = own_men | own_kings | opp_men | opp_kings
    promotion_row = _promotion_row(state.turn)
    moves: list[MoveKey] = []

    for start_sq in iter_bits(own_men | own_kings):
        is_king = bool(own_kings & bit(start_sq))
        for direction in _dirs_for_piece(is_king=is_king, turn=state.turn):
            landing = STEP_TABLES[direction][start_sq]
            if landing == -1 or occ & bit(landing):
                continue
            promotes = (not is_king) and ROW_OF_SQ32[landing] == promotion_row
            moves.append((start_sq, (landing,), (), promotes))

    return moves


def _generate_capture_moves(state: CheckersState, rules: CheckersRules) -> list[MoveKey]:
    own_men, own_kings, opp_men, opp_kings = _side_bitboards(state)
    moves: list[MoveKey] = []

    for start_sq in iter_bits(own_men | own_kings):
        is_king = bool(own_kings & bit(start_sq))
        moves.extend(
            _captures_for_piece(
                start_sq=start_sq,
                is_king=is_king,
                own_men=own_men,
                own_kings=own_kings,
                opp_men=opp_men,
                opp_kings=opp_kings,
                turn=state.turn,
                rules=rules,
            )
        )

    return moves


def _captures_for_piece(
    *,
    start_sq: int,
    is_king: bool,
    own_men: int,
    own_kings: int,
    opp_men: int,
    opp_kings: int,
    turn: valanga.Color,
    rules: CheckersRules,
) -> list[MoveKey]:
    promotion_row = _promotion_row(turn)
    out: list[MoveKey] = []

    def dfs(
        curr_sq: int,
        own_men_now: int,
        own_kings_now: int,
        opp_men_now: int,
        opp_kings_now: int,
        moved_is_king: bool,
        landings: list[int],
        jumped: list[int],
        crowned: bool,
    ) -> None:
        found = False
        occ = own_men_now | own_kings_now | opp_men_now | opp_kings_now
        curr_mask = bit(curr_sq)

        for direction in _dirs_for_piece(is_king=moved_is_king, turn=turn):
            cap_edge = CAPTURE_TABLES[direction][curr_sq]
            jumped_sq, landing_sq = cap_edge.jumped, cap_edge.landing
            if jumped_sq == -1 or landing_sq == -1:
                continue

            jumped_mask = bit(jumped_sq)
            landing_mask = bit(landing_sq)
            if not ((opp_men_now | opp_kings_now) & jumped_mask):
                continue
            if occ & landing_mask:
                continue

            found = True
            opp_men_next = opp_men_now
            opp_kings_next = opp_kings_now
            if opp_kings_now & jumped_mask:
                opp_kings_next &= ~jumped_mask
            else:
                opp_men_next &= ~jumped_mask

            own_men_next = own_men_now
            own_kings_next = own_kings_now
            if moved_is_king:
                own_kings_next = (own_kings_now & ~curr_mask) | landing_mask
            else:
                own_men_next = (own_men_now & ~curr_mask) | landing_mask

            became_king = (not moved_is_king) and ROW_OF_SQ32[landing_sq] == promotion_row
            if became_king and rules.crowning_ends_turn:
                out.append(
                    (
                        start_sq,
                        tuple([*landings, landing_sq]),
                        tuple([*jumped, jumped_sq]),
                        True,
                    )
                )
                continue

            own_men_recur = own_men_next
            own_kings_recur = own_kings_next
            if became_king:
                own_men_recur &= ~landing_mask
                own_kings_recur |= landing_mask

            dfs(
                curr_sq=landing_sq,
                own_men_now=own_men_recur,
                own_kings_now=own_kings_recur,
                opp_men_now=opp_men_next,
                opp_kings_now=opp_kings_next,
                moved_is_king=moved_is_king or became_king,
                landings=[*landings, landing_sq],
                jumped=[*jumped, jumped_sq],
                crowned=crowned or became_king,
            )

        if not found and jumped:
            out.append((start_sq, tuple(landings), tuple(jumped), crowned))

    dfs(
        curr_sq=start_sq,
        own_men_now=own_men,
        own_kings_now=own_kings,
        opp_men_now=opp_men,
        opp_kings_now=opp_kings,
        moved_is_king=is_king,
        landings=[],
        jumped=[],
        crowned=False,
    )

    return out
