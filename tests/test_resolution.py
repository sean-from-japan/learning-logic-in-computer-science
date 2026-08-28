import pytest

from logickit.formula import parse
from logickit.normal_forms import to_clauses
from logickit.resolution import refute, resolve
from logickit.semantics import is_satisfiable


def test_resolving_complementary_unit_clauses_gives_the_empty_clause():
    results = resolve(frozenset({"p"}), frozenset({"-p"}))
    assert results == [("p", frozenset())]


def test_resolution_removes_exactly_one_complementary_pair():
    results = resolve(frozenset({"p", "q"}), frozenset({"-p", "r"}))
    assert results == [("p", frozenset({"q", "r"}))]


def test_a_tautological_resolvent_is_discarded():
    # Resolving on p leaves q and -q together, which is useless.
    assert resolve(frozenset({"p", "q"}), frozenset({"-p", "-q"})) == []


@pytest.mark.parametrize(
    "text",
    ["p & ~p", "(p -> q) & p & ~q", "(p | q) & (~p | q) & (p | ~q) & (~p | ~q)"],
)
def test_unsatisfiable_formulas_are_refuted(text):
    result = refute(to_clauses(parse(text)))
    assert result.found
    assert result.steps[-1].result == frozenset()


@pytest.mark.parametrize("text", ["p | q", "(p -> q) & p", "p"])
def test_satisfiable_formulas_are_not_refuted(text):
    assert is_satisfiable(parse(text))
    assert not refute(to_clauses(parse(text))).found


def test_entailment_is_proved_by_refuting_the_negated_goal():
    # p -> q, p |= q  becomes  refute((~p|q) & p & ~q)
    premises = to_clauses(parse("(p -> q) & p"))
    negated_goal = to_clauses(parse("~q"))
    assert refute(premises + negated_goal).found


def test_every_step_of_a_refutation_can_be_replayed():
    result = refute(to_clauses(parse("(p -> q) & p & ~q")))
    for step in result.steps:
        resolvents = [resolvent for _, resolvent in resolve(step.left, step.right)]
        assert step.result in resolvents
