"""
Utilities for move UCI representation.
"""

from typing import Annotated

type MoveUci = Annotated[str, "a string representing a move uci"]

type HalfMove = Annotated[int, "an integer representing a half move"]
