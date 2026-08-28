# 5. CNF, DPLL and resolution

Where the course turns from "what does this mean" to "how would a machine
decide it".

## Conjunctive normal form

A **literal** is a variable or its negation. A **clause** is a disjunction of
literals. A formula in CNF is a conjunction of clauses:

```
(p | ~q) & (q | r | ~s) & (~p)
```

Everything is convertible to CNF, in three steps, each preserving meaning:

1. **Remove `->` and `<->`** using `φ -> ψ ≡ ~φ | ψ` and
   `φ <-> ψ ≡ (~φ | ψ) & (φ | ~ψ)`.
2. **Push negations inwards** with De Morgan and double-negation elimination,
   until every negation sits directly on a variable. This is **negation normal
   form**.
3. **Distribute `|` over `&`**: `A | (B & C) ≡ (A | B) & (A | C)`.

Step 3 is the expensive one. Distributing over a conjunction of `n` clauses
multiplies the clause count, and the growth is exponential in the worst case.
That is a property of this method, not a defect of an implementation, and it
is why industrial tools use a structure-preserving translation that adds new
variables instead — equisatisfiable rather than equivalent, and linear.

The version here is the honest exponential one:

```bash
logickit cnf "~((p | q) & (r -> s))"
```

Two simplifications are worth doing as you go: a clause containing both `p`
and `~p` is true under every assignment and can be dropped, and a clause that
a smaller clause already implies is redundant.

## Why CNF at all

Because it makes both remaining procedures easy to state.

- A clause set is satisfiable iff there is an assignment satisfying **every**
  clause.
- Making a literal true **deletes** every clause containing it and **shrinks**
  every clause containing its negation.

That second fact is the whole of DPLL.

## DPLL

Case analysis with two shortcuts that do most of the work.

**Unit propagation.** A clause with one literal left forces that literal.
No choice, no branching. Setting it usually creates more unit clauses, so this
cascades — and cascading unit propagation is where a solver spends most of its
time.

**Pure literals.** If a variable appears only positively across all remaining
clauses, setting it true can only help. It satisfies clauses and breaks
nothing.

**Then, and only then, branch.** Pick a literal, try it, and on failure try
its negation. An empty clause means a conflict: every literal in it was
falsified, and this branch is dead.

```bash
logickit solve "p & (~p | q) & (~q | r)" --trace
#   unit propagate p
#   unit propagate q
#   unit propagate r
#   all clauses satisfied
```

Three variables, no branching at all. A truth table would have built eight
rows to find out the same thing, and at twenty variables it would build a
million while DPLL still does three propagations.

What I understood only after writing it: DPLL is not a cleverer way of
enumerating assignments. It is a way of *never constructing most of them*.

## Resolution

Resolution answers the same question and returns a different kind of answer.

The rule: from `(A | p)` and `(B | ~p)`, derive `(A | B)`. Resolve on exactly
one complementary pair — resolving on two at once yields a clause containing
both `q` and `~q`, which is trivially true and useless.

Resolution is a **refutation** procedure. It does not prove `φ`; it derives
the **empty clause** from `¬φ`. The empty clause is a disjunction of nothing,
which is false, so deriving it means the clause set is unsatisfiable.

```bash
logickit refute "(p -> q) & p & ~q"
#   (p) + (~p | q) on p => (q)
#   (~p | q) + (~q) on q => (~p)
#   (~q) + (q) on q => ()
```

To prove `Γ ⊨ φ`: convert `Γ ∪ {¬φ}` to clauses and refute it. Every automated
theorem prover in the course is that sentence plus engineering.

## DPLL or resolution?

They decide the same question and hand back different things, and that is the
reason to have both:

| | DPLL | Resolution |
|---|---|---|
| Answer when satisfiable | a model you can check | nothing useful |
| Answer when unsatisfiable | "no model exists" | a derivation you can check step by step |
| Cost | search, exponential worst case | saturation, grows fast in practice |
| Descendant in industry | every modern SAT solver | first-order theorem provers |

The distinction that matters: DPLL's answer to *satisfiable* is verifiable in
one pass — evaluate the model. Resolution's answer to *unsatisfiable* is
verifiable in one pass — replay the derivation. Neither gives you a cheaply
checkable certificate for the other direction, and that asymmetry is the same
one that has run through the whole course.
