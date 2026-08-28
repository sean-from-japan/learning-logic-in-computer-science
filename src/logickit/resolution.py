"""Propositional resolution as a refutation procedure.

Resolution answers a different question from DPLL even though both decide
satisfiability. DPLL hands back a model; resolution hands back a *derivation
of the empty clause*, which is a proof of unsatisfiability that can be
checked step by step without trusting the program that produced it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .normal_forms import Clause, negate, render_clauses


@dataclass
class Step:
    left: Clause
    right: Clause
    on: str
    result: Clause

    def __str__(self) -> str:
        return (
            f"{render_clauses([self.left])} + {render_clauses([self.right])} "
            f"on {self.on} => {render_clauses([self.result]) if self.result else '()'}"
        )


@dataclass
class Refutation:
    found: bool
    steps: list[Step]

    def __bool__(self) -> bool:
        return self.found


def resolve(left: Clause, right: Clause) -> list[tuple[str, Clause]]:
    """Every resolvent of two clauses, with the literal each was resolved on.

    A pair can be resolvable on more than one literal, and resolving on two at
    once produces a tautology rather than anything useful, so exactly one
    complementary pair is removed per step.
    """
    results = []
    for literal in sorted(left):
        if negate(literal) in right:
            resolvent = (left - {literal}) | (right - {negate(literal)})
            if not any(negate(other) in resolvent for other in resolvent):
                results.append((literal.lstrip("-"), resolvent))
    return results


def refute(clauses: Sequence[Clause], limit: int = 20000) -> Refutation:
    """Search for the empty clause by saturation.

    Saturation is complete for propositional logic but grows quickly, which
    is the honest reason a SAT solver is a DPLL descendant and not this.
    """
    known: set[Clause] = set(clauses)
    steps: list[Step] = []
    if frozenset() in known:
        return Refutation(True, steps)

    frontier = list(known)
    generated = 0
    while frontier:
        current = frontier.pop(0)
        for other in list(known):
            for name, resolvent in resolve(current, other):
                generated += 1
                if generated > limit:
                    return Refutation(False, steps)
                if resolvent in known:
                    continue
                steps.append(Step(current, other, name, resolvent))
                if not resolvent:
                    return Refutation(True, steps)
                known.add(resolvent)
                frontier.append(resolvent)
    return Refutation(False, steps)


def entails(premises: Sequence[Clause], goal_clauses: Sequence[Clause]) -> Refutation | None:
    """Prove entailment by refuting the premises together with the negated goal."""
    refutation = refute(list(premises) + list(goal_clauses))
    return refutation if refutation.found else None
