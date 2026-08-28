from logickit.cli import main


def test_a_valid_formula_exits_zero(capsys):
    assert main(["table", "p | ~p"]) == 0
    assert "valid" in capsys.readouterr().out


def test_a_satisfiable_but_invalid_formula_exits_one(capsys):
    assert main(["table", "p & q"]) == 1
    assert "not valid" in capsys.readouterr().out


def test_entailment_prints_a_counter_model_when_it_fails(capsys):
    code = main(["entails", "p", "--premise", "p -> q", "--premise", "q"])
    assert code == 1
    assert "counter-model" in capsys.readouterr().out


def test_entailment_that_holds_exits_zero(capsys):
    assert main(["entails", "q", "--premise", "p -> q", "--premise", "p"]) == 0


def test_cnf_shows_both_stages(capsys):
    assert main(["cnf", "~(p -> q)"]) == 0
    output = capsys.readouterr().out
    assert "nnf" in output and "cnf" in output


def test_solve_reports_a_model(capsys):
    assert main(["solve", "(p | q) & ~p"]) == 0
    assert "satisfiable" in capsys.readouterr().out


def test_solve_reports_unsatisfiable(capsys):
    assert main(["solve", "p & ~p"]) == 1


def test_solve_can_show_its_trace(capsys):
    main(["solve", "p & (~p | q)", "--trace"])
    assert "unit propagate" in capsys.readouterr().out


def test_refute_derives_the_empty_clause(capsys):
    assert main(["refute", "(p -> q) & p & ~q"]) == 0
    assert "empty clause" in capsys.readouterr().out


def test_unify_prints_the_most_general_unifier(capsys):
    assert main(["unify", "f(X, b)", "f(a, Y)"]) == 0
    assert "X := a" in capsys.readouterr().out


def test_unify_explains_the_occurs_check(capsys):
    assert main(["unify", "X", "f(X)"]) == 1
    assert "occurs" in capsys.readouterr().out


def test_check_holds_for_mutual_exclusion(capsys):
    assert main(["check", "G !(a & b)"]) == 0


def test_check_returns_a_counterexample_for_starvation(capsys):
    assert main(["check", "G F a"]) == 1
    assert "counterexample" in capsys.readouterr().out


def test_a_malformed_formula_is_an_error_not_a_traceback(capsys):
    assert main(["table", "p &"]) == 2
    assert "error:" in capsys.readouterr().err
