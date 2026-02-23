"""Ruleset configuration for checkers variants."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckersRules:
    """Configurable rules used by checkers dynamics and generators."""

    forced_capture: bool = True
    crowning_ends_turn: bool = True
