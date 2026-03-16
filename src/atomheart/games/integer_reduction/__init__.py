"""Integer reduction game primitives and Valanga adapters."""

from .dynamics import IntegerReductionDynamics
from .reversible import IntegerReductionReversibleDynamics, IntegerReductionUndo
from .state import IntegerReductionState

__all__ = [
    "IntegerReductionDynamics",
    "IntegerReductionReversibleDynamics",
    "IntegerReductionState",
    "IntegerReductionUndo",
]
