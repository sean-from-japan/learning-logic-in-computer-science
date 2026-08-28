# 1. Propositional logic: syntax and semantics

## Two things that are easy to blur

A formula is a **string of symbols**. Whether it is true is a question about
an **assignment of truth values to its variables**. Keeping those apart is the
whole of this topic, and most early confusion is a place where they got mixed.

- Syntax: is `p & (q | r)` well formed? A grammar answers this.
- Semantics: is it true? Only a question once you say what `p`, `q`, `r` are.

The grammar this repository implements:

```
formula ::= variable | T | F
          | ~ formula
          | formula & formula
          | formula | formula
          | formula -> formula
          | formula <-> formula
          | ( formula )
```

with `~` binding tightest, then `&`, then `|`, then `->`, then `<->`, and
`->` associating to the right.

That last clause is not decoration. `p -> q -> r` means `p -> (q -> r)`, and
the other bracketing is a different formula with a different truth table:

```bash
logickit entails "(p -> q) -> r" --premise "p -> q -> r"
```

## Implication is not causation

`p -> q` is false in exactly one row: `p` true and `q` false. So
`F -> anything` is true, and this is the single most argued-with definition in
the subject.

The way I stopped fighting it: read `p -> q` as *"I am not claiming anything
unless p happens; if p happens, I promise q."* If `p` never happens, the
promise was never tested, so it was not broken. It is not a claim about `p`
causing `q`; it is a claim about which combinations are ruled out.

## Valid, satisfiable, unsatisfiable

Three questions about one formula, and it helps to see them as questions about
*how many* rows of the truth table say true:

| Every row | At least one row | No row |
|---|---|---|
| valid (a tautology) | satisfiable | unsatisfiable (a contradiction) |
| `p \| ~p` | `p & q` | `p & ~p` |

And a fact that makes half the later material work: **φ is valid exactly when
¬φ is unsatisfiable.** That is why a SAT solver, which only answers "is there
a model?", can be used to answer "is this valid?" — you ask it about the
negation. Every automated proof method in this course is built on that
exchange.

## Entailment

`φ₁, …, φₙ ⊨ ψ` means: every assignment making all the premises true also
makes the conclusion true. Not "ψ follows plausibly" — *every* assignment,
without exception.

Which gives the one practical technique of this topic. To show an entailment
**fails**, you do not argue: you produce one row.

```bash
logickit entails "p" --premise "p -> q" --premise "q"
# counter-model: p=F, q=T
```

`p -> q` is true (`p` is false), `q` is true, and `p` is false. One row, and
the argument is finished. Affirming the consequent, refuted in a line.

Two consequences that look strange and are not:

- **A contradiction entails everything.** No assignment makes `p` and `¬p`
  both true, so there is no row where the premises hold and the conclusion
  fails — vacuously.
- **A valid formula is entailed by nothing at all.** `⊨ p ∨ ¬p` needs no
  premises.

## Where this goes

Truth tables decide everything here, and they decide it in `2ⁿ` rows. Twenty
variables is a million rows; sixty is not happening. Every remaining topic in
the course is a response to that: derivations that never build the table
(natural deduction), search that prunes it (DPLL), and a form that a machine
can search (CNF and resolution).
