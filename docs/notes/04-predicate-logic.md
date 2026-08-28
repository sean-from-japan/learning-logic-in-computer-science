# 4. Predicate logic

## What propositional logic cannot say

In propositional logic, "every student passed" is one atom `p`. Nothing
connects it to "Alice passed". The internal structure is invisible, so the
inference from one to the other cannot be made.

Predicate logic adds that structure: objects, functions on objects, relations
between them, and quantifiers over them.

## The pieces

- **Terms** name objects: a constant `alice`, a variable `x`, or a function
  applied to terms, `motherOf(x)`.
- **Predicates** make claims about terms: `Passed(x)`, `Older(x, y)`. A
  predicate is not a term — it does not name an object, it says something.
- **Quantifiers** bind variables: `∀x. Passed(x)`, `∃x. Passed(x)`.

The distinction I had to keep checking: `motherOf(alice)` is a *term* and
names a person; `Passed(alice)` is a *formula* and is true or false. Functions
build objects, predicates make claims, and a signature says which is which.

## Free and bound

In `∀x. Loves(x, y)`, `x` is **bound** by the quantifier and `y` is **free**.

Two things follow, and both are exam material because both are easy to get
wrong:

- The name of a bound variable does not matter. `∀x. P(x)` and `∀z. P(z)` are
  the same statement.
- A formula with a free variable is not true or false on its own. It becomes a
  claim only once the free variable is given a value.

**Substitution can capture.** Substituting a term into a formula, where the
term contains a variable that the formula quantifies, silently changes the
meaning:

```
∃y. Taller(x, y)             "someone is shorter than x"
substitute y for x  ->
∃y. Taller(y, y)             "someone is taller than themselves"
```

The `y` walked into the scope of `∃y` and got captured. The rule that stops
this — rename the bound variable first — looks like bookkeeping and is the
difference between a correct system and an unsound one.

## Semantics needs a structure

In propositional logic, truth needs an assignment: one truth value per
variable. In predicate logic it needs a **structure**: a non-empty domain of
objects, an object for each constant, a function for each function symbol,
and a relation for each predicate symbol.

`∀x. P(x)` is true in a structure when `P` holds of every object in *that
domain*. Change the domain and the answer changes. That is why "is this
formula valid" is so much harder here: valid means true in *every* structure,
over every domain, and there are infinitely many.

## The quantifier rules, and their side conditions

The natural deduction rules for quantifiers each carry a condition, and the
conditions are the content:

- **`∀I`** — to prove `∀x. P(x)`, prove `P(a)` for a **fresh** `a` about which
  you assumed nothing. Freshness is what makes the step general. Use an `a`
  that appears elsewhere and you have proved something about that particular
  `a`, not about everything.
- **`∀E`** — from `∀x. P(x)`, conclude `P(t)` for any term `t`, provided `t`
  is substitutable, i.e. capture does not occur.
- **`∃I`** — to prove `∃x. P(x)`, exhibit a `t` with `P(t)`. A witness.
- **`∃E`** — from `∃x. P(x)`, name the witness `a` — fresh again — assume
  `P(a)`, and derive your goal. The goal must not mention `a`, or you have
  concluded something about a name you invented.

Both freshness conditions guard the same mistake: **treating a name you
introduced as if it were a name you were given.**

## Counter-models are harder, and still the right move

To show a predicate formula is not valid you exhibit a structure where it
fails — and the useful ones are tiny. A domain of two elements is usually
enough.

`(∀x. ∃y. R(x, y)) → (∃y. ∀x. R(x, y))` looks plausible: everyone relates to
someone, so surely someone is related to by everyone. Take the domain
`{1, 2}` with `R = {(1,2), (2,1)}`. Every element relates to something, and no
element is related to by everything. Two elements, and it is finished.

Swapping `∀∃` for `∃∀` is not valid. Building the two-element counter-model
myself is what made that stick, in a way that reading it never did.
