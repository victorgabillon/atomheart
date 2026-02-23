"""Move application and validation for checkers states."""

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


def _dirs_for_piece(is_king: bool, turn: valanga.Color) -> tuple[str, ...]:
    if is_king:
        return ALL_DIRECTIONS
    if turn == valanga.Color.WHITE:
        return WHITE_FORWARD_DIRECTIONS
    return BLACK_FORWARD_DIRECTIONS


def _promotion_row(turn: valanga.Color) -> int:
    return 7 if turn == valanga.Color.WHITE else 0


def _has_any_capture(
    *,
    own_men: int,
    own_kings: int,
    opp_men: int,
    opp_kings: int,
    turn: valanga.Color,
) -> bool:
    """Return whether side-to-move has at least one legal capture edge."""
    occ_opp = opp_men | opp_kings
    occ_all = own_men | own_kings | occ_opp
    for start_sq in iter_bits(own_men | own_kings):
        is_king = bool(own_kings & bit(start_sq))
        for direction in _dirs_for_piece(is_king=is_king, turn=turn):
            edge = CAPTURE_TABLES[direction][start_sq]
            if edge.jumped == -1:
                continue
            jumped_mask = bit(edge.jumped)
            landing_mask = bit(edge.landing)
            if (occ_opp & jumped_mask) and not (occ_all & landing_mask):
                return True
    return False


def validate_move(state: CheckersState, move: MoveKey, rules: CheckersRules) -> None:
    """Validate move geometry and occupancy against the current state."""
    start_sq, landings, jumped, promotes = move

    if len(landings) == 0:
        raise ValueError("Move must contain at least one landing square.")
    if len(jumped) == 0 and len(landings) != 1:
        raise ValueError("Quiet move must have exactly one landing square.")
    if len(jumped) > 0 and len(jumped) != len(landings):
        raise ValueError("Capture move must satisfy len(jumped) == len(landings).")
    if start_sq in landings:
        raise ValueError("Move start square cannot appear in landings.")
    if len(set(jumped)) != len(jumped):
        raise ValueError("Capture move cannot repeat jumped squares.")
    if len(set(landings)) != len(landings):
        raise ValueError("Move cannot repeat landing squares.")

    if not (0 <= start_sq < 32):
        raise ValueError(f"Invalid start square: {start_sq}.")

    if any(not (0 <= sq < 32) for sq in landings):
        raise ValueError("All landing squares must be in range [0, 31].")
    if any(not (0 <= sq < 32) for sq in jumped):
        raise ValueError("All jumped squares must be in range [0, 31].")

    if state.turn == valanga.Color.WHITE:
        own_men, own_kings = state.wm, state.wk
        opp_men, opp_kings = state.bm, state.bk
    else:
        own_men, own_kings = state.bm, state.bk
        opp_men, opp_kings = state.wm, state.wk

    start_mask = bit(start_sq)
    moved_is_king = bool(own_kings & start_mask)
    if not moved_is_king and not (own_men & start_mask):
        raise ValueError(f"No side-to-move piece on start square {start_sq}.")

    occ = own_men | own_kings | opp_men | opp_kings
    if len(jumped) == 0:
        if rules.forced_capture and _has_any_capture(
            own_men=own_men,
            own_kings=own_kings,
            opp_men=opp_men,
            opp_kings=opp_kings,
            turn=state.turn,
        ):
            raise ValueError("Capture is mandatory.")

        landing = landings[0]
        landing_mask = bit(landing)
        if occ & landing_mask:
            raise ValueError("Quiet move destination must be empty.")

        if not any(
            STEP_TABLES[direction][start_sq] == landing
            for direction in _dirs_for_piece(is_king=moved_is_king, turn=state.turn)
        ):
            raise ValueError("Quiet move does not match legal step geometry.")

        crowned = (
            (not moved_is_king)
            and ROW_OF_SQ32[landing] == _promotion_row(state.turn)
        )
        if promotes != crowned:
            raise ValueError(
                "Move promote flag is inconsistent with quiet move landing."
            )
        return

    curr_sq = start_sq
    own_men_now, own_kings_now = own_men, own_kings
    opp_men_now, opp_kings_now = opp_men, opp_kings
    crowned = False

    for i, (jumped_sq, landing_sq) in enumerate(zip(jumped, landings, strict=True)):
        occ_now = own_men_now | own_kings_now | opp_men_now | opp_kings_now
        jumped_mask = bit(jumped_sq)
        landing_mask = bit(landing_sq)

        if not ((opp_men_now | opp_kings_now) & jumped_mask):
            raise ValueError("Capture step jumped square must contain an opponent piece.")
        if occ_now & landing_mask:
            raise ValueError("Capture landing square must be empty when reached.")

        matched = any(
            (
                CAPTURE_TABLES[direction][curr_sq].jumped == jumped_sq
                and CAPTURE_TABLES[direction][curr_sq].landing == landing_sq
            )
            for direction in _dirs_for_piece(is_king=moved_is_king, turn=state.turn)
        )
        if not matched:
            raise ValueError("Capture step does not match legal capture geometry.")

        curr_mask = bit(curr_sq)
        if moved_is_king:
            own_kings_now = (own_kings_now & ~curr_mask) | landing_mask
        else:
            own_men_now = (own_men_now & ~curr_mask) | landing_mask

        if opp_kings_now & jumped_mask:
            opp_kings_now &= ~jumped_mask
        else:
            opp_men_now &= ~jumped_mask

        became_king = (not moved_is_king) and ROW_OF_SQ32[landing_sq] == _promotion_row(
            state.turn
        )
        if became_king:
            crowned = True
            if rules.crowning_ends_turn and i != len(jumped) - 1:
                raise ValueError(
                    "Capture sequence cannot continue after crowning when rules.crowning_ends_turn is True."
                )
            own_men_now &= ~landing_mask
            own_kings_now |= landing_mask
            moved_is_king = True

        curr_sq = landing_sq

    if promotes != crowned:
        raise ValueError("Move promote flag is inconsistent with capture sequence.")


def apply_move(
    state: CheckersState,
    move: MoveKey,
    rules: CheckersRules,
    *,
    validate: bool = True,
) -> CheckersState:
    """Apply a move to a state and return the next state."""
    if validate:
        validate_move(state=state, move=move, rules=rules)

    start_sq, landings, jumped, promotes = move
    to_sq = landings[-1]

    if state.turn == valanga.Color.WHITE:
        own_men, own_kings = state.wm, state.wk
        opp_men, opp_kings = state.bm, state.bk
    else:
        own_men, own_kings = state.bm, state.bk
        opp_men, opp_kings = state.wm, state.wk

    start_mask = bit(start_sq)
    to_mask = bit(to_sq)
    moved_was_king = bool(own_kings & start_mask)

    if moved_was_king:
        own_kings &= ~start_mask
    else:
        own_men &= ~start_mask

    for jumped_sq in jumped:
        jumped_mask = bit(jumped_sq)
        if opp_kings & jumped_mask:
            opp_kings &= ~jumped_mask
        else:
            opp_men &= ~jumped_mask

    if moved_was_king or promotes:
        own_kings |= to_mask
    else:
        own_men |= to_mask

    if jumped or not moved_was_king:
        next_ply = 0
    else:
        next_ply = state.ply_since_capture_or_man_move + 1

    next_turn = (
        valanga.Color.BLACK if state.turn == valanga.Color.WHITE else valanga.Color.WHITE
    )

    if state.turn == valanga.Color.WHITE:
        return CheckersState(
            wm=own_men,
            wk=own_kings,
            bm=opp_men,
            bk=opp_kings,
            turn=next_turn,
            ply_since_capture_or_man_move=next_ply,
        )

    return CheckersState(
        wm=opp_men,
        wk=opp_kings,
        bm=own_men,
        bk=own_kings,
        turn=next_turn,
        ply_since_capture_or_man_move=next_ply,
    )
