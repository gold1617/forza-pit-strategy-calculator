# Forza Pit Strategy Calculator

A simple command-line tool written in Python to calculate optimal tire and fuel strategies for a race. The calculator takes into account your car's tire wear rates and fuel consumption, outputting possible stint distributions and pit stop strategies.

## Setup

1. Ensure you have Python 3 and `pipenv` installed on your machine.
2. Clone or download this repository.
3. Run `pipenv install` to set up the virtual environment and install any required dependencies.

## Usage

You can run the tool from your terminal or command prompt by executing `strategy_calculator.py` using `pipenv run` and passing the necessary flags.

```bash
pipenv run python strategy_calculator.py [arguments]
```

### Arguments

| Short | Long | Description | Required | Default |
|-------|------|-------------|----------|---------|
| `-w` | `--wear-rate` | Tire wear rate per lap as a percentage (e.g., `5` for 5%, `4.2` for 4.2%). | Yes | |
| `-t` | `--tire-type` | The compound the wear rate applies to. Choices: `s` (Soft), `m` (Medium), `h` (Hard). | Yes | |
| `-l` | `--laps` | Total number of laps in the race. | Yes | |
| `-f` | `--fuel-consumption` | Fuel consumption per lap as a percentage (e.g., `2` for 2%). | Yes | |
| `-m` | `--max-stops` | Maximum number of pit stops allowed in the race. | No | `3` |

### Example

Let's say you are doing a 20-lap race. In practice, you measured your soft tires wearing at 5% per lap, and your fuel consuming at 4.5% per lap. You'd like to limit the strategies to a maximum of 2 stops:

```bash
pipenv run python strategy_calculator.py --wear-rate 5 --tire-type s --laps 20 --fuel-consumption 4.5 --max-stops 2
```

Using short flags:

```bash
pipenv run python strategy_calculator.py -w 5 -t s -l 20 -f 4.5 -m 2
```

### Output Example

The script outputs the maximum number of laps each compound can withstand (assuming a 70% target wear threshold), followed by all viable race strategies sorted by lowest number of pit stops and softest tire choices.

```text
Max laps per tire (at 70% wear): Soft: 14, Medium: 21, Hard: 28

Total possible strategies found: ...

Strategy 1 [1 stop(s)]: S (14 laps, fuel to 100.0%)  -> S (6 laps) 
Strategy 2 [1 stop(s)]: S (10 laps, fuel to 100.0%)  -> M (10 laps) 
```
