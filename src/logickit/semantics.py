"""Truth tables, validity, satisfiability, entailment, and counter-models.

The distinction the course kept coming back to, and the one this module makes
concrete: proving something is valid needs a *derivation*, but showing it is
not valid needs a single *counter-model*. Only the second is what a program
hands back here, and it is the more useful of the two when you are wrong.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Iterator, Sequence

from .formula import AND, IFF, IMPLIES, OR, Binary, Const, Formula, Not, Var, variables

Assignment = dict[str, bool]


class EvaluationError(ValueError):
    """Raised when a formula mentions a variable the assignment does not give."""


def evaluate(node: Formula, assignment: Assignment) -> bool:
    if isinstance(node, Const):
        return node.value
    if isinstance(node, Var):
        try:
            return assignment[node.name]
        except KeyError:
            raise EvaluationError(f"no truth value given for {node.name!r}") from None
    if isinstance(node, Not):
        return not evaluate(node.inner, assignment)

    left = evaluate(node.left, assignment)
    right = evaluate(node.right, assignment)
    if node.op == AND:
        return left and right
    if node.op == OR:
        return left or right
    if node.op == IMPLIES:
        # The one every beginner argues with: false implies anything.
        return (not left) or right
    if node.op == IFF:
        return left == right
    raise EvaluationError(f"unknown connective {node.op!r}")


def assignments(names: Sequence[str]) -> Iterator[Assignment]:
    """Every assignment over ``names``, in the order a truth table prints."""
    ordered = list(names)
    for values in itertools.product([False, True], repeat=len(ordered)):
        yield dict(zip(ordered, values))


def signature(*formulas: Formula) -> list[str]:
    names: set = set()
    for formula in formulas:
        names |= variables(formula)
    return sorted(names)


def truth_table(formula: Formula) -> tuple[list[str], list[tuple[Assignment, bool]]]:
    names = signature(formula)
    return names, [(row, evaluate(formula, row)) for row in assignments(names)]


def is_tautology(formula: Formula) -> bool:
    return counter_model(formula) is None


def is_satisfiable(formula: Formula) -> bool:
    return model(formula) is not None


def is_contradiction(formula: Formula) -> bool:
    return not is_satisfiable(formula)


def model(formula: Formula) -> Assignment | None:
    """An assignment making ``formula`` true, or None if there is none."""
    for row in assignments(signature(formula)):
        if evaluate(formula, row):
            return row
    return None


def counter_model(formula: Formula) -> Assignment | None:
    """An assignment making ``formula`` false, or None if it is a tautology."""
    for row in assignments(signature(formula)):
        if not evaluate(formula, row):
            return row
    return None


def entails(premises: Iterable[Formula], conclusion: Formula) -> bool:
    """Semantic entailment: every model of all the premises models the conclusion."""
    return entailment_counter_model(premises, conclusion) is None


def entailment_counter_model(premises: Iterable[Formula], conclusion: Formula) -> Assignment | None:
    """The assignment that refutes the entailment, if there is one.

    This is the thing worth having. "Not valid" is an answer you cannot act
    on; a row of the truth table where the premises hold and the conclusion
    fails tells you exactly which case your reasoning missed.
    """
    premise_list = list(premises)
    for row in assignments(signature(*premise_list, conclusion)):
        if all(evaluate(premise, row) for premise in premise_list) and not evaluate(
            conclusion, row
        ):
            return row
    return None


def equivalent(left: Formula, right: Formula) -> bool:
    return is_tautology(Binary(IFF, left, right))


def format_assignment(assignment: Assignment) -> str:
    if not assignment:
        return "(no variables)"
    return ", ".join(
        f"{name}={'T' if value else 'F'}" for name, value in sorted(assignment.items())
    )


def render_truth_table(formula: Formula) -> str:
    names, rows = truth_table(formula)
    heading = [*list(names), str(formula)]
    widths = [max(len(column), 5) for column in heading]
    lines = ["  ".join(column.ljust(width) for column, width in zip(heading, widths))]
    lines.append("  ".join("-" * width for width in widths))
    for assignment, value in rows:
        cells = [("T" if assignment[name] else "F") for name in names]
        cells.append("T" if value else "F")
        lines.append("  ".join(cell.ljust(width) for cell, width in zip(cells, widths)))
    return "\n".join(lines)
