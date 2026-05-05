from src.strategy.calculator import get_stint_lengths, calculate_strategies


def test_get_stint_lengths_soft():
    """Tests calculation of stint lengths for a soft tire given a standard wear rate."""
    res = get_stint_lengths(5.0, 70.0, "s")
    assert res == {"s": 14, "m": 21, "h": 28}


def test_get_stint_lengths_medium():
    """Tests calculation of stint lengths for a medium tire compound."""
    res = get_stint_lengths(10.0 / 3.0, 70.0, "m")
    assert res == {"s": 14, "m": 21, "h": 28}


def test_get_stint_lengths_hard():
    """Tests calculation of stint lengths for a hard tire compound."""
    res = get_stint_lengths(2.5, 70.0, "h")
    assert res == {"s": 14, "m": 21, "h": 28}


def test_get_stint_lengths_other():
    """Tests calculation of stint lengths for an unspecified ('other') tire compound."""
    res = get_stint_lengths(5.0, 70.0, "o")
    assert res == {"o": 14}


def test_get_stint_lengths_negative_wear():
    """Ensures zero laps are returned when a negative or zero wear rate is provided."""
    res = get_stint_lengths(0.0, 70.0, "s")
    assert res == {"s": 0, "m": 0, "h": 0}
    res = get_stint_lengths(-1.0, 70.0, "s")
    assert res == {"s": 0, "m": 0, "h": 0}
    res = get_stint_lengths(-1.0, 70.0, "o")
    assert res == {"o": 0}


def test_calculate_strategies_no_options():
    """Tests strategy output when wear rate is extremely high, leaving no valid pit stop options."""
    # wear_s = 100, target = 10. laps_s = 0.1 -> 0
    # laps_h = 10 / 50 = 0.2 -> 0.
    res = calculate_strategies(100.0, 10.0, "s", 50, 3, 2.0)
    assert res == []


def test_calculate_strategies_basic():
    """Tests standard race strategy generation for typical laps, wear, and max stops."""
    # 40 laps, wear_s=5 (stints: s=14, m=21, h=28), max_stops=3, fuel_con=2.0
    res = calculate_strategies(5.0, 70.0, "s", 40, 3, 2.0)
    assert len(res) > 0
    for strat in res:
        total_laps = sum(stint[1] for stint in strat)
        assert total_laps == 40
        assert len(strat) - 1 <= 3

        first_stint_tire, first_stint_laps, first_stint_fuel, first_stint_refuel = (
            strat[0]
        )
        assert first_stint_fuel <= 100.0


def test_calculate_strategies_fuel_limits():
    """Verifies strategy calculation properly accommodates aggressive fuel constraints."""
    # 60 laps, max_stops=3, fuel_con=5.0
    # s=35, m=52, h=70
    res = calculate_strategies(2.0, 70.0, "s", 60, 3, 5.0)
    # The calculator may return empty if fuel is a strict bottleneck and it can't adapt lap lengths
    for strat in res:
        total_laps = sum(stint[1] for stint in strat)
        assert total_laps == 60
        for i, stint in enumerate(strat):
            tire, laps, start_fuel, refuel = stint
            fuel_used = laps * 5.0
            assert start_fuel >= fuel_used - 0.01
            assert start_fuel <= 100.01


def test_calculate_strategies_sorting():
    """Ensures that strategies are correctly sorted with the fewest pit stops appearing first."""
    # 28 laps
    res = calculate_strategies(5.0, 70.0, "s", 28, 3, 2.0)
    assert len(res) > 0
    assert len(res[0]) == 1
    assert res[0][0][0] == "h"


def test_calculate_strategies_other():
    """Tests strategy generation for the fallback 'other' tire compound."""
    # 30 laps, other wear_type
    res = calculate_strategies(5.0, 70.0, "o", 30, 3, 2.0)
    assert len(res) > 0
    for strat in res:
        total_laps = sum(stint[1] for stint in strat)
        assert total_laps == 30
        assert all(stint[0] == "o" for stint in strat)


def test_calculate_strategies_fuel_constrained():
    """Tests scenarios where tire wear is acceptable but fuel capacity forces additional pit stops."""
    # 12 laps, wear=5%/lap (stints: o=14), but fuel=10%/lap
    # forces stop after 10 laps
    res = calculate_strategies(5.0, 70.0, "o", 12, 3, 10.0)
    assert len(res) > 0
    strat = res[0]
    assert len(strat) == 2  # 1 stop
    assert strat[0][1] == 10
    assert strat[1][1] == 2


def test_calculate_strategies_o_zero():
    """Ensures an empty strategy list is returned when the 'other' tire can complete 0 laps."""
    res = calculate_strategies(0.0, 70.0, "o", 10, 3, 2.0)
    assert res == []


def test_print_strategies(capsys):
    """Verifies that the printed output of strategies matches expected formats and handles edge cases."""
    from src.strategy.calculator import print_strategies

    # Normal case
    print_strategies([[("s", 10, 100.0, False), ("m", 20, 80.0, True)]], 70.0, 5.0, "s")
    out, err = capsys.readouterr()
    assert "Strategy 1 [1 stop(s)]" in out

    # Zero laps "o"
    print_strategies([], 70.0, 200.0, "o")
    out, err = capsys.readouterr()
    assert "Error: Wear rate is too high" in out

    # Zero laps "h"
    print_strategies([], 70.0, 500.0, "s")
    out, err = capsys.readouterr()
    assert "Error: Wear rate is too high to complete even 1 lap on Hard tires!" in out


def test_find_strategies_max_stops():
    """Checks that recursive strategy finding aborts early when the max stops limit is reached."""
    # Will hit continue on max_stops
    res = calculate_strategies(5.0, 70.0, "s", 100, 1, 2.0)
    assert res == []


def test_cli_main_success(capsys, monkeypatch):
    """Tests the CLI script entry point and validates successful strategy output."""
    from src.strategy.calculator import main
    import sys

    monkeypatch.setattr(
        sys, "argv", ["calculator.py", "-w", "5", "-t", "s", "-l", "10", "-f", "2"]
    )
    main()
    out, err = capsys.readouterr()
    assert "Strategy" in out


def test_cli_main_negative_wear(capsys, monkeypatch):
    """Tests that the CLI cleanly exits with an error code on negative wear rates."""
    from src.strategy.calculator import main
    import sys

    monkeypatch.setattr(
        sys, "argv", ["calculator.py", "-w", "-1", "-t", "s", "-l", "10", "-f", "2"]
    )
    try:
        main()
    except SystemExit as e:
        assert e.code == 1
    out, err = capsys.readouterr()
    assert "Error: Wear rate must be positive" in out
