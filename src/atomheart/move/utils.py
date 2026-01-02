"""
Utilities for move UCI representation.
"""

from typing import Annotated, TypeAlias

MoveUci: TypeAlias = Annotated[str, "a string representing a move uci"]
