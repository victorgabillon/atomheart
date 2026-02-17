"""Valanga adapters based on :class:`IBoard`."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import valanga
from valanga.over_event import HowOver, Winner

if TYPE_CHECKING:
    import chess

    from atomheart.board.iboard import IBoard
    from atomheart.move.imove import MoveKey


@dataclass(frozen=True, slots=True)
class ChessState(valanga.TurnState):
    """Pure observation wrapper around an :class:`IBoard`."""

    board: "IBoard"

    @property
    def tag(self) -> valanga.StateTag:
        """Return the board tag."""
        return self.board.tag

    def is_game_over(self) -> bool:
        """Return whether the game is over."""
        return self.board.is_game_over()

    def pprint(self) -> str:
        """Return a pretty-printed board string."""
        return self.board.print_chess_board()

    @property
    def turn(self) -> valanga.Color:
        """Return the current turn color."""
        return self.board.turn


class ChessDynamics(valanga.Dynamics[ChessState]):
    """Rule engine for chess transitions from an :class:`IBoard` state."""

    def legal_actions(
        self, state: ChessState
    ) -> valanga.BranchKeyGeneratorP[valanga.BranchKey]:
        """Return legal move keys for the current state."""
        return state.board.legal_moves

    def step(
        self, state: ChessState, action: valanga.BranchKey
    ) -> valanga.Transition[ChessState]:
        """Copy and advance the board with ``action``."""
        move_key = cast("MoveKey", action)

        board2 = state.board.copy(stack=False, deep_copy_legal_moves=True)
        mods = board2.play_move_key(move_key)
        is_over = board2.is_game_over()

        over_event: valanga.OverEvent | None = None
        if is_over:
            over_event = _over_event_from_board(board2)

        return valanga.Transition(
            next_state=ChessState(board2),
            modifications=mods,
            is_over=is_over,
            over_event=over_event,
            info={
                "result": board2.result(claim_draw=True) if is_over else "*",
                # Only compute termination when game is over; otherwise it may assert.
                "termination": board2.termination() if is_over else None,
            },
        )

    def action_name(self, state: ChessState, action: valanga.BranchKey) -> str:
        """Return the UCI name of a move key."""
        return state.board.get_uci_from_move_key(cast("MoveKey", action))

    def action_from_name(self, state: ChessState, name: str) -> valanga.BranchKey:
        """Return the move key for a UCI move name."""
        return state.board.get_move_key_from_uci(name)


def _over_event_from_board(board: "IBoard") -> valanga.OverEvent:
    """Convert board end-of-game info into a Valanga over event."""
    result = board.result(claim_draw=True)
    termination: chess.Termination | None = board.termination()

    if result == "1-0":
        return valanga.OverEvent(HowOver.WIN, Winner.WHITE, termination)

    if result == "0-1":
        return valanga.OverEvent(HowOver.WIN, Winner.BLACK, termination)

    if result == "1/2-1/2":
        return valanga.OverEvent(
            HowOver.DRAW,
            Winner.NO_KNOWN_WINNER,
            termination,
        )

    return valanga.OverEvent(
        HowOver.DO_NOT_KNOW_OVER,
        Winner.NO_KNOWN_WINNER,
        termination,
    )
