#!/usr/bin/env python3
"""Count distinct Morpion states by depth, with optional symmetry reduction.

Example:
    python tools/morpion_count_states.py --depth 3 --variant 5T
    python tools/morpion_count_states.py --depth 4 --variant 5D --show-samples
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _ensure_package(name: str, path: Path) -> ModuleType:
    """Create a lightweight package module when package import side effects fail."""
    module = sys.modules.get(name)
    if module is None:
        module = ModuleType(name)
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module
    return module


def _load_module(name: str, path: Path) -> ModuleType:
    """Load a module directly from a source file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        msg = f"Could not create module spec for {name} from {path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


try:
    from atomheart.games.morpion import MorpionDynamics, MorpionState, Variant, initial_state
except Exception:
    _ensure_package("atomheart", SRC_DIR / "atomheart")
    _ensure_package("atomheart.games", SRC_DIR / "atomheart" / "games")
    _ensure_package(
        "atomheart.games.morpion",
        SRC_DIR / "atomheart" / "games" / "morpion",
    )
    _load_module(
        "atomheart.games.morpion.canonical",
        SRC_DIR / "atomheart" / "games" / "morpion" / "canonical.py",
    )
    _load_module(
        "atomheart.games.morpion.state",
        SRC_DIR / "atomheart" / "games" / "morpion" / "state.py",
    )
    _load_module(
        "atomheart.games.morpion.dynamics",
        SRC_DIR / "atomheart" / "games" / "morpion" / "dynamics.py",
    )
    morpion_module = _load_module(
        "atomheart.games.morpion",
        SRC_DIR / "atomheart" / "games" / "morpion" / "__init__.py",
    )
    MorpionDynamics = morpion_module.MorpionDynamics
    MorpionState = morpion_module.MorpionState
    Variant = morpion_module.Variant
    initial_state = morpion_module.initial_state


@dataclass(frozen=True, slots=True)
class LayerStats:
    """Per-depth counting results."""

    depth: int
    generated_successors: int
    unique_raw: int
    unique_canonical: int


def explore(
    depth: int,
    variant: Variant,
) -> tuple[list[LayerStats], dict[int, list[MorpionState]]]:
    """Breadth-first exploration up to ``depth`` plies."""
    dynamics = MorpionDynamics()
    start = initial_state(variant=variant)

    current_layer = [start]
    samples_by_depth: dict[int, list[MorpionState]] = {0: [start]}
    stats = [
        LayerStats(
            depth=0,
            generated_successors=0,
            unique_raw=1,
            unique_canonical=1,
        )
    ]

    for ply in range(1, depth + 1):
        next_by_raw_tag: dict[int, MorpionState] = {}
        canonical_seen: set[tuple[object, ...]] = set()
        generated_successors = 0

        for state in current_layer:
            for action in dynamics.legal_actions(state).get_all():
                generated_successors += 1
                next_state = dynamics.step(state, action).next_state
                next_by_raw_tag.setdefault(next_state.tag, next_state)
                canonical_seen.add(next_state.canonical_tag)

        next_layer = list(next_by_raw_tag.values())
        samples_by_depth[ply] = next_layer[:5]

        stats.append(
            LayerStats(
                depth=ply,
                generated_successors=generated_successors,
                unique_raw=len(next_layer),
                unique_canonical=len(canonical_seen),
            )
        )
        current_layer = next_layer

    return stats, samples_by_depth


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Maximum search depth in plies.",
    )
    parser.add_argument(
        "--variant",
        choices=("5T", "5D"),
        default="5T",
        help="Morpion variant.",
    )
    parser.add_argument(
        "--show-samples",
        action="store_true",
        help="Print a few sample states from each depth.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the state-count exploration and print a compact summary."""
    args = parse_args()
    variant = Variant.TOUCHING_5T if args.variant == "5T" else Variant.DISJOINT_5D

    stats, samples_by_depth = explore(depth=args.depth, variant=variant)

    print("Morpion state counting")
    print(f"variant = {variant}")
    print(f"depth   = {args.depth}")
    print()

    print(
        f"{'depth':>5} | {'generated':>10} | {'unique_raw':>10} | "
        f"{'unique_canonical':>16} | {'reduction':>9}"
    )
    print("-" * 71)

    for row in stats:
        reduction = "n/a"
        if row.unique_raw > 0:
            reduction_ratio = 1.0 - (row.unique_canonical / row.unique_raw)
            reduction = f"{100.0 * reduction_ratio:6.2f}%"
        print(
            f"{row.depth:5d} | {row.generated_successors:10d} | "
            f"{row.unique_raw:10d} | {row.unique_canonical:16d} | "
            f"{reduction:>9}"
        )

    if args.show_samples:
        print()
        print("Sample states:")
        for depth, states in samples_by_depth.items():
            print()
            print(f"=== depth {depth} ===")
            for i, state in enumerate(states):
                print(
                    f"[sample {i}] moves={state.moves} "
                    f"played_moves={len(state.played_moves)} "
                    f"points={len(state.points)}"
                )
                print(state.pprint())
                print()


if __name__ == "__main__":
    main()
