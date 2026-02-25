"""Basic integration tests for Morpion game adapters."""

from atomheart.games.morpion import MorpionDynamics, Variant, initial_state


def test_initial_has_moves() -> None:
    """The standard start position should expose legal moves."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)
    actions = dynamics.legal_actions(state).get_all()
    assert len(actions) > 0


def test_step_increases_moves() -> None:
    """Applying one legal move should increment the move counter."""
    dynamics = MorpionDynamics()
    state = initial_state(variant=Variant.TOUCHING_5T)
    action = dynamics.legal_actions(state).get_all()[0]
    transition = dynamics.step(state, action)
    assert transition.next_state.moves == state.moves + 1
