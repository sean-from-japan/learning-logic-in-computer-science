"""Rewriting to negation normal form and conjunctive normal form.

Conversion to CNF is where the course stopped being about truth tables: it is
a rewriting system whose whole point is to feed a solver. The two properties
that matter are that each step preserves meaning and that the process
terminates, and both are asserted in the tests rather than argued for here.
"""

from __future__ import annotations

from .formula import AND, IFF, IMPLIES, OR, Binary, Const, Formula, Not, Var

#: A clause is a set of literals; a literal is ``name`` or ``-name``.
Literal = str
Clause = frozenset[Literal]


def negate(literal: Literal) -> Literal:
    return literal[1:] if literal.startswith("-") else f"-{literal}"


def eliminate_connectives(node: Formula) -> Formula:
    """Rewrite -> and <-> away, leaving only ~, & and |."""
    if isinstance(node, (Var, Const)):
        return node
    if isinstance(node, Not):
        return Not(eliminate_connectives(node.inner))
    left = eliminate_connectives(node.left)
    right = eliminate_connectives(node.right)
    if node.op == IMPLIES:
        return Binary(OR, Not(left), right)
    if node.op == IFF:
        return Binary(AND, Binary(OR, Not(left), right), Binary(OR, left, Not(right)))
    return Binary(node.op, left, right)


def to_nnf(node: Formula) -> Formula:
    """Push every negation down to the variables."""
    return _push_negations(eliminate_connectives(node))


def _push_negations(node: Formula) -> Formula:
    if isinstance(node, (Var, Const)):
        return node
    if isinstance(node, Binary):
        return Binary(node.op, _push_negations(node.left), _push_negations(node.right))

    inner = node.inner
    if isinstance(inner, Const):
        return Const(not inner.value)
    if isinstance(inner, Var):
        return node
    if isinstance(inner, Not):
        return _push_negations(inner.inner)  # double negation
    flipped = AND if inner.op == OR else OR  # De Morgan
    return Binary(flipped, _push_negations(Not(inner.left)), _push_negations(Not(inner.right)))


def to_clauses(node: Formula) -> list[Clause]:
    """Convert to CNF as a list of clauses, simplified.

    Distribution can blow up exponentially. That is a real property of this
    method rather than a defect of the implementation, and it is why a solver
    that needs scale uses a structure-preserving translation instead. This
    course's version is the honest, exponential one.
    """
    clauses = _distribute(to_nnf(node))
    return _simplify(clauses)


def _distribute(node: Formula) -> list[Clause]:
    if isinstance(node, Const):
        # An empty clause is unsatisfiable; no clauses at all is trivially true.
        return [] if node.value else [frozenset()]
    if isinstance(node, Var):
        return [frozenset({node.name})]
    if isinstance(node, Not):
        assert isinstance(node.inner, Var), "to_nnf leaves negations only on variables"
        return [frozenset({f"-{node.inner.name}"})]
    if node.op == AND:
        return _distribute(node.left) + _distribute(node.right)
    left = _distribute(node.left)
    right = _distribute(node.right)
    return [first | second for first in left for second in right]


def _simplify(clauses: list[Clause]) -> list[Clause]:
    kept: list[Clause] = []
    seen: set[Clause] = set()
    for clause in clauses:
        # A clause holding both p and -p is true under every assignment.
        if any(negate(literal) in clause for literal in clause):
            continue
        if clause in seen:
            continue
        seen.add(clause)
        kept.append(clause)
    # Drop any clause that a smaller one already implies.
    return [clause for clause in kept if not any(other < clause for other in kept)]


def render_clauses(clauses: list[Clause]) -> str:
    if not clauses:
        return "(no clauses: always true)"
    parts = []
    for clause in clauses:
        if not clause:
            parts.append("()")
            continue
        literals = sorted(clause, key=lambda item: (item.lstrip("-"), item.startswith("-")))
        parts.append("(" + " | ".join(_pretty(literal) for literal in literals) + ")")
    return " & ".join(parts)


def _pretty(literal: Literal) -> str:
    return f"~{literal[1:]}" if literal.startswith("-") else literal
