"""Regression tests for deterministic Morpion state tags."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from atomheart.games.morpion import MorpionDynamics, Variant, initial_state

ROOT = Path(__file__).resolve().parents[2]
MORPION_TAG_SOURCE_FILES = (
    ROOT / "src" / "atomheart" / "games" / "morpion" / "canonical.py",
    ROOT / "src" / "atomheart" / "games" / "morpion" / "state.py",
)


def _run_with_hash_seed(code: str, seed: int) -> str:
    """Run Python code under one explicit hash seed and return stdout."""
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    env["PYTHONPATH"] = (
        str(ROOT / "src")
        if not env.get("PYTHONPATH")
        else f"{ROOT / 'src'}{os.pathsep}{env['PYTHONPATH']}"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_morpion_state_tag_is_stable_across_python_hash_seeds() -> None:
    """The same replayed Morpion state should have the same tag after restart."""
    code = """
from atomheart.games.morpion import MorpionDynamics, Variant, initial_state

dynamics = MorpionDynamics()
state = initial_state(variant=Variant.TOUCHING_5T)
for _ in range(4):
    action = dynamics.legal_actions(state).get_all()[0]
    state = dynamics.step(state, action).next_state
print(state.tag)
"""

    assert _run_with_hash_seed(code, 0) == _run_with_hash_seed(code, 1)


def test_canonical_move_set_hash_is_stable_across_python_hash_seeds() -> None:
    """The canonical move-set hash should not depend on Python hash randomization."""
    code = """
from atomheart.games.morpion import (
    MorpionDynamics,
    Variant,
    canonical_move_set_hash,
    initial_state,
)

dynamics = MorpionDynamics()
state = initial_state(variant=Variant.TOUCHING_5T)
for _ in range(4):
    action = dynamics.legal_actions(state).get_all()[0]
    state = dynamics.step(state, action).next_state
print(canonical_move_set_hash(state.played_moves))
"""

    assert _run_with_hash_seed(code, 0) == _run_with_hash_seed(code, 1)


def test_symmetric_states_share_canonical_tag_and_stable_state_tag() -> None:
    """Symmetric-equivalent successors should still collide under canonical tags."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)

    next_state_a = dynamics.step(state, (0, -6, -2, 0)).next_state
    next_state_b = dynamics.step(state, (1, 1, -6, 0)).next_state

    assert next_state_a.canonical_tag == next_state_b.canonical_tag
    assert next_state_a.tag == next_state_b.tag
    assert isinstance(next_state_a.tag, int)


def test_state_tag_matches_canonical_hash_and_legacy_geometry_tag_is_int() -> None:
    """State tags should use canonical identity while legacy geometry stays int-shaped."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)
    for _ in range(4):
        action = dynamics.legal_actions(state).get_all()[0]
        state = dynamics.step(state, action).next_state

    assert state.tag == state.canonical_hash
    assert isinstance(state._legacy_geometry_tag, int)


def test_morpion_tag_sources_do_not_use_builtin_hash() -> None:
    """Persisted Morpion tag paths must not use Python's randomized hash."""
    builtin_hash_call = re.compile(r"(?<![.\w])hash\(")
    offenders: list[str] = []

    for path in MORPION_TAG_SOURCE_FILES:
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            if builtin_hash_call.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{line_number}: {line}")

    assert offenders == []
