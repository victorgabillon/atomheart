"""Morpion Solitaire game primitives and Valanga adapter."""

# pylint: disable=duplicate-code

from . import canonical as _canonical
from .dynamics import MorpionDynamics, action_to_played_move
from .state import MorpionState, Variant, initial_state

Move = _canonical.Move
apply_rooted_symmetry = _canonical.apply_rooted_symmetry
canonical_move_set_hash = _canonical.canonical_move_set_hash
canonical_move_set_tag = _canonical.canonical_move_set_tag
canonical_move_set_tag_d4 = _canonical.canonical_move_set_tag_d4
canonical_move_set_tag_d4_translation = _canonical.canonical_move_set_tag_d4_translation

__all__ = [
    "MorpionDynamics",
    "MorpionState",
    "Move",
    "Variant",
    "action_to_played_move",
    "apply_rooted_symmetry",
    "canonical_move_set_hash",
    "canonical_move_set_tag",
    "canonical_move_set_tag_d4",
    "canonical_move_set_tag_d4_translation",
    "initial_state",
]
