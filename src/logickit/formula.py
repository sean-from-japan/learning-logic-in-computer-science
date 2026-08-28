"""Propositional syntax: the abstract tree and a parser for it.

Writing the parser is the part of the course that stopped being abstract. The
grammar below is the precedence table from any logic text, but expressed as a
recursive descent parser it is a program that either accepts a string or says
where it stopped, and there is nowhere left to be vague about what binds
tighter than what.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Union


class ParseError(ValueError):
    """Raised with the position at which a formula stopped making sense."""


@dataclass(frozen=True)
class Var:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Const:
    """Verum and falsum, written T and F."""

    value: bool

    def __str__(self) -> str:
        return "T" if self.value else "F"


@dataclass(frozen=True)
class Not:
    inner: Formula

    def __str__(self) -> str:
        return f"~{_bracket(self.inner, self)}"


@dataclass(frozen=True)
class Binary:
    op: str
    left: Formula
    right: Formula

    def __str__(self) -> str:
        return f"{_bracket(self.left, self)} {self.op} {_bracket(self.right, self)}"


Formula = Union[Var, Const, Not, Binary]

AND = "&"
OR = "|"
IMPLIES = "->"
IFF = "<->"

#: Higher binds tighter. Negation is handled by the parser, not this table.
PRECEDENCE = {IFF: 1, IMPLIES: 2, OR: 3, AND: 4}

TRUE = Const(True)
FALSE = Const(False)


def _precedence(node: Formula) -> int:
    if isinstance(node, Binary):
        return PRECEDENCE[node.op]
    return 100


def _bracket(child: Formula, parent: Formula) -> str:
    """Print the minimum brackets a reader needs, and no more."""
    if _precedence(child) > _precedence(parent):
        return str(child)
    if isinstance(parent, Binary) and isinstance(child, Binary):
        same = PRECEDENCE[child.op] == PRECEDENCE[parent.op]
        # -> is right associative, so a left child of equal precedence needs
        # brackets and a right child does not.
        if same and parent.op == IMPLIES and child is parent.right:
            return str(child)
        if same and parent.op in (AND, OR) and child.op == parent.op:
            return str(child)
    return f"({child})"


def variables(node: Formula) -> frozenset[str]:
    if isinstance(node, Var):
        return frozenset({node.name})
    if isinstance(node, Const):
        return frozenset()
    if isinstance(node, Not):
        return variables(node.inner)
    return variables(node.left) | variables(node.right)


def size(node: Formula) -> int:
    """Number of nodes; used to show that a rewrite really did shrink."""
    if isinstance(node, (Var, Const)):
        return 1
    if isinstance(node, Not):
        return 1 + size(node.inner)
    return 1 + size(node.left) + size(node.right)


_TOKEN = re.compile(
    r"""\s*(?:
        (?P<iff>   <->|<=>|↔|≡ )
      | (?P<imp>   ->|=>|→ )
      | (?P<and>   /\\|&&|&|∧ )
      | (?P<or>    \\/|\|\||\||∨ )
      | (?P<not>   ~|!|¬ )
      | (?P<lpar>  \( )
      | (?P<rpar>  \) )
      | (?P<const> \b(?:T|F|true|false|top|bot)\b )
      | (?P<var>   [A-Za-z][A-Za-z0-9_]* )
      | (?P<bad>   \S )
    )""",
    re.VERBOSE,
)

_CONSTANTS = {"T": True, "true": True, "top": True, "F": False, "false": False, "bot": False}


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    position: int


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        match = _TOKEN.match(text, position)
        if match is None or match.end() == match.start():
            raise ParseError(f"unexpected character at position {position}: {text[position]!r}")
        kind = match.lastgroup or "bad"
        if kind == "bad":
            raise ParseError(
                f"unexpected character at position {match.start('bad')}: {match.group()!r}"
            )
        tokens.append(Token(kind, match.group(kind), match.start(kind)))
        position = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token], text: str) -> None:
        self.tokens = tokens
        self.text = text
        self.index = 0

    def peek(self) -> Token:
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return Token("end", "", len(self.text))

    def take(self) -> Token:
        token = self.peek()
        self.index += 1
        return token

    def expect(self, kind: str) -> Token:
        token = self.peek()
        if token.kind != kind:
            raise ParseError(
                f"expected {kind} at position {token.position}, found {token.text or 'end of input'!r}"
            )
        return self.take()

    # iff is the loosest, and is left associative.
    def parse_iff(self) -> Formula:
        node = self.parse_implies()
        while self.peek().kind == "iff":
            self.take()
            node = Binary(IFF, node, self.parse_implies())
        return node

    # -> is right associative: a -> b -> c means a -> (b -> c).
    def parse_implies(self) -> Formula:
        node = self.parse_or()
        if self.peek().kind == "imp":
            self.take()
            return Binary(IMPLIES, node, self.parse_implies())
        return node

    def parse_or(self) -> Formula:
        node = self.parse_and()
        while self.peek().kind == "or":
            self.take()
            node = Binary(OR, node, self.parse_and())
        return node

    def parse_and(self) -> Formula:
        node = self.parse_unary()
        while self.peek().kind == "and":
            self.take()
            node = Binary(AND, node, self.parse_unary())
        return node

    def parse_unary(self) -> Formula:
        if self.peek().kind == "not":
            self.take()
            return Not(self.parse_unary())
        return self.parse_atom()

    def parse_atom(self) -> Formula:
        token = self.take()
        if token.kind == "lpar":
            inner = self.parse_iff()
            self.expect("rpar")
            return inner
        if token.kind == "const":
            return Const(_CONSTANTS[token.text])
        if token.kind == "var":
            return Var(token.text)
        raise ParseError(
            f"expected a formula at position {token.position}, found {token.text or 'end of input'!r}"
        )


def parse(text: str) -> Formula:
    """Parse one formula. Anything left over is an error, not a silent trim."""
    if not text.strip():
        raise ParseError("empty formula")
    parser = _Parser(tokenize(text), text)
    node = parser.parse_iff()
    remaining = parser.peek()
    if remaining.kind != "end":
        raise ParseError(f"unexpected {remaining.text!r} at position {remaining.position}")
    return node


def walk(node: Formula) -> Iterator[Formula]:
    yield node
    if isinstance(node, Not):
        yield from walk(node.inner)
    elif isinstance(node, Binary):
        yield from walk(node.left)
        yield from walk(node.right)
