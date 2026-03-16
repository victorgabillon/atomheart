"""Game namespaces exposed by atomheart.

Core lightweight games are always available. Chess is listed only when the
optional chess dependency is installed.
"""

from importlib import import_module

from . import checkers, integer_reduction, morpion, nim

__all__ = ["checkers", "integer_reduction", "morpion", "nim"]

try:
    chess = import_module("atomheart.games.chess")
except ImportError:
    pass
else:
    __all__.append("chess")
