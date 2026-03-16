"""Collection of game modules supported by atomheart.

Available games:
- checkers: International checkers/draughts
- chess: Standard chess (requires chess and optionally shakmaty_python_binding)
- integer_reduction: Single-player integer reduction toy game
- nim: Single-pile subtraction Nim
- morpion: Morpion Solitaire (5T/5D variants)
"""

from . import checkers, integer_reduction, morpion, nim

__all__ = ["checkers", "integer_reduction", "morpion", "nim"]

try:
    from . import chess  # noqa: F401

    __all__.append("chess")
except ImportError:
    pass
