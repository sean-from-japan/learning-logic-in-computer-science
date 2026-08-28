# 2. Natural deduction

## What changes

Truth tables answer semantic questions by checking every case. Natural
deduction answers them by **building an object**: a derivation from the
premises to the conclusion in which every step is licensed by a rule. It never
mentions truth values at all.

The notation shifts with it. `⊨` is about models; `⊢` is about derivations.
`φ ⊢ ψ` says *there is a derivation*, not *ψ is true*.

## The rules come in pairs

Each connective has an **introduction** rule (how to build one) and an
**elimination** rule (how to use one). Once you see it as a pair, the set stops
needing memorisation:

| Connective | Introduce it by | Use it by |
|---|---|---|
| `∧` | having both sides | taking either side |
| `∨` | having either side | proving the goal from each side separately |
| `→` | assuming the left and deriving the right | having the left, and detaching |
| `¬` | assuming it and deriving `⊥` | putting it beside the thing it negates to get `⊥` |
| `⊥` | — | deriving anything at all |

The pattern: introduction rules build the connective into the conclusion,
elimination rules consume it from a premise. A proof is usually elimination
downwards from the premises until you meet introduction upwards from the goal.

## Assumptions, and the mistake I kept making

Two rules — `→I` and `¬I` — work by *temporarily assuming* something and then
**discharging** it. The assumption is live inside the box and dead outside it.

The error I made repeatedly was using a formula derived inside a box after the
box had closed. It always looked fine, because the formula was on the page and
I had derived it correctly. What made it wrong was that its derivation depended
on an assumption that no longer holds.

The check that fixed it: for every line, ask *which assumptions is this line
standing on?* If any of them has been discharged, the line is not available.

## Disjunction elimination is where the work is

`∨E` is the only rule that needs two sub-proofs. Given `φ ∨ ψ` and a goal `χ`,
you must derive `χ` from `φ` and, separately, derive `χ` from `ψ`. Both. If
only one case goes through, you have proved nothing, because you never knew
which side held.

This is case analysis, it is the same shape as a proof by cases in
mathematics, and it is why derivations involving `∨` are longer than they look.

## Classical versus intuitionistic

Three rules are optional and stand or fall together:

- proof by contradiction (assume `¬φ`, derive `⊥`, conclude `φ`)
- excluded middle (`φ ∨ ¬φ`, for free)
- double negation elimination (`¬¬φ ⊢ φ`)

Drop them and you have **intuitionistic** logic, where proving something
exists means exhibiting it. Keep them and you have **classical** logic, where
"it cannot fail to exist" counts.

This is not a technicality about which rules are allowed. It is why proof
assistants matter to programming: in a system where a proof of existence must
carry a witness, a proof *is* a program that produces the thing. That
connection is the reason this topic is in a computer science degree at all.

## Derivations versus counter-models, once more

The asymmetry from the previous note, now sharper:

- To show `φ` **is** valid: build a derivation. Search, insight, work.
- To show `φ` is **not** valid: produce one assignment. Mechanical.

So when you are stuck on a derivation, the first move is not to try harder. It
is to check whether the thing is valid at all:

```bash
logickit table "((p -> q) & q) -> p"
# satisfiable, but not valid
```

I lost real time to derivations of things that were false.
