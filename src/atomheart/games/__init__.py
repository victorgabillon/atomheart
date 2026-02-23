"""Collection of game modules supported by atomheart.

Available games:
- checkers: International checkers/draughts
- chess: Standard chess (requires chess and optionally shakmaty_python_binding)
"""

from . import checkers

__all__ = ["checkers"]

try:
    from . import chess  # noqa: F401

    __all__.append("chess")
except ImportError:
    pass
