"""Checkers state text serialization tests."""

import pytest
import valanga

from atomheart.games.checkers.state import CheckersState


def test_standard_allows_turn_override() -> None:
    """Standard constructor should support setting side to move."""
    state = CheckersState.standard(turn=valanga.Color.BLACK)

    assert state.turn == valanga.Color.BLACK
    assert state.wm == 0x00000FFF
    assert state.bm == 0xFFF00000


def test_to_text_from_text_roundtrip_initial() -> None:
    """Initial position should round-trip exactly through text."""
    state = CheckersState.standard()
    text = state.to_text()

    assert (
        text
        == "W;ply=0;W=1,2,3,4,5,6,7,8,9,10,11,12;B=21,22,23,24,25,26,27,28,29,30,31,32"
    )
    assert CheckersState.from_text(text) == state
    assert str(state) == text


def test_to_text_from_text_roundtrip_with_kings() -> None:
    """Mixed men and kings should preserve all fields through round trip."""
    state = CheckersState(
        wm=(1 << 0) | (1 << 4),
        wk=1 << 2,
        bm=1 << 20,
        bk=(1 << 25) | (1 << 31),
        turn=valanga.Color.BLACK,
        ply_since_capture_or_man_move=7,
    )

    rebuilt = CheckersState.from_text(state.to_text())

    assert rebuilt == state


def test_from_text_rejects_invalid_inputs() -> None:
    """Parser should fail fast on malformed inputs."""
    with pytest.raises(ValueError):
        CheckersState.from_text("not-a-position")

    assert CheckersState.from_text("W;ply=0;W=;B=") == CheckersState(
        wm=0,
        wk=0,
        bm=0,
        bk=0,
        turn=valanga.Color.WHITE,
        ply_since_capture_or_man_move=0,
    )

    with pytest.raises(ValueError):
        CheckersState.from_text("W;ply=0;W=0;B=")

    with pytest.raises(ValueError):
        CheckersState.from_text("W;ply=0;W=1,1;B=")

    with pytest.raises(ValueError):
        CheckersState.from_text("W;ply=0;W=1;B=1")

    with pytest.raises(ValueError):
        CheckersState.from_text("W;ply=0;W=1,,2;B=")


def test_piece_helpers() -> None:
    """piece_at and pieces_by_square should expose a stable piece encoding."""
    state = CheckersState(
        wm=1 << 0,
        wk=1 << 1,
        bm=1 << 2,
        bk=1 << 3,
        turn=valanga.Color.WHITE,
    )

    assert state.piece_at(1) == 1
    assert state.piece_at(2) == 2
    assert state.piece_at(3) == -1
    assert state.piece_at(4) == -2
    assert state.piece_at(5) == 0
    assert len(state.pieces_by_square()) == 32

    with pytest.raises(ValueError):
        state.piece_at(0)
