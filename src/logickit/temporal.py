"""Linear temporal logic over a labelled transition system.

The course's last topic, and the one that answers "what is any of this for":
a program's behaviour is a set of infinite runs, a specification is a formula
those runs must satisfy, and model checking is the search for a run that
breaks it.

The checker here is explicit-state and bounded. It enumerates lasso-shaped
runs — a finite prefix followed by a cycle — up to a bound, and evaluates the
formula exactly on each. That is sound for finding counterexamples and, on a
finite system where the bound covers every reachable lasso, it also answers
the positive case. It is not the automata-theoretic construction a real model
checker uses, and it is not meant to be; see the limitations in the README.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass

# --- syntax ---------------------------------------------------------------


@dataclass(frozen=True)
class Atom:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Bool:
    value: bool

    def __str__(self) -> str:
        return "true" if self.value else "false"


@dataclass(frozen=True)
class Neg:
    inner: Ltl

    def __str__(self) -> str:
        return f"!({self.inner})"


@dataclass(frozen=True)
class And:
    left: Ltl
    right: Ltl

    def __str__(self) -> str:
        return f"({self.left} & {self.right})"


@dataclass(frozen=True)
class Or:
    left: Ltl
    right: Ltl

    def __str__(self) -> str:
        return f"({self.left} | {self.right})"


@dataclass(frozen=True)
class Next:
    inner: Ltl

    def __str__(self) -> str:
        return f"X({self.inner})"


@dataclass(frozen=True)
class Always:
    inner: Ltl

    def __str__(self) -> str:
        return f"G({self.inner})"


@dataclass(frozen=True)
class Eventually:
    inner: Ltl

    def __str__(self) -> str:
        return f"F({self.inner})"


@dataclass(frozen=True)
class Until:
    left: Ltl
    right: Ltl

    def __str__(self) -> str:
        return f"({self.left} U {self.right})"


Ltl = object  # a closed union; the isinstance chain in `holds` is the contract


def implies(left: Ltl, right: Ltl) -> Ltl:
    return Or(Neg(left), right)


# --- runs -----------------------------------------------------------------


@dataclass(frozen=True)
class Lasso:
    """An infinite run written finitely: ``stem`` then ``cycle`` forever."""

    stem: tuple[str, ...]
    cycle: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.cycle:
            raise ValueError("a lasso needs a non-empty cycle")

    def state_at(self, index: int) -> str:
        if index < len(self.stem):
            return self.stem[index]
        offset = (index - len(self.stem)) % len(self.cycle)
        return self.cycle[offset]

    @property
    def period_start(self) -> int:
        return len(self.stem)

    @property
    def period(self) -> int:
        return len(self.cycle)

    def __str__(self) -> str:
        stem = " -> ".join(self.stem)
        cycle = " -> ".join(self.cycle)
        return (f"{stem} -> " if stem else "") + f"({cycle})^w"


# --- transition systems ---------------------------------------------------


class TransitionSystem:
    """States, transitions, and the atoms true in each state."""

    def __init__(
        self,
        initial: str,
        transitions: dict[str, Iterable[str]],
        labels: dict[str, Iterable[str]],
    ) -> None:
        self.transitions: dict[str, tuple[str, ...]] = {
            state: tuple(targets) for state, targets in transitions.items()
        }
        self.labels: dict[str, frozenset[str]] = {
            state: frozenset(atoms) for state, atoms in labels.items()
        }
        if initial not in self.transitions:
            raise ValueError(f"initial state {initial!r} is not in the transition table")
        for state, targets in self.transitions.items():
            if not targets:
                # Deadlock states make "infinite run" meaningless, so they are
                # rejected rather than silently given a self-loop.
                raise ValueError(f"state {state!r} has no outgoing transition")
            for target in targets:
                if target not in self.transitions:
                    raise ValueError(f"transition {state!r} -> {target!r} leaves the system")
        self.initial = initial

    def holds_at(self, state: str, atom: str) -> bool:
        return atom in self.labels.get(state, frozenset())

    def lassos(self, max_length: int = 12) -> Iterator[Lasso]:
        """Every lasso reachable from the initial state, up to a path length."""
        seen: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
        stack: list[list[str]] = [[self.initial]]
        while stack:
            path = stack.pop()
            state = path[-1]
            for target in self.transitions[state]:
                extended = [*path, target]
                if target in path:
                    start = path.index(target)
                    key = (tuple(path[:start]), tuple(path[start:]))
                    if key not in seen:
                        seen.add(key)
                        yield Lasso(key[0], key[1])
                    continue
                if len(extended) <= max_length:
                    stack.append(extended)


# --- semantics ------------------------------------------------------------


def holds(system: TransitionSystem, run: Lasso, formula: Ltl, index: int = 0) -> bool:
    """Does ``formula`` hold at position ``index`` of ``run``?

    Because the run repeats with a known period, every temporal operator only
    has to look at a finite window: positions past the end of one full lap
    around the cycle repeat what has already been seen.
    """
    horizon = run.period_start + run.period

    if isinstance(formula, Bool):
        return formula.value
    if isinstance(formula, Atom):
        return system.holds_at(run.state_at(index), formula.name)
    if isinstance(formula, Neg):
        return not holds(system, run, formula.inner, index)
    if isinstance(formula, And):
        return holds(system, run, formula.left, index) and holds(system, run, formula.right, index)
    if isinstance(formula, Or):
        return holds(system, run, formula.left, index) or holds(system, run, formula.right, index)
    if isinstance(formula, Next):
        return holds(system, run, formula.inner, index + 1)
    if isinstance(formula, Always):
        return all(
            holds(system, run, formula.inner, step) for step in range(index, index + horizon + 1)
        )
    if isinstance(formula, Eventually):
        return any(
            holds(system, run, formula.inner, step) for step in range(index, index + horizon + 1)
        )
    if isinstance(formula, Until):
        for step in range(index, index + horizon + 1):
            if holds(system, run, formula.right, step):
                return all(
                    holds(system, run, formula.left, before) for before in range(index, step)
                )
        return False
    raise TypeError(f"not an LTL formula: {formula!r}")


@dataclass
class CheckResult:
    satisfied: bool
    counterexample: Lasso | None
    runs_examined: int

    def __bool__(self) -> bool:
        return self.satisfied


def check(system: TransitionSystem, formula: Ltl, max_length: int = 12) -> CheckResult:
    """Check that every reachable lasso satisfies ``formula``.

    A failing run is returned, because a counterexample is the useful output:
    "the specification does not hold" is not something you can debug.
    """
    examined = 0
    for run in system.lassos(max_length):
        examined += 1
        if not holds(system, run, formula):
            return CheckResult(False, run, examined)
    return CheckResult(True, None, examined)


def parse_ltl(text: str) -> Ltl:
    """A small parser: atoms, ! & |, ->, and X G F U."""
    return _LtlParser(text).parse()


class _LtlParser:
    def __init__(self, text: str) -> None:
        self.tokens = _tokenize_ltl(text)
        self.index = 0

    def parse(self) -> Ltl:
        node = self.parse_implies()
        if self.index != len(self.tokens):
            raise ValueError(f"unexpected {self.tokens[self.index]!r}")
        return node

    def peek(self) -> str | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def parse_implies(self) -> Ltl:
        node = self.parse_or()
        if self.peek() == "->":
            self.index += 1
            return implies(node, self.parse_implies())
        return node

    def parse_or(self) -> Ltl:
        node = self.parse_and()
        while self.peek() == "|":
            self.index += 1
            node = Or(node, self.parse_and())
        return node

    def parse_and(self) -> Ltl:
        node = self.parse_until()
        while self.peek() == "&":
            self.index += 1
            node = And(node, self.parse_until())
        return node

    def parse_until(self) -> Ltl:
        node = self.parse_unary()
        while self.peek() == "U":
            self.index += 1
            node = Until(node, self.parse_unary())
        return node

    def parse_unary(self) -> Ltl:
        token = self.peek()
        if token is None:
            raise ValueError("unexpected end of formula")
        if token == "!":
            self.index += 1
            return Neg(self.parse_unary())
        if token in ("X", "G", "F"):
            self.index += 1
            inner = self.parse_unary()
            return {"X": Next, "G": Always, "F": Eventually}[token](inner)
        if token == "(":
            self.index += 1
            inner = self.parse_implies()
            if self.peek() != ")":
                raise ValueError("expected )")
            self.index += 1
            return inner
        if token in ("true", "false"):
            self.index += 1
            return Bool(token == "true")
        if not token.isidentifier():
            raise ValueError(f"unexpected {token!r}")
        self.index += 1
        return Atom(token)


def _tokenize_ltl(text: str) -> Sequence[str]:
    tokens: list[str] = []
    position = 0
    while position < len(text):
        char = text[position]
        if char.isspace():
            position += 1
        elif text.startswith("->", position):
            tokens.append("->")
            position += 2
        elif char in "()!&|":
            tokens.append(char)
            position += 1
        elif char.isalnum() or char == "_":
            start = position
            while position < len(text) and (text[position].isalnum() or text[position] == "_"):
                position += 1
            tokens.append(text[start:position])
        else:
            raise ValueError(f"unexpected {char!r} at position {position}")
    return tokens
