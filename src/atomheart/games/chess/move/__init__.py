"""Chess move implementations and utilities."""

from importlib.util import find_spec

from .imove import IMove
from .move_factory import MoveFactory, create_move_factory
from .utils import MoveUci

__all__ = [
    "IMove",
    "MoveFactory",
    "MoveUci",
    "create_move_factory",
]

if find_spec("shakmaty_python_binding") is not None:
    from .rust_move import RustMove  # noqa: F401

    __all__.append("RustMove")
