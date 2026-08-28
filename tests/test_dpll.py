import pytest

from logickit.dpll import solve
from logickit.formula import parse
from logickit.normal_forms import to_clauses
from logickit.semantics import evaluate, is_satisfiable, signature

SATISFIABLE = ["p", "p | q", "(p -> q) & p", "(p | q) & (~p | r) & (~q | ~r)", "p <-> q"]
UNSATISFIABLE = ["p & ~p", "(p | q) & (~p | q) & (p | ~q) & (~p | ~q)", "(p -> q) & p & ~q"]


@pytest.mark.parametrize("text", SATISFIABLE + UNSATISFIABLE)
def test_dpll_agrees_with_the_truth_table(text):
    formula = parse(text)
    assert solve(to_clauses(formula)).satisfiable == is_satisfiable(formula)


@pytest.mark.parametrize("text", SATISFIABLE)
def test_the_model_really_satisfies_the_formula(text):
    formula = parse(text)
    solution = solve(to_clauses(formula), signature(formula))
    assert solution.model is not None
    assert evaluate(formula, solution.model)


@pytest.mark.parametrize("text", UNSATISFIABLE)
def test_no_model_is_returned_for_an_unsatisfiable_formula(text):
    solution = solve(to_clauses(parse(text)))
    assert not solution.satisfiable
    assert solution.model is None


def test_unit_propagation_happens_before_any_branching():
    # (p) forces p, which forces q through (~p | q): no decision is needed.
    solution = solve(to_clauses(parse("p & (~p | q)")))
    assert solution.satisfiable
    assert solution.statistics.decisions == 0
    assert solution.statistics.unit_propagations >= 2


def test_a_pure_literal_is_taken_without_branching():
    # r appears only positively, so it can be set true with no case analysis.
    solution = solve(to_clauses(parse("(p | r) & (q | r)")))
    assert solution.satisfiable
    assert solution.statistics.decisions == 0


def test_dpll_does_not_enumerate_all_assignments():
    text = " & ".join(f"(p{index} | q{index})" for index in range(12))
    solution = solve(to_clauses(parse(text)))
    assert solution.satisfiable
    # A truth table would be 2**24 rows; the search takes a handful of steps.
    assert len(solution.statistics.trace) < 100


def test_the_trace_records_a_conflict_and_a_backtrack():
    solution = solve(to_clauses(parse("(p | q) & (~p | q) & (p | ~q) & (~p | ~q)")))
    assert not solution.satisfiable
    assert solution.statistics.conflicts > 0


def test_variables_the_search_never_touched_still_appear_in_the_model():
    formula = parse("p | (q & ~q)")
    solution = solve(to_clauses(formula), signature(formula))
    assert set(solution.model or {}) == {"p", "q"}
