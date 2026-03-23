# Forza Pit Strategy Calculator

A command-line tool written in Python to calculate optimal tire and fuel strategies for a race. The calculator natively connects to the Forza Motorsport UDP Telemetry stream to actively measure your car's tire wear rates and fuel consumption by analyzing your practice laps, outputting highly precise stint distributions and pit stop strategies based on real data.

## Setup

1. Ensure you have Python 3.12+ and `pipenv` installed on your machine.
2. Clone or download this repository.
3. Run `pipenv install --dev` to set up the virtual environment and install all required source and development dependencies.

## Usage

### 1. Configuration (Forza Telemetry)
Before running the calculator, ensure Forza Motorsport is configured to send Data Out (UDP telemetry) to the address matching your `config.json` settings natively located in the root of the project:

```json
{
  "udp": {
    "host": "0.0.0.0",
    "port": 36792,
    "timeout_seconds": 30.0
  }
}
```
*Note: In Forza's HUD settings, set **Data Out** to On, **Data Out IP Address** to your machine's local IP (or `127.0.0.1` if running locally), **Data Out IP Port** to `36792`, and explicitly set the **Data Out Packet Format** to **DASH**.*

### 2. Automated Collection (Recommended)
You can run the tool's integrated collector and calculation orchestration script automatically by executing:

```bash
pipenv run calculate
```

- When triggered, it will spin up a UDP server asynchronously waiting for Forza's practice laps.
- Run a few clean laps!
- The script uses the active data stream to empirically evaluate your precise tire wear rates and fuel consumption per lap.
- Once you are finished driving (or simply pause the game), the collector will safely timeout (defined natively in `config.json` as `timeout_seconds`, defaulting to 30s) and automatically advance to the terminal strategy builder.
- Input your race's total lap count, target tire wear boundaries, and maximum acceptable pits, and it will output all calculated strategies!

### 3. Utility Scripts
The project comes packaged with pipenv shorthands for standard developer utilities:
- **`pipenv run test`**: Runs the entire `pytest` mock testing validation framework suite locally.
- **`pipenv run lint`**: Formats the codebase via `black` and strictly checks for logic errors using `flake8`.

---

## Manual Execution (Legacy Option)

If you do not want to connect the UDP collector to gather data dynamically, you can still natively execute the legacy strategy calculation logic by passing your metrics explicitly via the command line arguments.

```bash
pipenv run python -m src.strategy.calculator [arguments]
```

### Arguments

| Short | Long | Description | Required | Default |
|-------|------|-------------|----------|---------|
| `-w` | `--wear-rate` | Tire wear rate per lap as a percentage (e.g., `5` for 5%, `4.2` for 4.2%). | Yes | |
| `-t` | `--tire-type` | The compound the wear rate applies to. Choices: `s` (Soft), `m` (Medium), `h` (Hard). | Yes | |
| `-l` | `--laps` | Total number of laps in the race. | Yes | |
| `-f` | `--fuel-consumption` | Fuel consumption per lap as a percentage (e.g., `2` for 2%). | Yes | |
| `-m` | `--max-stops` | Maximum number of pit stops allowed in the race. | No | `3` |
| `-W` | `--target-wear` | Target tire wear percentage to pit at. | No | `70.0` |

