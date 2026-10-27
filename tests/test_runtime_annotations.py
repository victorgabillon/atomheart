"""Runtime annotation and layout contracts for the Python 3.14 public API."""

from annotationlib import Format, get_annotations
from collections.abc import Mapping
from dataclasses import fields
from typing import get_type_hints

import pytest

from atomheart import (
    CheckersDynamics,
    CheckersReversibleDynamics,
    CheckersState,
    IntegerReductionDynamics,
    IntegerReductionReversibleDynamics,
    IntegerReductionState,
    MorpionDynamics,
    MorpionState,
    NimDynamics,
    NimReversibleDynamics,
    NimState,
)
from atomheart.games._branch_key_gen import TupleBranchKeyGen
from atomheart.games.morpion import initial_state
from atomheart.games.morpion.canonical import canonical_move_set_tag
from atomheart.games.morpion.state import Move
from valanga import Color


@pytest.mark.parametrize(
    "cls",
    [CheckersState, IntegerReductionState, MorpionState, NimState],
)
def test_public_state_dataclass_annotations_resolve(cls: type) -> None:
    """All concrete state fields expose evaluated types without missing imports."""
    hints = get_type_hints(cls)
    for f in fields(cls):
        assert f.name in hints
        assert not isinstance(hints[f.name], str)
    assert all(
        isinstance(value, str)
        for value in get_annotations(cls, format=Format.STRING).values()
    )


@pytest.mark.parametrize(
    "cls",
    [
        CheckersDynamics,
        IntegerReductionDynamics,
        MorpionDynamics,
        NimDynamics,
        CheckersReversibleDynamics,
        IntegerReductionReversibleDynamics,
        NimReversibleDynamics,
    ],
)
def test_dynamics_method_annotations_resolve(cls: type) -> None:
    """Core protocol implementations keep their runtime annotation dependencies."""
    for method in (cls.__init__, cls.legal_actions):
        assert get_type_hints(method)


def test_morpion_factory_and_canonical_function_annotations() -> None:
    """Typed native factories preserve the existing empty move-set value."""
    hints = get_type_hints(MorpionState)
    assert hints["dir_usage"] == Mapping[tuple[tuple[int, int], int], int]
    move_field = next(f for f in fields(MorpionState) if f.name == "played_moves")
    assert move_field.default_factory() == frozenset[Move]()
    assert get_type_hints(canonical_move_set_tag)["return"] == tuple[Move, ...]
    assert initial_state().played_moves == frozenset()


def test_state_layout_and_branch_generator_self_reference() -> None:
    """Role state wrappers retain slots and generators expose native self types."""
    state = NimState(stones=3, turn=Color.WHITE)
    assert not hasattr(state, "__dict__")
    generator = TupleBranchKeyGen((1, 2))
    assert list(generator) == [1, 2]
    assert list(generator.copy_with_reset()) == [1, 2]
    assert (
        get_type_hints(TupleBranchKeyGen.copy_with_reset)["return"].__origin__
        is TupleBranchKeyGen
    )
