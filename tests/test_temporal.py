import pytest

from logickit.temporal import (
    Always,
    Atom,
    Eventually,
    Lasso,
    Next,
    TransitionSystem,
    Until,
    check,
    holds,
    parse_ltl,
)


@pytest.fixture
def traffic():
    """A light that cycles red, red-amber, green, amber, and back."""
    return TransitionSystem(
        initial="red",
        transitions={
            "red": ["red_amber"],
            "red_amber": ["green"],
            "green": ["amber"],
            "amber": ["red"],
        },
        labels={
            "red": ["stop"],
            "red_amber": ["stop", "changing"],
            "green": ["go"],
            "amber": ["changing"],
        },
    )


def test_a_deadlocked_state_is_rejected():
    with pytest.raises(ValueError, match="no outgoing transition"):
        TransitionSystem("a", {"a": ["b"], "b": []}, {"a": [], "b": []})


def test_a_transition_leaving_the_system_is_rejected():
    with pytest.raises(ValueError, match="leaves the system"):
        TransitionSystem("a", {"a": ["ghost"]}, {"a": []})


def test_a_lasso_repeats_its_cycle_forever(traffic):
    run = Lasso((), ("red", "red_amber", "green", "amber"))
    assert run.state_at(0) == "red"
    assert run.state_at(4) == "red"
    assert run.state_at(6) == "green"


def test_next_looks_one_step_ahead(traffic):
    run = Lasso((), ("red", "red_amber", "green", "amber"))
    assert holds(traffic, run, Next(Atom("changing")))
    assert not holds(traffic, run, Next(Atom("go")))


def test_always_must_hold_at_every_position(traffic):
    run = Lasso((), ("red", "red_amber", "green", "amber"))
    assert not holds(traffic, run, Always(Atom("stop")))
    assert holds(traffic, run, Always(parse_ltl("stop | go | changing")))


def test_eventually_finds_a_state_inside_the_cycle(traffic):
    run = Lasso((), ("red", "red_amber", "green", "amber"))
    assert holds(traffic, run, Eventually(Atom("go")))


def test_until_requires_the_left_side_up_to_the_right(traffic):
    run = Lasso((), ("red", "red_amber", "green", "amber"))
    # stop holds at red and red_amber, and go arrives at green.
    assert holds(traffic, run, Until(Atom("stop"), Atom("go")))
    # changing arrives at red_amber, but go does not hold at red before it.
    assert not holds(traffic, run, Until(Atom("go"), Atom("changing")))


def test_until_is_satisfied_immediately_when_the_right_side_already_holds(traffic):
    run = Lasso((), ("red", "red_amber", "green", "amber"))
    # stop holds at position 0, so anything U stop is true there, even though
    # go never holds at red. This is the reading of U that catches people out.
    assert holds(traffic, run, Until(Atom("go"), Atom("stop")))


def test_the_light_always_eventually_turns_green(traffic):
    assert check(traffic, parse_ltl("G F go"))


def test_green_is_always_followed_by_amber(traffic):
    assert check(traffic, parse_ltl("G (go -> X changing)"))


def test_a_plausible_specification_that_is_actually_false(traffic):
    # "a stop state is never immediately followed by go" sounds like the
    # safety property you want, but red_amber is a stop state and green
    # follows it, so the model checker returns the cycle as a counterexample.
    result = check(traffic, parse_ltl("G (stop -> !X go)"))
    assert not result.satisfied
    assert result.counterexample is not None


def test_a_false_property_returns_a_run_that_breaks_it(traffic):
    result = check(traffic, parse_ltl("G stop"))
    assert not result.satisfied
    assert result.counterexample is not None
    assert "green" in str(result.counterexample)


@pytest.fixture
def mutex():
    """Two processes that may both wait, but never share the critical section."""
    return TransitionSystem(
        initial="idle",
        transitions={
            "idle": ["wait_a", "wait_b"],
            "wait_a": ["crit_a", "wait_both"],
            "wait_b": ["crit_b", "wait_both"],
            "wait_both": ["crit_a", "crit_b"],
            "crit_a": ["idle"],
            "crit_b": ["idle"],
        },
        labels={
            "idle": [],
            "wait_a": ["waiting"],
            "wait_b": ["waiting"],
            "wait_both": ["waiting"],
            "crit_a": ["critical", "a"],
            "crit_b": ["critical", "b"],
        },
    )


def test_mutual_exclusion_holds(mutex):
    # No state is labelled with both processes in the critical section.
    assert check(mutex, parse_ltl("G !(a & b)"))


def test_entering_the_critical_section_requires_waiting_first(mutex):
    assert check(mutex, parse_ltl("!critical U critical"))


def test_progress_fails_because_one_process_can_be_starved(mutex):
    # "process a always eventually runs" is false: the system can loop through
    # b forever, and the counterexample is that loop.
    result = check(mutex, parse_ltl("G F a"))
    assert not result.satisfied
    assert "crit_b" in str(result.counterexample)


def test_parsing_covers_the_operators():
    assert str(parse_ltl("G (p -> F q)")) == "G((!(p) | F(q)))"


@pytest.mark.parametrize("text", ["", "G", "(p", "p &", "p @ q"])
def test_malformed_ltl_is_rejected(text):
    with pytest.raises(ValueError):
        parse_ltl(text)
