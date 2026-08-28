"""``logickit`` on the command line: the demonstrations, runnable."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .dpll import solve
from .formula import ParseError, parse
from .normal_forms import render_clauses, to_clauses, to_nnf
from .resolution import refute
from .semantics import (
    entailment_counter_model,
    format_assignment,
    is_satisfiable,
    is_tautology,
    render_truth_table,
    signature,
)
from .temporal import TransitionSystem, check, parse_ltl
from .unification import TermError, format_substitution, parse_term, unify

EXIT_OK = 0
EXIT_FALSE = 1
EXIT_USAGE = 2


def _cmd_table(args: argparse.Namespace) -> int:
    formula = parse(args.formula)
    print(render_truth_table(formula))
    print()
    if is_tautology(formula):
        print("valid: true under every assignment")
        return EXIT_OK
    if is_satisfiable(formula):
        print("satisfiable, but not valid")
    else:
        print("unsatisfiable: false under every assignment")
    return EXIT_FALSE


def _cmd_entails(args: argparse.Namespace) -> int:
    premises = [parse(text) for text in args.premise]
    conclusion = parse(args.conclusion)
    witness = entailment_counter_model(premises, conclusion)
    joined = ", ".join(str(premise) for premise in premises) or "(no premises)"
    if witness is None:
        print(f"{joined} |= {conclusion}")
        print("holds: every model of the premises is a model of the conclusion")
        return EXIT_OK
    print(f"{joined} |/= {conclusion}")
    print(f"counter-model: {format_assignment(witness)}")
    print("under that assignment every premise is true and the conclusion is false")
    return EXIT_FALSE


def _cmd_cnf(args: argparse.Namespace) -> int:
    formula = parse(args.formula)
    print(f"input : {formula}")
    print(f"nnf   : {to_nnf(formula)}")
    clauses = to_clauses(formula)
    print(f"cnf   : {render_clauses(clauses)}")
    print(f"clauses: {len(clauses)}")
    return EXIT_OK


def _cmd_solve(args: argparse.Namespace) -> int:
    formula = parse(args.formula)
    clauses = to_clauses(formula)
    solution = solve(clauses, signature(formula))
    print(f"cnf: {render_clauses(clauses)}")
    if args.trace:
        print("\ntrace:")
        for line in solution.statistics.trace:
            print("  " + line)
    statistics = solution.statistics
    print(
        f"\nunit propagations: {statistics.unit_propagations}, "
        f"pure literals: {statistics.pure_literals}, "
        f"decisions: {statistics.decisions}, conflicts: {statistics.conflicts}"
    )
    if solution.satisfiable:
        print(f"satisfiable: {format_assignment(solution.model or {})}")
        return EXIT_OK
    print("unsatisfiable")
    return EXIT_FALSE


def _cmd_refute(args: argparse.Namespace) -> int:
    formula = parse(args.formula)
    clauses = to_clauses(formula)
    print(f"cnf: {render_clauses(clauses)}")
    result = refute(clauses)
    if result.found:
        print(f"\nrefuted in {len(result.steps)} resolution step(s):")
        for step in result.steps[-args.show :]:
            print("  " + str(step))
        print("\nthe empty clause was derived, so the formula is unsatisfiable")
        return EXIT_OK
    print("\nno refutation found: the clause set is satisfiable")
    return EXIT_FALSE


def _cmd_unify(args: argparse.Namespace) -> int:
    left = parse_term(args.left)
    right = parse_term(args.right)
    result = unify(left, right)
    print(f"left : {left}")
    print(f"right: {right}")
    if result.success:
        print(f"mgu  : {format_substitution(result.substitution)}")
        return EXIT_OK
    print(f"no unifier: {result.reason}")
    return EXIT_FALSE


def _cmd_check(args: argparse.Namespace) -> int:
    # A two-process mutual exclusion sketch, small enough to read.
    system = TransitionSystem(
        initial="idle",
        transitions={
            "idle": ["wait_a", "wait_b"],
            "wait_a": ["crit_a", "wait_both"],
            "wait_b": ["crit_b", "wait_both"],
            "wait_both": ["crit_a", "crit_b"],
            "crit_a": ["idle"],
            "crit_b": ["idle"],
        },
        labels={
            "idle": [],
            "wait_a": ["waiting"],
            "wait_b": ["waiting"],
            "wait_both": ["waiting"],
            "crit_a": ["critical", "a"],
            "crit_b": ["critical", "b"],
        },
    )
    formula = parse_ltl(args.formula)
    result = check(system, formula, args.bound)
    print(f"formula: {formula}")
    print(f"runs examined: {result.runs_examined}")
    if result.satisfied:
        print("holds on every lasso within the bound")
        return EXIT_OK
    print(f"counterexample: {result.counterexample}")
    return EXIT_FALSE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logickit",
        description="Runnable demonstrations of a logic course: semantics, CNF, DPLL, "
        "resolution, unification and LTL model checking.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    table = sub.add_parser("table", help="print a truth table and say whether the formula is valid")
    table.add_argument("formula")
    table.set_defaults(func=_cmd_table)

    entails = sub.add_parser(
        "entails", help="check entailment, and show a counter-model if it fails"
    )
    entails.add_argument("conclusion")
    entails.add_argument("--premise", action="append", default=[])
    entails.set_defaults(func=_cmd_entails)

    cnf = sub.add_parser("cnf", help="convert to negation normal form and then to clauses")
    cnf.add_argument("formula")
    cnf.set_defaults(func=_cmd_cnf)

    solver = sub.add_parser("solve", help="decide satisfiability with DPLL")
    solver.add_argument("formula")
    solver.add_argument("--trace", action="store_true", help="show every step the search took")
    solver.set_defaults(func=_cmd_solve)

    resolution = sub.add_parser("refute", help="derive the empty clause by resolution")
    resolution.add_argument("formula")
    resolution.add_argument("--show", type=int, default=10, help="how many final steps to print")
    resolution.set_defaults(func=_cmd_refute)

    unifier = sub.add_parser("unify", help="unify two first-order terms")
    unifier.add_argument("left")
    unifier.add_argument("right")
    unifier.set_defaults(func=_cmd_unify)

    model = sub.add_parser("check", help="model check an LTL formula against the example system")
    model.add_argument("formula")
    model.add_argument("--bound", type=int, default=12, help="maximum path length to explore")
    model.set_defaults(func=_cmd_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ParseError, TermError, ValueError) as failure:
        print(f"error: {failure}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
