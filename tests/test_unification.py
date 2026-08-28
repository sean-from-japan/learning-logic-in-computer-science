import pytest

from logickit.unification import (
    Function,
    TermError,
    Variable,
    apply,
    format_substitution,
    occurs,
    parse_term,
    unify,
)


def term(text):
    return parse_term(text)


def test_a_variable_unifies_with_anything():
    result = unify(term("X"), term("f(a)"))
    assert result.success
    assert str(result.substitution["X"]) == "f(a)"


def test_identical_terms_need_no_substitution():
    assert unify(term("f(a, b)"), term("f(a, b)")).substitution == {}


def test_different_function_symbols_do_not_unify():
    result = unify(term("f(a)"), term("g(a)"))
    assert not result.success
    assert "different function symbols" in (result.reason or "")


def test_different_arities_do_not_unify():
    result = unify(term("f(a)"), term("f(a, b)"))
    assert not result.success
    assert "arguments" in (result.reason or "")


def test_the_occurs_check_stops_an_infinite_term():
    result = unify(term("X"), term("f(X)"))
    assert not result.success
    assert "occurs" in (result.reason or "")


def test_the_occurs_check_looks_through_the_substitution():
    # X = Y then Y = f(X): the cycle is only visible after substituting.
    result = unify(term("g(X, Y)"), term("g(Y, f(X))"))
    assert not result.success


def test_variables_are_bound_transitively():
    result = unify(term("f(X, b)"), term("f(a, Y)"))
    assert result.success
    assert str(apply(result.substitution, term("h(X, Y)"))) == "h(a, b)"


def test_the_unifier_makes_both_sides_equal():
    left, right = term("f(X, g(Y))"), term("f(a, g(b))")
    result = unify(left, right)
    assert apply(result.substitution, left) == apply(result.substitution, right)


def test_the_unifier_is_most_general():
    # Unifying f(X) with f(Y) must not commit either variable to a constant.
    result = unify(term("f(X)"), term("f(Y)"))
    assert result.success
    assert all(isinstance(value, Variable) for value in result.substitution.values())


def test_nested_structures_unify_pairwise():
    result = unify(term("p(f(X), Y, Z)"), term("p(f(a), g(Z), b)"))
    assert result.success
    assert str(apply(result.substitution, term("Y"))) == "g(b)"


def test_names_beginning_with_a_capital_are_variables():
    assert isinstance(term("X"), Variable)
    assert isinstance(term("alice"), Function)
    assert term("f(X)") == Function("f", (Variable("X"),))


def test_occurs_is_false_for_an_unrelated_variable():
    assert not occurs("X", term("f(Y)"), {})


@pytest.mark.parametrize("text", ["", "f(", "f(a", ")", "f(a,)", "f a"])
def test_malformed_terms_are_rejected(text):
    with pytest.raises(TermError):
        parse_term(text)


def test_substitutions_print_readably():
    result = unify(term("f(X, b)"), term("f(a, Y)"))
    assert format_substitution(result.substitution) == "{X := a, Y := b}"
