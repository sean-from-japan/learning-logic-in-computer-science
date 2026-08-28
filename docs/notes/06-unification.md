# 6. Unification

## The question

Given two terms containing variables, is there a substitution making them
identical?

```
f(X, b)   and   f(a, Y)      ->   {X := a, Y := b}
f(X)      and   g(X)          ->   no: different function symbols
X         and   f(X)          ->   no: the occurs check
```

It is a small algorithm and it is everywhere: resolution for predicate logic,
Hindley–Milner type inference, pattern matching in a logic programming
language, term rewriting. Learning it once pays off repeatedly.

## The algorithm

Keep a set of pairs to solve and a substitution built so far. Repeatedly take
a pair, apply what you already know to both sides, and:

- **equal already** — discard the pair;
- **one side is a variable** `X` — check `X` does not occur in the other side,
  then bind `X` and carry on;
- **both are functions** — the symbols and arity must match, then replace the
  pair with the pairs of corresponding arguments;
- **anything else** — fail, and say why.

Failure should be informative. "No unifier" is not useful; "different function
symbols, `f` and `g`" is. Both failure modes are distinct messages here for
exactly that reason.

## The occurs check

Unifying `X` with `f(X)` requires `X = f(X) = f(f(X)) = …`. No finite term
satisfies it.

```bash
logickit unify "X" "f(X)"
# no unifier: X occurs in f(X), so no finite term unifies them
```

Skip the check and the algorithm builds a cyclic structure, then loops or
crashes when something walks it. Worse, in a theorem prover it lets through
"proofs" that are not proofs.

The version that is easy to miss is the one where the cycle only appears after
substituting. Unifying `g(X, Y)` with `g(Y, f(X))`: the first pair gives
`X := Y`, and only after applying that does the second pair become `Y` against
`f(Y)`. So the occurs check has to look **through** the substitution built so
far, not just at the raw term. That is one line, and it is the line I would
have got wrong if I had not written a test for it.

Several Prolog systems omit the check by default, for speed, and document that
they do. It is a deliberate trade, not an oversight.

## Most general

An algorithm returning `{X := a, Y := b}` for `f(X, Y)` against `f(a, Y)`
would be wrong even though both sides become equal — it commits `Y` to `b`
for no reason. The unifier must be **most general**: any other unifier is an
instance of it.

Unifying `f(X)` with `f(Y)` must produce `{X := Y}` and not `{X := a, Y := a}`.
Binding a variable to a constant when a variable would do throws away
solutions, and in a theorem prover that means losing proofs.

## Where it goes

For predicate resolution, two clauses no longer resolve because a literal and
its exact negation appear. They resolve when a literal and the negation of
another **unify**, and the resulting clause has the unifier applied to it.

Unification is the step that lifts resolution from propositional logic to
predicate logic. That is why a small syntactic algorithm gets its own week.
