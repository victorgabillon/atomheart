"""Defines the IMove interface for chess moves."""

from abc import abstractmethod
from typing import Annotated, Protocol

from .utils import MoveUci

# numbering scheme for actions in the node of the trees
type MoveKey = Annotated[int, "Move key identifier"]  # Now properly annotated


class IMove(Protocol):
    """Interface for a chess move.

    Args:
        Protocol (Protocol): Protocol for type checking.

    """

    @abstractmethod
    def uci(self) -> MoveUci:
        """Return the UCI string representation of the move.

        Returns:
            moveUci: The UCI string representation of the move.

        """
        ...
