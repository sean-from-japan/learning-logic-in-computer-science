import pytest

from logickit.formula import parse
from logickit.semantics import (
    EvaluationError,
    counter_model,
    entailment_counter_model,
    entails,
    equivalent,
    evaluate,
    is_contradiction,
    is_satisfiable,
    is_tautology,
    render_truth_table,
)


def test_implication_is_true_when_the_antecedent_is_false():
    assert evaluate(parse("p -> q"), {"p": False, "q": False})


def test_a_missing_variable_is_an_error_not_a_default():
    with pytest.raises(EvaluationError, match="q"):
        evaluate(parse("p & q"), {"p": True})


@pytest.mark.parametrize(
    "text",
    [
        "p | ~p",  # excluded middle
        "~(p & ~p)",  # non-contradiction
        "(p -> q) <-> (~q -> ~p)",  # contraposition
        "~(p & q) <-> (~p | ~q)",  # De Morgan
        "((p -> q) & p) -> q",  # modus ponens
        "((p -> q) & ~q) -> ~p",  # modus tollens
        "(p -> q) | (q -> p)",  # one of the two always holds
    ],
)
def test_known_tautologies(text):
    assert is_tautology(parse(text)), render_truth_table(parse(text))


@pytest.mark.parametrize("text", ["p & ~p", "(p -> q) & p & ~q"])
def test_known_contradictions(text):
    assert is_contradiction(parse(text))


def test_affirming_the_consequent_is_not_valid_and_the_counter_model_shows_why():
    formula = parse("((p -> q) & q) -> p")
    assert not is_tautology(formula)
    witness = counter_model(formula)
    assert witness == {"p": False, "q": True}


def test_entailment_holds_for_modus_ponens():
    assert entails([parse("p -> q"), parse("p")], parse("q"))


def test_entailment_failure_returns_the_row_that_breaks_it():
    witness = entailment_counter_model([parse("p -> q"), parse("q")], parse("p"))
    assert witness == {"p": False, "q": True}


def test_a_contradiction_entails_anything():
    assert entails([parse("p"), parse("~p")], parse("q"))


def test_no_premises_means_validity():
    assert entails([], parse("p | ~p"))
    assert not entails([], parse("p"))


def test_equivalence_of_the_two_forms_of_implication():
    assert equivalent(parse("p -> q"), parse("~p | q"))


def test_satisfiable_but_not_valid():
    formula = parse("p & q")
    assert is_satisfiable(formula)
    assert not is_tautology(formula)


def test_truth_table_has_a_row_per_assignment():
    table = render_truth_table(parse("p & q"))
    assert len(table.splitlines()) == 2 + 4
