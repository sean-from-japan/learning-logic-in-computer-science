# The study system

How I studied a logic module, why it was built this way, and what I would
change. This is the part of the repository I think is actually transferable;
the code is the evidence that it worked.

## The problem I was solving

I took the module on exchange, in my second language, in a subject where the
notation is the content. Three specific difficulties, in the order they
mattered:

1. **Notation drifts.** The same idea appears as `⊨` and `|=`, as `⊢` and
   `|-`, with rules named `∧E` in one place and `&-elim` in another. Every
   variant costs a moment of translation, and in an exam those moments are
   the whole budget.
2. **The material is a dependency graph, not a list.** Resolution needs CNF;
   CNF needs equivalences; the equivalences need the semantics of `→`.
   Missing one early node makes three later topics feel arbitrary.
3. **I can generate practice faster than I can trust it.** A language model
   will produce a hundred exercises on natural deduction in a minute, and
   some of the answers will be wrong in ways that are invisible if you are
   still learning the subject. Unverified practice is worse than none: it
   teaches the mistake.

## The shape of the answer

The system had three parts.

### 1. Two grounding documents, written before any studying

Before generating anything, I wrote two documents by hand from the primary
material:

- **A notation table.** Every symbol, its standard form, and every
  alternative spelling I had seen for it. This is the file that makes the
  rest work: with it, a generated explanation using `~` and a lecture using
  `¬` stop being two things.
- **A course context document.** The topic sequence, what depends on what,
  and the small number of facts that everything else hangs off — soundness in
  one direction, completeness in the other, propositional logic decidable,
  predicate logic not.

Both were then given to every AI tool I used, as the authority it had to
follow. That is the whole trick: **the model is not the source of truth about
the course; a document I wrote from the primary material is.** When a
generated explanation contradicted the grounding document, the generated
explanation was wrong, and I did not have to adjudicate it every time.

### 2. Generation used for variation, never for answers

What AI was genuinely good for:

- **More instances of a problem I had already solved once.** Same shape,
  different formula. This is the thing textbooks never have enough of.
- **Counterexample hunting.** "Give me a formula where this rule looks like
  it applies but does not." Wrong answers here are cheap, because checking a
  counterexample is much easier than finding one.
- **Explaining a step I had already got right, differently.** When my
  derivation worked but I could not say why, a second phrasing often located
  the gap.

What it was bad for, and what I stopped asking it:

- **Producing a derivation I then trusted.** A natural deduction proof can
  look completely convincing and use an elimination rule with the wrong
  discharge, and if I could spot that reliably I would not have needed the
  proof.
- **Deciding whether something is valid.** This is exactly the question a
  program answers exactly and a language model answers plausibly.

### 3. Every final answer checked by me, by hand or by machine

The rule I ended up with: **nothing enters my notes until I have verified it
in a way that does not involve the thing that produced it.**

For semantic claims that verification can be mechanical — build the truth
table, or find the counter-model. That is the observation this repository
grew out of. Once you have written `entailment_counter_model`, "is this
entailment valid?" stops being a matter of confidence:

```bash
logickit entails "p" --premise "p -> q" --premise "q"
# p -> q, q |/= p
# counter-model: p=F, q=T
```

For syntactic claims — that a derivation is correct — I checked by hand,
rule by rule, against the notation table. Slower, no way around it.

## What made the difference

**Writing the notation table first was worth more than any amount of
practice.** It is an hour of dull work that removes a class of confusion
permanently, and everything downstream — my notes, generated material,
conversations — becomes consistent for free.

**Being able to check a semantic claim in one second changes how you study.**
Not because the program does the work, but because a cheap check makes you
willing to be wrong more often, and being wrong more often is the fast path.

**Implementing a procedure is a better test of understanding than doing it.**
I could carry out CNF conversion by hand well before I could write it, and
what the code forced was the part I had been skating over: what happens to a
clause containing both `p` and `¬p`, what "the empty clause" means, why the
distribution step is the one that explodes.

## What I would change

- **I built the tools after the exam, not during.** Writing the CNF converter
  in week 8 would have taught me more than the extra exercises I did instead.
  Deciding what to implement *while* the topic is live is the change I would
  make.
- **The notation table was static.** It should have been the file I edited
  every week, not a thing I wrote once.
- **I checked semantics mechanically and syntax by hand.** A proof checker
  for natural deduction would have closed the remaining gap, and it is not a
  large program. That is the obvious next thing to build.

## Outcome

The module mark was 92/100. I am including it because it is the only external
evidence that the method held up under exam conditions, and because a study
method with no result attached is just an opinion. It is a mark for the
module, not for anything in this repository.
