import pytest

from logickit.formula import parse
from logickit.normal_forms import negate, render_clauses, to_clauses, to_nnf
from logickit.semantics import assignments, equivalent, evaluate, signature


def clause_value(clauses, assignment):
    """Evaluate a clause set directly, to check it against the formula."""
    for clause in clauses:
        satisfied = False
        for literal in clause:
            name = literal.lstrip("-")
            value = assignment[name]
            if literal.startswith("-"):
                value = not value
            satisfied = satisfied or value
        if not satisfied:
            return False
    return True


FORMULAS = [
    "p",
    "~p",
    "p & q",
    "p | q",
    "p -> q",
    "p <-> q",
    "~(p & q)",
    "~(p | q)",
    "~~p",
    "~(p -> q)",
    "(p -> q) -> r",
    "~((p | q) & (r -> s))",
    "(p <-> q) <-> r",
    "p & (q | (r & ~s))",
]


@pytest.mark.parametrize("text", FORMULAS)
def test_nnf_preserves_meaning(text):
    formula = parse(text)
    assert equivalent(formula, to_nnf(formula))


@pytest.mark.parametrize("text", FORMULAS)
def test_nnf_leaves_negations_only_on_variables(text):
    from logickit.formula import Not, Var, walk

    for node in walk(to_nnf(parse(text))):
        if isinstance(node, Not):
            assert isinstance(node.inner, Var), f"{node} in {text}"


@pytest.mark.parametrize("text", FORMULAS)
def test_clauses_agree_with_the_formula_on_every_assignment(text):
    formula = parse(text)
    clauses = to_clauses(formula)
    names = signature(formula)
    for assignment in assignments(names):
        assert clause_value(clauses, assignment) == evaluate(
            formula, assignment
        ), f"{text} -> {render_clauses(clauses)} at {assignment}"


def test_a_tautology_reduces_to_no_clauses():
    assert to_clauses(parse("p | ~p")) == []


def test_a_contradiction_keeps_both_clauses_rather_than_collapsing():
    # (p) & (~p) is unsatisfiable, but CNF conversion does not derive the
    # empty clause: that is resolution's job, not the rewriter's.
    assert to_clauses(parse("p & ~p")) == [frozenset({"p"}), frozenset({"-p"})]


def test_falsum_is_the_empty_clause():
    assert to_clauses(parse("F")) == [frozenset()]


def test_duplicate_clauses_are_removed():
    clauses = to_clauses(parse("(p | q) & (q | p)"))
    assert len(clauses) == 1


def test_a_subsumed_clause_is_dropped():
    # (p) makes (p | q) redundant.
    clauses = to_clauses(parse("p & (p | q)"))
    assert clauses == [frozenset({"p"})]


def test_negate_flips_a_literal_both_ways():
    assert negate("p") == "-p"
    assert negate("-p") == "p"
