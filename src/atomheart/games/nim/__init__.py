"""Nim game primitives and Valanga adapters."""

from .dynamics import NimDynamics
from .reversible import NimReversibleDynamics, NimUndo
from .state import NimState

__all__ = [
    "NimDynamics",
    "NimReversibleDynamics",
    "NimState",
    "NimUndo",
]
