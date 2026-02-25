"""Collection of game modules supported by atomheart.

Available games:
- checkers: International checkers/draughts
- chess: Standard chess (requires chess and optionally shakmaty_python_binding)
- morpion: Morpion Solitaire (5T/5D variants)
"""

from . import checkers
from . import morpion

__all__ = ["checkers", "morpion"]

try:
    from . import chess  # noqa: F401

    __all__.append("chess")
except ImportError:
    pass
