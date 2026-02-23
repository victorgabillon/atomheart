"""ReversibleDynamics implementation for checkers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import valanga

from .apply import validate_move
from .bitboard import bit
from .move import MoveKey
from .state import CheckersState


@dataclass(frozen=True, slots=True)
class CheckersUndo:
    """Compact undo data for make/unmake on checkers bitboards."""

    turn: valanga.Color
    from_sq: int
    to_sq: int
    moved_was_king: bool
    promoted: bool
    captured: tuple[tuple[int, bool], ...]
    prev_ply: int


if TYPE_CHECKING:
    from .dynamics import CheckersDynamics


class CheckersReversibleDynamics(valanga.ReversibleDynamics[MoveKey, CheckersUndo]):
    """In-place reversible dynamics for checkers search."""

    dynamics: CheckersDynamics
    _wm: int
    _wk: int
    _bm: int
    _bk: int
    _turn: valanga.Color
    _ply: int

    def __init__(self, dynamics: CheckersDynamics, state: CheckersState) -> None:
        """Initialize reversible dynamics with a dynamics engine and initial state."""
        self.dynamics = dynamics
        self._wm = state.wm
        self._wk = state.wk
        self._bm = state.bm
        self._bk = state.bk
        self._turn = state.turn
        self._ply = state.ply_since_capture_or_man_move

    @property  # type: ignore[override]
    def state(self) -> CheckersState:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Build immutable state snapshot from current mutable bitboards."""
        return CheckersState(
            wm=self._wm,
            wk=self._wk,
            bm=self._bm,
            bk=self._bk,
            turn=self._turn,
            ply_since_capture_or_man_move=self._ply,
        )

    @state.setter
    def state(self, value: CheckersState) -> None:
        self._wm = value.wm
        self._wk = value.wk
        self._bm = value.bm
        self._bk = value.bk
        self._turn = value.turn
        self._ply = value.ply_since_capture_or_man_move

    def legal_actions(self) -> valanga.BranchKeyGeneratorP[MoveKey]:
        """Return legal actions from current state."""
        return self.dynamics.legal_actions(self.state)

    def push(self, action: valanga.BranchKey) -> CheckersUndo:  # pylint: disable=too-many-branches
        """Apply action in-place and return undo information."""
        move = self.dynamics._as_move_key(action)  # pyright: ignore[reportPrivateUsage]  # pylint: disable=protected-access
        validate_move(state=self.state, move=move, rules=self.dynamics.rules)
        start_sq, landings, jumped, promotes = move
        to_sq = landings[-1]
        start_mask = bit(start_sq)
        to_mask = bit(to_sq)

        if self._turn == valanga.Color.WHITE:
            own_men, own_kings = self._wm, self._wk
            opp_men, opp_kings = self._bm, self._bk
        else:
            own_men, own_kings = self._bm, self._bk
            opp_men, opp_kings = self._wm, self._wk

        moved_was_king = bool(own_kings & start_mask)
        if moved_was_king:
            own_kings &= ~start_mask
        elif own_men & start_mask:
            own_men &= ~start_mask
        else:
            raise ValueError(f"No piece on start square {start_sq}.")  # noqa: TRY003

        captured: list[tuple[int, bool]] = []
        for jumped_sq in jumped:
            jumped_mask = bit(jumped_sq)
            if opp_kings & jumped_mask:
                opp_kings &= ~jumped_mask
                captured.append((jumped_sq, True))
            elif opp_men & jumped_mask:
                opp_men &= ~jumped_mask
                captured.append((jumped_sq, False))
            else:
                raise ValueError(f"No opponent piece to capture on square {jumped_sq}.")  # noqa: TRY003

        if moved_was_king or promotes:
            own_kings |= to_mask
        else:
            own_men |= to_mask

        undo = CheckersUndo(
            turn=self._turn,
            from_sq=start_sq,
            to_sq=to_sq,
            moved_was_king=moved_was_king,
            promoted=promotes,
            captured=tuple(captured),
            prev_ply=self._ply,
        )

        if jumped or not moved_was_king:
            self._ply = 0
        else:
            self._ply += 1

        if self._turn == valanga.Color.WHITE:
            self._wm, self._wk = own_men, own_kings
            self._bm, self._bk = opp_men, opp_kings
            self._turn = valanga.Color.BLACK
        else:
            self._bm, self._bk = own_men, own_kings
            self._wm, self._wk = opp_men, opp_kings
            self._turn = valanga.Color.WHITE

        return undo

    def pop(self, undo: CheckersUndo) -> None:
        """Revert state from undo information."""
        self._turn = undo.turn
        self._ply = undo.prev_ply

        from_mask = bit(undo.from_sq)
        to_mask = bit(undo.to_sq)

        if self._turn == valanga.Color.WHITE:
            own_men, own_kings = self._wm, self._wk
            opp_men, opp_kings = self._bm, self._bk
        else:
            own_men, own_kings = self._bm, self._bk
            opp_men, opp_kings = self._wm, self._wk

        if undo.moved_was_king or undo.promoted:
            own_kings &= ~to_mask
        else:
            own_men &= ~to_mask

        if undo.moved_was_king:
            own_kings |= from_mask
        else:
            own_men |= from_mask

        for captured_sq, captured_was_king in undo.captured:
            captured_mask = bit(captured_sq)
            if captured_was_king:
                opp_kings |= captured_mask
            else:
                opp_men |= captured_mask

        if self._turn == valanga.Color.WHITE:
            self._wm, self._wk = own_men, own_kings
            self._bm, self._bk = opp_men, opp_kings
        else:
            self._bm, self._bk = own_men, own_kings
            self._wm, self._wk = opp_men, opp_kings

    def action_name(self, action: valanga.BranchKey) -> str:
        """Render a move name using state-aware dynamics."""
        return self.dynamics.action_name(self.state, action)

    def action_from_name(self, name: str) -> MoveKey:
        """Parse/resolve a move name from current state."""
        return self.dynamics.action_from_name(self.state, name)
