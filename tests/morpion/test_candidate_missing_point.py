"""Exact candidate occupancy and rule-engine preservation controls."""

import pytest

from atomheart.games.morpion import dynamics as rules
from atomheart.games.morpion.state import Dir, Point, Variant, initial_state


def _reference_missing_index(
    points: frozenset[Point],
    pts5: tuple[Point, Point, Point, Point, Point],
) -> int | None:
    """Retain the exhaustive predicate as an independent regression oracle."""
    missing = [index for index, point in enumerate(pts5) if point not in points]
    return missing[0] if len(missing) == 1 else None


@pytest.mark.parametrize("origin", [(0, 0), (-13, 7), (10**6, -(10**6))])
@pytest.mark.parametrize("direction", rules.DIRECTIONS)
@pytest.mark.parametrize("mask", range(32))
def test_every_candidate_occupancy(origin: Point, direction: Dir, mask: int) -> None:
    """Cover zero through five misses, including a single miss at index zero."""
    line = rules._line_points(*origin, direction)
    points = frozenset(point for index, point in enumerate(line) if mask >> index & 1)
    absent = [index for index in range(5) if not mask >> index & 1]
    expected = absent[0] if len(absent) == 1 else None

    assert rules._missing_index_for_candidate(points, line) == expected
    # Points outside this line must not affect its eligibility.
    assert (
        rules._missing_index_for_candidate(points | {(10**9, 10**9)}, line) == expected
    )


def test_changed_occupancy_is_recomputed() -> None:
    """The same line must reflect each supplied immutable point set."""
    line = rules._line_points(0, 0, (1, 0))
    for points, expected in [
        (frozenset(line[1:]), 0),
        (frozenset(line[2:]), None),
        (frozenset(line), None),
        (frozenset(line[:-1]), 4),
        (frozenset(), None),
    ]:
        assert rules._missing_index_for_candidate(points, line) == expected


@pytest.mark.parametrize("variant", list(Variant))
def test_complete_actions_and_successors_match_reference(
    variant: Variant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve ordered actions, orbits, terminality and every legal transition."""
    dynamics = rules.MorpionDynamics()
    state = initial_state(variant)
    for _ in range(40):
        raw = dynamics.all_legal_actions(state)
        unique = dynamics.unique_legal_actions(state)
        generated = dynamics.legal_actions(state).get_all()
        orbits = dynamics.legal_action_orbits(state)
        terminal = dynamics.is_terminal_state(state)
        successors = [dynamics.step(state, action) for action in raw]

        with monkeypatch.context() as reference:
            reference.setattr(
                rules, "_missing_index_for_candidate", _reference_missing_index
            )
            assert dynamics.all_legal_actions(state) == raw
            assert dynamics.unique_legal_actions(state) == unique
            assert dynamics.legal_actions(state).get_all() == generated
            assert dynamics.legal_action_orbits(state) == orbits
            assert dynamics.is_terminal_state(state) == terminal
            assert [dynamics.step(state, action) for action in raw] == successors

        assert terminal == (not raw)
        if terminal:
            break
        state = successors[0].next_state
    else:
        pytest.fail("Deterministic control must reach terminality within 40 states")
