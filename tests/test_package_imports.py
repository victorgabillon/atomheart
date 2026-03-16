"""Package-level import tests for optional chess exposure."""

from importlib import import_module


def _has_top_level_chess_support() -> bool:
    """Return whether the top-level optional chess exports are available."""
    atomheart = import_module("atomheart")
    return all(
        hasattr(atomheart, name)
        for name in (
            "BoardChi",
            "ChessDynamics",
            "ChessState",
            "create_board_chi",
            "create_board_chi_from_pychess_board",
        )
    )


def _has_games_chess_support() -> bool:
    """Return whether the chess game namespace itself is importable."""
    try:
        import_module("atomheart.games.chess")
    except ImportError:
        return False
    return True


def test_core_top_level_exports_are_available() -> None:
    """Lightweight top-level exports should always be available."""
    atomheart = import_module("atomheart")

    for name in (
        "CheckersDynamics",
        "IntegerReductionDynamics",
        "MorpionDynamics",
        "NimDynamics",
    ):
        assert hasattr(atomheart, name)


def test_games_namespace_lists_core_games() -> None:
    """The games namespace should list lightweight games unconditionally."""
    games = import_module("atomheart.games")

    assert {"checkers", "integer_reduction", "morpion", "nim"} <= set(games.__all__)


def test_chess_exports_follow_dependency_availability() -> None:
    """Chess exports should appear only when the chess dependency is installed."""
    atomheart = import_module("atomheart")
    games = import_module("atomheart.games")

    if _has_top_level_chess_support():
        assert "chess" in games.__all__
        assert hasattr(atomheart, "ChessDynamics")
        assert hasattr(atomheart, "ChessState")
    else:
        assert "chess" not in games.__all__
        assert not hasattr(atomheart, "ChessDynamics")


def test_games_namespace_chess_listing_matches_importable_surface() -> None:
    """The games namespace should reflect the actual optional chess surface."""
    games = import_module("atomheart.games")

    if _has_games_chess_support():
        assert "chess" in games.__all__
    else:
        assert "chess" not in games.__all__


def test_importing_lightweight_game_modules_remains_direct() -> None:
    """Concrete lightweight game-module imports should keep working."""
    from atomheart.games import nim as nim_namespace

    nim = import_module("atomheart.games.nim")
    integer_reduction = import_module("atomheart.games.integer_reduction")

    assert nim_namespace.NimState.__name__ == "NimState"
    assert nim.NimState.__name__ == "NimState"
    assert integer_reduction.IntegerReductionState.__name__ == "IntegerReductionState"
