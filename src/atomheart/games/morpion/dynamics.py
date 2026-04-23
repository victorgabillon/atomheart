"""Valanga dynamics adapter for Morpion Solitaire (5T / 5D)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import valanga

from .canonical import (
    Move,
    apply_rooted_symmetry,
    rooted_move_set_symmetry_stabilizer,
)
from .state import Dir, MorpionState, Point, Segment, Variant, norm_seg

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

DIRECTIONS: tuple[Dir, ...] = (
    (1, 0),
    (0, 1),
    (1, 1),
    (1, -1),
)

Action = tuple[int, int, int, int]


class MorpionIllegalActionError(ValueError):
    """Raised when an action violates Morpion rules."""

    @classmethod
    def missing_point_already_present(cls) -> MorpionIllegalActionError:
        """Create error for adding an already occupied missing point."""
        return cls("Illegal action: missing point already present.")

    @classmethod
    def line_missing_more_than_one_point(cls) -> MorpionIllegalActionError:
        """Create error for a line missing more than one required point."""
        return cls("Illegal action: line missing more than one point.")

    @classmethod
    def overlaps_existing_segment(cls) -> MorpionIllegalActionError:
        """Create error for segment overlap with an existing line."""
        return cls("Illegal action: overlaps existing segment.")

    @classmethod
    def violates_same_direction_rule(cls) -> MorpionIllegalActionError:
        """Create error for same-direction incompatibility under variant rules."""
        return cls("Illegal action: violates 5T/5D same-direction rule.")

    @classmethod
    def action_out_of_range(cls) -> MorpionIllegalActionError:
        """Create error for action index values outside valid bounds."""
        return cls("Morpion action out of range.")


class MorpionActionNameError(ValueError):
    """Raised when parsing a textual action representation fails."""

    def __init__(self, name: str) -> None:
        """Build parse error with original action name."""
        super().__init__(f"Bad action name: {name!r}")


class MorpionActionTypeError(TypeError):
    """Raised when action key is not a valid Morpion action tuple."""

    def __init__(self) -> None:
        """Build tuple-shape validation error."""
        super().__init__(
            "Morpion actions must be 4-tuples: (dir_index, x0, y0, missing_i)."
        )


class MorpionActionReconstructionError(ValueError):
    """Raised when transformed Morpion points cannot be re-normalized as an action."""

    @classmethod
    def expected_distinct_points(cls) -> MorpionActionReconstructionError:
        """Create error for malformed five-point action reconstructions."""
        return cls("Morpion action reconstruction expects five distinct points.")

    @classmethod
    def could_not_normalize(
        cls,
        points5: tuple[Point, Point, Point, Point, Point],
    ) -> MorpionActionReconstructionError:
        """Create error for unrecognized five-point configurations."""
        return cls(f"Could not normalize Morpion action points: {points5!r}")


class MorpionPlayedMoveError(ValueError):
    """Raised when a played-line endpoint move is invalid or not replayable."""

    @classmethod
    def must_span_four_steps(cls, move: Move) -> MorpionPlayedMoveError:
        """Create error for moves that do not span four unit steps."""
        return cls(f"Morpion move must span four unit steps: {move!r}")

    @classmethod
    def unsupported_direction(cls, move: Move) -> MorpionPlayedMoveError:
        """Create error for moves with a non-Morpion direction."""
        return cls(f"Unsupported Morpion move direction: {move!r}")

    @classmethod
    def not_replayable_in_state(cls, move: Move) -> MorpionPlayedMoveError:
        """Create error for moves that do not fit the provided state."""
        return cls(f"Morpion move is not replayable from this state: {move!r}")


def _as_action(action: valanga.BranchKey) -> Action:
    """Validate and cast a generic branch key to Morpion ``Action``."""
    if not isinstance(action, tuple):
        raise MorpionActionTypeError
    action_tuple = cast("tuple[object, ...]", action)
    if len(action_tuple) != 4:
        raise MorpionActionTypeError

    normalized = cast("Action", action_tuple)
    dir_index, _, _, missing_i = normalized
    if dir_index not in range(4) or missing_i not in range(5):
        raise MorpionIllegalActionError.action_out_of_range()
    return normalized


class _ListBranchKeyGen(valanga.BranchKeyGeneratorP[valanga.BranchKey]):
    """Small resettable in-memory branch-key generator."""

    sort_branch_keys: bool = False

    def __init__(
        self,
        keys: Sequence[valanga.BranchKey],
        *,
        sort_branch_keys: bool = False,
    ) -> None:
        """Store keys for deterministic iteration."""
        self.sort_branch_keys = sort_branch_keys
        self._keys: list[valanga.BranchKey]
        if self.sort_branch_keys:
            self._keys = sorted(keys, key=repr)
        else:
            self._keys = list(keys)
        self._i = 0

    @property
    def all_generated_keys(self) -> Sequence[valanga.BranchKey] | None:
        """Return all keys already generated by this instance."""
        return self._keys

    def __iter__(self) -> Iterator[valanga.BranchKey]:
        """Return iterator protocol self."""
        return self

    def __next__(self) -> valanga.BranchKey:
        """Return next key or raise ``StopIteration``."""
        if self._i >= len(self._keys):
            raise StopIteration
        key = self._keys[self._i]
        self._i += 1
        return key

    def more_than_one(self) -> bool:
        """Return whether more than one branch key exists."""
        return len(self._keys) > 1

    def get_all(self) -> Sequence[valanga.BranchKey]:
        """Return all branch keys as a new list."""
        return list(self._keys)

    def copy_with_reset(self) -> _ListBranchKeyGen:
        """Return a fresh generator reset at position zero."""
        return _ListBranchKeyGen(self._keys, sort_branch_keys=self.sort_branch_keys)


def _line_points(
    x0: int, y0: int, direction: Dir
) -> tuple[Point, Point, Point, Point, Point]:
    """Return the five points on the candidate line."""
    dx, dy = direction
    return (
        (x0 + 0 * dx, y0 + 0 * dy),
        (x0 + 1 * dx, y0 + 1 * dy),
        (x0 + 2 * dx, y0 + 2 * dy),
        (x0 + 3 * dx, y0 + 3 * dy),
        (x0 + 4 * dx, y0 + 4 * dy),
    )


def _unit_segments_on_line(
    pts5: tuple[Point, Point, Point, Point, Point],
) -> tuple[Segment, Segment, Segment, Segment]:
    """Return the four unit segments composing a five-point line."""
    return (
        norm_seg(pts5[0], pts5[1]),
        norm_seg(pts5[1], pts5[2]),
        norm_seg(pts5[2], pts5[3]),
        norm_seg(pts5[3], pts5[4]),
    )


def _played_move_points(move: Move) -> tuple[Point, Point, Point, Point, Point]:
    """Expand one played-line endpoint move into its five lattice points."""
    x1, y1, x2, y2 = move
    dx = x2 - x1
    dy = y2 - y1
    if dx % 4 != 0 or dy % 4 != 0:
        raise MorpionPlayedMoveError.must_span_four_steps(move)

    direction = (dx // 4, dy // 4)
    if direction not in DIRECTIONS:
        raise MorpionPlayedMoveError.unsupported_direction(move)

    return (
        (x1, y1),
        (x1 + direction[0], y1 + direction[1]),
        (x1 + 2 * direction[0], y1 + 2 * direction[1]),
        (x1 + 3 * direction[0], y1 + 3 * direction[1]),
        (x2, y2),
    )


def action_to_played_move(action: valanga.BranchKey) -> Move:
    """Convert one Morpion action to its played-line endpoint representation."""
    dir_index, x0, y0, _ = _as_action(action)
    pts5 = _line_points(x0, y0, DIRECTIONS[dir_index])
    start = pts5[0]
    end = pts5[4]
    if start <= end:
        return (start[0], start[1], end[0], end[1])
    return (end[0], end[1], start[0], start[1])


def played_move_to_action(state: MorpionState, move: Move) -> Action:
    """Convert one played-line endpoint move into the legal action from ``state``."""
    points = _played_move_points(move)
    missing_indexes = [
        index for index, point in enumerate(points) if point not in state.points
    ]
    if len(missing_indexes) != 1:
        raise MorpionPlayedMoveError.not_replayable_in_state(move)

    direction = (
        points[1][0] - points[0][0],
        points[1][1] - points[0][1],
    )
    return (
        DIRECTIONS.index(direction),
        points[0][0],
        points[0][1],
        missing_indexes[0],
    )


def _points5_to_action(
    points5: tuple[Point, Point, Point, Point, Point],
    missing_point: Point,
) -> Action:
    """Normalize five collinear points back into the canonical action tuple."""
    point_set = frozenset(points5)
    if len(point_set) != 5 or missing_point not in point_set:
        raise MorpionActionReconstructionError.expected_distinct_points()

    start = min(point_set)
    for dir_index, direction in enumerate(DIRECTIONS):
        candidate = _line_points(start[0], start[1], direction)
        if frozenset(candidate) != point_set:
            continue
        return (dir_index, start[0], start[1], candidate.index(missing_point))
    raise MorpionActionReconstructionError.could_not_normalize(points5)


def transform_action_rooted(action: Action, sym: int) -> Action:
    """Transform one Morpion action by a rooted symmetry and renormalize it."""
    dir_index, x0, y0, missing_i = _as_action(action)
    points5 = _line_points(x0, y0, DIRECTIONS[dir_index])
    transformed_points5 = (
        apply_rooted_symmetry(points5[0], sym),
        apply_rooted_symmetry(points5[1], sym),
        apply_rooted_symmetry(points5[2], sym),
        apply_rooted_symmetry(points5[3], sym),
        apply_rooted_symmetry(points5[4], sym),
    )
    transformed_missing_point = transformed_points5[missing_i]
    return _points5_to_action(transformed_points5, transformed_missing_point)


def state_rooted_symmetry_stabilizer(state: MorpionState) -> tuple[int, ...]:
    """Return rooted symmetries that preserve the current Morpion state."""
    if len(state.played_moves) != state.moves:
        # Legacy handcrafted states without a full move history cannot safely be
        # quotiented, so fall back to the identity symmetry only.
        return (0,)
    return rooted_move_set_symmetry_stabilizer(state.played_moves)


def canonical_action_in_state(state: MorpionState, action: valanga.BranchKey) -> Action:
    """Return the canonical representative of one action under the state stabilizer."""
    normalized_action = _as_action(action)
    stabilizer = state_rooted_symmetry_stabilizer(state)
    return min(transform_action_rooted(normalized_action, sym) for sym in stabilizer)


def _point_usage_kind(index: int) -> int:
    """Return usage kind bitmask for line point index."""
    return 1 if index in (0, 4) else 2


def _is_parallel_compat(
    state: MorpionState,
    dir_index: int,
    pts5: tuple[Point, Point, Point, Point, Point],
) -> bool:
    """Return whether same-direction sharing is valid under 5T/5D rules."""
    if state.variant == Variant.DISJOINT_5D:
        return all((p, dir_index) not in state.dir_usage for p in pts5)

    for index, point in enumerate(pts5):
        want = _point_usage_kind(index)
        have = state.dir_usage.get((point, dir_index), 0)
        if have == 0:
            continue
        if have & 2:
            return False
        if have & 1 and want != 1:
            return False
    return True


def _apply_dir_usage(
    state: MorpionState,
    dir_index: int,
    pts5: tuple[Point, Point, Point, Point, Point],
) -> dict[tuple[Point, int], int]:
    """Return updated same-direction point-usage map after adding one line."""
    new_usage = dict(state.dir_usage)
    for index, point in enumerate(pts5):
        kind = _point_usage_kind(index)
        key = (point, dir_index)
        new_usage[key] = new_usage.get(key, 0) | kind
    return new_usage


def _missing_index_for_candidate(
    points: frozenset[Point],
    pts5: tuple[Point, Point, Point, Point, Point],
) -> int | None:
    """Return missing index when exactly one point is absent, else ``None``."""
    missing = [index for index, point in enumerate(pts5) if point not in points]
    if len(missing) != 1:
        return None
    return missing[0]


@dataclass(slots=True)
class MorpionDynamics(valanga.Dynamics[MorpionState]):
    """Rule engine for Morpion transitions."""

    def legal_actions(
        self,
        state: MorpionState,
    ) -> valanga.BranchKeyGeneratorP[valanga.BranchKey]:
        """Return legal action keys for ``state``."""
        actions = self.unique_legal_actions(state)
        return _ListBranchKeyGen(actions, sort_branch_keys=True)

    def all_legal_actions(self, state: MorpionState) -> tuple[Action, ...]:
        """Return the full raw legal-action list for the provided state."""
        return tuple(sorted(self._enumerate_raw_actions(state)))

    def legal_action_orbits(
        self, state: MorpionState
    ) -> tuple[tuple[Action, ...], ...]:
        """Return the raw legal actions partitioned by rooted symmetry orbit."""
        stabilizer = state_rooted_symmetry_stabilizer(state)
        groups: dict[Action, list[Action]] = defaultdict(list)
        for action in self.all_legal_actions(state):
            representative = min(
                transform_action_rooted(action, sym) for sym in stabilizer
            )
            groups[representative].append(action)

        return tuple(
            tuple(sorted(actions))
            for _, actions in sorted(groups.items(), key=lambda item: item[0])
        )

    def unique_legal_actions(self, state: MorpionState) -> tuple[Action, ...]:
        """Return one canonical representative per legal-action orbit."""
        return tuple(representative for representative, _ in self._orbit_items(state))

    def is_terminal_state(self, state: MorpionState) -> bool:
        """Return whether ``state`` has no legal successor."""
        return not any(self._enumerate_raw_actions(state, stop_after_one=True))

    def canonical_action_in_state(
        self,
        state: MorpionState,
        action: valanga.BranchKey,
    ) -> Action:
        """Return the canonical representative for one legal action."""
        return canonical_action_in_state(state, action)

    def state_rooted_symmetry_stabilizer(
        self,
        state: MorpionState,
    ) -> tuple[int, ...]:
        """Expose the rooted stabilizer of the current state."""
        return state_rooted_symmetry_stabilizer(state)

    def step(
        self,
        state: MorpionState,
        action: valanga.BranchKey,
    ) -> valanga.Transition[MorpionState]:
        """Apply a legal move and return transition metadata."""
        dir_index, x0, y0, missing_i = self._as_action(action)
        pts5 = _line_points(x0, y0, DIRECTIONS[dir_index])

        new_point = pts5[missing_i]
        if new_point in state.points:
            raise MorpionIllegalActionError.missing_point_already_present()

        for index, point in enumerate(pts5):
            if index == missing_i:
                continue
            if point not in state.points:
                raise MorpionIllegalActionError.line_missing_more_than_one_point()

        segs = _unit_segments_on_line(pts5)
        if any(seg in state.used_unit_segments for seg in segs):
            raise MorpionIllegalActionError.overlaps_existing_segment()

        if not _is_parallel_compat(state, dir_index, pts5):
            raise MorpionIllegalActionError.violates_same_direction_rule()

        new_points = set(state.points)
        new_points.add(new_point)

        new_segs = set(state.used_unit_segments)
        new_segs.update(segs)

        next_played_moves = set(state.played_moves)
        next_played_moves.add(action_to_played_move(action))

        next_state = MorpionState(
            points=frozenset(new_points),
            used_unit_segments=frozenset(new_segs),
            dir_usage=_apply_dir_usage(state, dir_index, pts5),
            played_moves=frozenset(next_played_moves),
            moves=state.moves + 1,
            variant=state.variant,
        )

        is_over = not any(self._enumerate_raw_actions(next_state, stop_after_one=True))
        return valanga.Transition(
            next_state=next_state,
            modifications=None,
            is_over=is_over,
            over_event=None,
            info={"action": self.action_name(state, action)},
        )

    def action_name(self, state: MorpionState, action: valanga.BranchKey) -> str:
        """Convert an action key to a deterministic text representation."""
        _ = state
        dir_index, x0, y0, missing_i = self._as_action(action)
        dx, dy = DIRECTIONS[dir_index]
        return f"d={dx},{dy}; start=({x0},{y0}); missing={missing_i}"

    def action_from_name(self, state: MorpionState, name: str) -> valanga.BranchKey:
        """Parse action text produced by :meth:`action_name`."""
        _ = state
        parts = [part.strip() for part in name.split(";")]
        if len(parts) != 3:
            raise MorpionActionNameError(name)

        d_part = parts[0].removeprefix("d=").strip()
        start_part = parts[1].removeprefix("start=").strip()
        miss_part = parts[2].removeprefix("missing=").strip()

        dx_s, dy_s = [value.strip() for value in d_part.split(",")]
        dx, dy = int(dx_s), int(dy_s)

        start_part = start_part.removeprefix("(").removesuffix(")")
        x0_s, y0_s = [value.strip() for value in start_part.split(",")]
        x0, y0 = int(x0_s), int(y0_s)

        missing_i = int(miss_part)
        return (DIRECTIONS.index((dx, dy)), x0, y0, missing_i)

    @staticmethod
    def _as_action(action: valanga.BranchKey) -> Action:
        """Validate and cast a generic branch key to Morpion ``Action``."""
        return _as_action(action)

    def _orbit_items(
        self,
        state: MorpionState,
    ) -> tuple[tuple[Action, tuple[Action, ...]], ...]:
        """Return sorted orbit representatives paired with their raw members."""
        orbits = self.legal_action_orbits(state)
        return tuple((orbit[0], orbit) for orbit in orbits)

    def _enumerate_raw_actions(
        self,
        state: MorpionState,
        *,
        stop_after_one: bool = False,
    ) -> Iterable[Action]:
        """Enumerate legal actions by scanning a bounded lattice box."""
        if not state.points:
            return

        xs = [p[0] for p in state.points]
        ys = [p[1] for p in state.points]
        margin = 4
        minx, maxx = min(xs) - margin, max(xs) + margin
        miny, maxy = min(ys) - margin, max(ys) + margin

        for dir_index, direction in enumerate(DIRECTIONS):
            for x0 in range(minx, maxx + 1):
                for y0 in range(miny, maxy + 1):
                    pts5 = _line_points(x0, y0, direction)

                    missing_i = _missing_index_for_candidate(state.points, pts5)
                    if missing_i is None:
                        continue

                    segs = _unit_segments_on_line(pts5)
                    if any(seg in state.used_unit_segments for seg in segs):
                        continue

                    if not _is_parallel_compat(state, dir_index, pts5):
                        continue

                    yield (dir_index, x0, y0, missing_i)
                    if stop_after_one:
                        return

    def _enumerate_actions(
        self,
        state: MorpionState,
        *,
        stop_after_one: bool = False,
    ) -> Iterable[Action]:
        """Compatibility alias for the raw legal-action enumerator."""
        yield from self._enumerate_raw_actions(
            state,
            stop_after_one=stop_after_one,
        )
