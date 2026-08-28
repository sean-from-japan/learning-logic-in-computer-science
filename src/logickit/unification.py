"""First-order terms and the unification algorithm.

Unification is the point where the course's two halves met: it is pure syntax,
and it is the engine underneath resolution for predicate logic, type
inference and every logic programming language. The occurs check is the whole
subtlety, and it is one line that is easy to leave out and impossible to leave
out safely.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Union


class TermError(ValueError):
    """Raised when a term cannot be read."""


@dataclass(frozen=True)
class Variable:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Function:
    name: str
    arguments: tuple[Term, ...] = ()

    def __str__(self) -> str:
        if not self.arguments:
            return self.name
        return f"{self.name}({', '.join(str(argument) for argument in self.arguments)})"


Term = Union[Variable, Function]
Substitution = dict[str, Term]


def apply(substitution: Substitution, term: Term) -> Term:
    """Apply a substitution until nothing changes."""
    if isinstance(term, Variable):
        replacement = substitution.get(term.name)
        return term if replacement is None else apply(substitution, replacement)
    return Function(term.name, tuple(apply(substitution, argument) for argument in term.arguments))


def occurs(name: str, term: Term, substitution: Substitution) -> bool:
    """Does variable ``name`` appear inside ``term``?

    Without this, unifying x with f(x) succeeds and builds an infinite term.
    That is the bug that lets an unsound "proof" through, and several logic
    programming systems omit the check on purpose, for speed.
    """
    resolved = apply(substitution, term)
    if isinstance(resolved, Variable):
        return resolved.name == name
    return any(occurs(name, argument, substitution) for argument in resolved.arguments)


@dataclass
class UnificationResult:
    success: bool
    substitution: Substitution
    reason: str | None = None

    def __bool__(self) -> bool:
        return self.success


def unify(left: Term, right: Term) -> UnificationResult:
    """Compute a most general unifier, or say why there is none."""
    substitution: Substitution = {}
    pending: list[tuple[Term, Term]] = [(left, right)]

    while pending:
        first, second = pending.pop(0)
        first = apply(substitution, first)
        second = apply(substitution, second)

        if first == second:
            continue

        if isinstance(first, Variable):
            if occurs(first.name, second, substitution):
                return UnificationResult(
                    False, {}, f"{first.name} occurs in {second}, so no finite term unifies them"
                )
            substitution[first.name] = second
            continue

        if isinstance(second, Variable):
            pending.insert(0, (second, first))
            continue

        if first.name != second.name:
            return UnificationResult(
                False, {}, f"different function symbols: {first.name} and {second.name}"
            )
        if len(first.arguments) != len(second.arguments):
            return UnificationResult(
                False,
                {},
                f"{first.name} used with {len(first.arguments)} and {len(second.arguments)} arguments",
            )
        pending = list(zip(first.arguments, second.arguments)) + pending

    resolved = {name: apply(substitution, value) for name, value in substitution.items()}
    return UnificationResult(True, resolved)


_TERM_TOKEN = re.compile(r"\s*(?:(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<punct>[(),])|(?P<bad>\S))")


def parse_term(text: str, variables_are_uppercase: bool = True) -> Term:
    """Read a term. By convention a name starting with a capital is a variable."""
    tokens: list[tuple[str, str]] = []
    position = 0
    while position < len(text):
        match = _TERM_TOKEN.match(text, position)
        if match is None:
            raise TermError(f"cannot read term at position {position}")
        if match.group("bad"):
            raise TermError(f"unexpected {match.group('bad')!r} at position {match.start('bad')}")
        kind = "name" if match.group("name") else "punct"
        tokens.append((kind, match.group(kind)))
        position = match.end()

    if not tokens:
        raise TermError("empty term")

    index = 0

    def parse() -> Term:
        nonlocal index
        if index >= len(tokens) or tokens[index][0] != "name":
            raise TermError("expected a name")
        name = tokens[index][1]
        index += 1
        arguments: list[Term] = []
        if index < len(tokens) and tokens[index][1] == "(":
            index += 1
            while True:
                arguments.append(parse())
                if index >= len(tokens):
                    raise TermError("unclosed bracket")
                if tokens[index][1] == ",":
                    index += 1
                    continue
                if tokens[index][1] == ")":
                    index += 1
                    break
                raise TermError(f"unexpected {tokens[index][1]!r} inside an argument list")
        if not arguments and variables_are_uppercase and name[0].isupper():
            return Variable(name)
        return Function(name, tuple(arguments))

    term = parse()
    if index != len(tokens):
        raise TermError(f"unexpected {tokens[index][1]!r} after the term")
    return term


def format_substitution(substitution: Substitution) -> str:
    if not substitution:
        return "{} (already equal)"
    return (
        "{" + ", ".join(f"{name} := {value}" for name, value in sorted(substitution.items())) + "}"
    )
