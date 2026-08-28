# 3. Soundness and completeness

Two theorems that connect the two halves of the course. They are usually
stated as symbol-pushing and they are not: each one rules out a specific,
imaginable disaster.

## The statements

- **Soundness:** if `Γ ⊢ φ` then `Γ ⊨ φ`. Everything derivable is true.
- **Completeness:** if `Γ ⊨ φ` then `Γ ⊢ φ`. Everything true is derivable.

## What each one rules out

**Without soundness, the proof system lies.** There would be a derivation,
every step correctly applying a rule, of something with a counter-model. A
proof would be worthless: you could derive `φ` and I could hand you an
assignment making it false, and we would both be right.

Soundness is what makes a derivation *evidence*. It is proved by induction on
the derivation: each rule, individually, preserves truth, so any stack of them
does too. That is a boring proof, and the boringness is the point — it can be
checked mechanically.

**Without completeness, the proof system is too weak.** There would be a
formula true in every model that no derivation reaches. The system would not
be *wrong*, just insufficient: some truths would be permanently out of reach
of the rules, and failing to find a proof would tell you nothing.

Completeness is the harder theorem, and it says the rule set is not missing
anything.

## The direction I kept mixing up

The mnemonic that finally stuck:

- **Sound** = does not make things up. `⊢` is the *smaller* side; soundness
  says it fits inside `⊨`.
- **Complete** = does not miss anything. `⊨` fits inside `⊢`.

Together: **`⊢` and `⊨` pick out exactly the same set.** Provable and true
coincide. Which means you may use whichever is more convenient — and that
licence is what the rest of the course spends its time on. Truth tables to
refute, derivations to establish, and no anxiety about the two disagreeing.

## Decidability is a separate question

Completeness says a proof exists. It does not say you can find it.

- **Propositional logic is decidable.** Build the truth table; the algorithm
  always terminates. Expensively, but always.
- **Predicate logic is undecidable.** No algorithm decides validity for every
  formula. This is Church's theorem, and it is not a gap waiting to be filled
  — it is a proof that no such algorithm exists.

Predicate logic is nevertheless **semi-decidable**: a search will eventually
find a proof if one exists. If none exists, it may run forever. That
asymmetry is the shape of every practical automated theorem prover: they
terminate with "proved", and otherwise they terminate with "I gave up", which
is not the same as "false".

## Why a computer science course cares

These theorems are the licence for the entire tooling stack that follows.

- A **SAT solver** decides satisfiability. Soundness and completeness of the
  proof system are what let you take "unsatisfiable" as a proof of validity of
  the negation.
- A **proof assistant** checks derivations rather than truth. Soundness is
  the reason a checked proof means anything at all, and it is why the trusted
  kernel of such a system is kept small: it is the one part where an error
  would be an error in soundness.

Every use of an automated tool in verification cashes out one of these two
theorems. That is why they are worth being precise about.
