import pytest
from unittest import mock
from src import main


@mock.patch("src.main.collect_telemetry")
@mock.patch("src.main.calculate_strategies")
@mock.patch("src.main.print_strategies")
@mock.patch("builtins.input")
@mock.patch(
    "builtins.open",
    new_callable=mock.mock_open,
    read_data='{"udp": {"host": "1.2.3.4", "port": 1234, "timeout_seconds": 10}}',
)
def test_main_success(
    mock_open, mock_input, mock_print_strat, mock_calc_strat, mock_collect
):
    """Verifies that the main workflow executes successfully with valid mock data."""
    mock_collect.return_value = (5.0, 2.0)
    mock_input.side_effect = ["s", "40", "3", "70"]
    mock_calc_strat.return_value = [[("s", 14, 100.0, True)]]

    main.main()

    mock_collect.assert_called_with("1.2.3.4", 1234, 10)
    mock_calc_strat.assert_called_with(5.0, 70.0, "s", 40, 3, 2.0)
    mock_print_strat.assert_called_once()


@mock.patch("src.main.collect_telemetry")
@mock.patch("builtins.open", side_effect=Exception("File not found"))
@mock.patch("builtins.input")
def test_main_telemetry_none(mock_input, mock_open, mock_collect):
    """Ensures the application exits cleanly if telemetry data is missing or invalid."""
    mock_collect.return_value = (None, None)
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 1


@mock.patch("src.main.collect_telemetry", return_value=(5.0, 2.0))
@mock.patch("builtins.input")
def test_main_invalid_tire(mock_input, mock_collect):
    """Tests application exit when the user inputs an unrecognized tire compound."""
    mock_input.side_effect = ["invalid"]
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 1


@mock.patch("src.main.collect_telemetry", return_value=(5.0, 2.0))
@mock.patch("builtins.input")
def test_main_invalid_laps(mock_input, mock_collect):
    """Tests application exit when the user inputs an invalid lap count."""
    mock_input.side_effect = ["s", "not_a_number"]
    with pytest.raises(SystemExit) as e:
        main.main()
    assert e.value.code == 1


@mock.patch("src.main.collect_telemetry", return_value=(5.0, 2.0))
@mock.patch("builtins.input")
@mock.patch("src.main.calculate_strategies")
@mock.patch("src.main.print_strategies")
def test_main_empty_inputs(mock_print, mock_calc, mock_input, mock_collect):
    """Verifies that default values are used when the user leaves optional inputs blank."""
    mock_input.side_effect = ["s", "40", "", ""]
    mock_calc.return_value = []
    main.main()
    mock_calc.assert_called_with(5.0, 70.0, "s", 40, 3, 2.0)
