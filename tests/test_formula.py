import pytest

from logickit.formula import (
    AND,
    IMPLIES,
    OR,
    Binary,
    Not,
    ParseError,
    Var,
    parse,
    size,
    variables,
)


def test_precedence_binds_and_tighter_than_or():
    assert parse("p & q | r") == Binary(OR, Binary(AND, Var("p"), Var("q")), Var("r"))


def test_precedence_binds_or_tighter_than_implication():
    assert parse("p | q -> r") == Binary(IMPLIES, Binary(OR, Var("p"), Var("q")), Var("r"))


def test_implication_is_right_associative():
    # p -> (q -> r), not (p -> q) -> r; the two are not equivalent.
    assert parse("p -> q -> r") == Binary(IMPLIES, Var("p"), Binary(IMPLIES, Var("q"), Var("r")))


def test_negation_binds_tightest():
    assert parse("~p & q") == Binary(AND, Not(Var("p")), Var("q"))


def test_brackets_override_precedence():
    assert parse("~(p & q)") == Not(Binary(AND, Var("p"), Var("q")))


@pytest.mark.parametrize(
    "text",
    ["p -> q", "p => q", "p → q"],
)
def test_ascii_and_unicode_notations_agree(text):
    assert parse(text) == parse("p -> q")


@pytest.mark.parametrize("text", ["p & q", "p /\\ q", "p ∧ q", "p && q"])
def test_conjunction_spellings_agree(text):
    assert parse(text) == parse("p & q")


@pytest.mark.parametrize("text", ["p | q", "p \\/ q", "p ∨ q", "p || q"])
def test_disjunction_spellings_agree(text):
    assert parse(text) == parse("p | q")


def test_printing_round_trips_through_the_parser():
    for text in ["p & q | r", "p -> q -> r", "~(p <-> q) & r", "(p -> q) -> r"]:
        assert parse(str(parse(text))) == parse(text)


def test_printing_keeps_the_brackets_that_matter():
    assert str(parse("(p -> q) -> r")) == "(p -> q) -> r"
    assert str(parse("p -> (q -> r)")) == "p -> q -> r"


def test_variables_are_collected():
    assert variables(parse("p & (q | ~p)")) == {"p", "q"}


def test_size_counts_nodes():
    assert size(parse("p")) == 1
    assert size(parse("~p")) == 2
    assert size(parse("p & q")) == 3


@pytest.mark.parametrize("text", ["", "   ", "p &", "& p", "(p", "p)", "p q", "p # q"])
def test_malformed_input_is_rejected_with_a_position(text):
    with pytest.raises(ParseError):
        parse(text)


def test_the_error_says_where_it_stopped():
    with pytest.raises(ParseError, match="position"):
        parse("p & & q")
