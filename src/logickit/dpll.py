"""DPLL, with a trace of the decisions it made.

The reason for writing this rather than reading it: a truth table over 20
variables is a million rows, and DPLL usually never looks at most of them. The
trace is what makes that visible — unit propagation and pure literals do the
work, and branching is the last resort rather than the method.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from .normal_forms import Clause, Literal, negate

Model = dict[str, bool]


@dataclass
class Statistics:
    decisions: int = 0
    unit_propagations: int = 0
    pure_literals: int = 0
    conflicts: int = 0
    trace: list[str] = field(default_factory=list)

    def note(self, depth: int, message: str) -> None:
        self.trace.append("  " * depth + message)


@dataclass
class Solution:
    satisfiable: bool
    model: Model | None
    statistics: Statistics

    def __bool__(self) -> bool:
        return self.satisfiable


def _assign(clauses: Sequence[Clause], literal: Literal) -> list[Clause]:
    """Clauses that remain once ``literal`` is true."""
    opposite = negate(literal)
    remaining: list[Clause] = []
    for clause in clauses:
        if literal in clause:
            continue  # the clause is satisfied
        if opposite in clause:
            remaining.append(clause - {opposite})
        else:
            remaining.append(clause)
    return remaining


def _record(model: Model, literal: Literal) -> Model:
    updated = dict(model)
    updated[literal.lstrip("-")] = not literal.startswith("-")
    return updated


def _unit_literal(clauses: Sequence[Clause]) -> Literal | None:
    for clause in clauses:
        if len(clause) == 1:
            return next(iter(clause))
    return None


def _pure_literal(clauses: Sequence[Clause]) -> Literal | None:
    present: set[Literal] = set()
    for clause in clauses:
        present |= clause
    for literal in sorted(present):
        if negate(literal) not in present:
            return literal
    return None


def _choose(clauses: Sequence[Clause]) -> Literal:
    """Pick a branching literal deterministically, so runs are reproducible."""
    counts: dict[Literal, int] = {}
    for clause in clauses:
        for literal in clause:
            counts[literal] = counts.get(literal, 0) + 1
    return max(sorted(counts), key=lambda literal: counts[literal])


def solve(clauses: Sequence[Clause], variables: Sequence[str] | None = None) -> Solution:
    """Decide satisfiability of a clause set, returning a model when there is one."""
    statistics = Statistics()
    found = _dpll(list(clauses), {}, statistics, 0)
    if found is None:
        return Solution(False, None, statistics)
    if variables:
        # Variables the search never needed can take either value; report one.
        for name in variables:
            found.setdefault(name, False)
    return Solution(True, found, statistics)


def _dpll(clauses: list[Clause], model: Model, statistics: Statistics, depth: int) -> Model | None:
    while True:
        if not clauses:
            statistics.note(depth, "all clauses satisfied")
            return model
        if any(len(clause) == 0 for clause in clauses):
            statistics.conflicts += 1
            statistics.note(depth, "empty clause: conflict")
            return None

        unit = _unit_literal(clauses)
        if unit is not None:
            statistics.unit_propagations += 1
            statistics.note(depth, f"unit propagate {_show(unit)}")
            model = _record(model, unit)
            clauses = _assign(clauses, unit)
            continue

        pure = _pure_literal(clauses)
        if pure is not None:
            statistics.pure_literals += 1
            statistics.note(depth, f"pure literal {_show(pure)}")
            model = _record(model, pure)
            clauses = _assign(clauses, pure)
            continue
        break

    literal = _choose(clauses)
    statistics.decisions += 1
    statistics.note(depth, f"decide {_show(literal)}")
    found = _dpll(_assign(clauses, literal), _record(model, literal), statistics, depth + 1)
    if found is not None:
        return found

    opposite = negate(literal)
    statistics.note(depth, f"backtrack, try {_show(opposite)}")
    return _dpll(_assign(clauses, opposite), _record(model, opposite), statistics, depth + 1)


def _show(literal: Literal) -> str:
    return f"~{literal[1:]}" if literal.startswith("-") else literal
