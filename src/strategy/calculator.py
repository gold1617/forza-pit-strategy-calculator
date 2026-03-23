import argparse
import sys

cached_strategies = {}
stint_lengths = {}


def get_stint_lengths(wear_rate, target_wear, tire_type):
    if wear_rate <= 0:
        print("Error: Wear rate must be positive.")
        return {"s": 0, "m": 0, "h": 0}

    if tire_type == "s":
        wear_s = wear_rate
    elif tire_type == "m":
        wear_s = wear_rate * 1.5
    elif tire_type == "h":
        wear_s = wear_rate * 2.0

    wear_m = wear_s * (2.0 / 3.0)
    wear_h = wear_s * 0.5

    laps_s = target_wear / wear_s
    laps_m = target_wear / wear_m
    laps_h = target_wear / wear_h

    return {"s": round(laps_s), "m": round(laps_m), "h": round(laps_h)}


def calculate_strategies(
    wear_rate, target_wear, tire_type, laps, max_stops, fuel_consumption
):
    global stint_lengths
    stint_lengths = get_stint_lengths(wear_rate, target_wear, tire_type)

    if stint_lengths["h"] == 0:
        return []

    start_fuel = min(laps * fuel_consumption, 100.0)

    global cached_strategies
    cached_strategies = {}

    strategies = find_strategies(
        laps, max_stops, round(start_fuel, 2), fuel_consumption
    )

    strategies.sort(
        key=lambda strat: (
            len(strat),
            -sum(1 for stint in strat if stint[0] == "s"),
            -sum(1 for stint in strat if stint[0] == "m"),
        )
    )

    return strategies


def print_strategies(strategies, target_wear, wear_rate, tire_type):
    sl = get_stint_lengths(wear_rate, target_wear, tire_type)
    print(
        f"Max laps per tire (at {target_wear}% wear): Soft: {sl['s']}, Medium: {sl['m']}, Hard: {sl['h']}\n"
    )

    if sl["h"] == 0:
        print("Error: Wear rate is too high to complete even 1 lap on Hard tires!")
        return

    print(f"Total possible strategies found: {len(strategies)}\n")

    for i, strat in enumerate(strategies):
        strat_str = " -> ".join(
            [
                (
                    f"{t.upper()} ({laps} laps, fuel to {fuel:.1f}%) "
                    if i == 0 or refuel
                    else f"{t.upper()} ({laps} laps) "
                )
                for i, (t, laps, fuel, refuel) in enumerate(strat)
            ]
        )
        stops = len(strat) - 1
        print(f"Strategy {i+1} [{stops} stop(s)]: {strat_str}")


def find_strategies(num_laps, max_stops, fuel_at_start_of_stint, fuel_consumption):
    if num_laps <= 0:
        return [[]]

    if num_laps in cached_strategies:
        return cached_strategies[num_laps]

    strategies = []
    tires_to_use = ["s"]
    if num_laps > stint_lengths["s"]:
        tires_to_use.append("m")
    if num_laps > stint_lengths["m"]:
        tires_to_use.append("h")

    for tire in tires_to_use:
        laps_in_stint = min(stint_lengths[tire], num_laps)
        additional_fuel = 0
        fuel_consumed_in_stint = round(laps_in_stint * fuel_consumption, 2)
        if fuel_consumed_in_stint > fuel_at_start_of_stint:
            additional_fuel = min(
                100.0 - fuel_at_start_of_stint,
                num_laps * fuel_consumption - fuel_at_start_of_stint,
            )

        fuel_after_stint = round(
            fuel_at_start_of_stint + additional_fuel - fuel_consumed_in_stint, 2
        )

        current_strategies = find_strategies(
            num_laps - laps_in_stint, max_stops, fuel_after_stint, fuel_consumption
        )
        for strat in current_strategies:
            if len(strat) > max_stops or fuel_after_stint < 0:
                continue
            strategies.append(
                [
                    (
                        tire,
                        laps_in_stint,
                        fuel_at_start_of_stint + additional_fuel,
                        additional_fuel > 0,
                    )
                ]
                + strat
            )

    cached_strategies[num_laps] = strategies
    return strategies


def main():
    parser = argparse.ArgumentParser(
        description="Calculate possible tire strategies for a race."
    )
    parser.add_argument(
        "-w",
        "--wear-rate",
        type=float,
        help="Wear rate per lap (e.g., 0.05 for 5% or 5 for 5%)",
    )
    parser.add_argument(
        "-t",
        "--tire-type",
        choices=["s", "m", "h"],
        help="Tire type the wear rate applies to",
    )
    parser.add_argument(
        "-l", "--laps", type=int, help="Total number of laps in the race"
    )
    parser.add_argument(
        "-m",
        "--max-stops",
        type=int,
        default=3,
        help="Maximum number of pit stops allowed",
    )
    parser.add_argument(
        "-f",
        "--fuel-consumption",
        type=float,
        help="Fuel consumption per lap (percentage, e.g., 2 for 2%)",
    )
    parser.add_argument(
        "-W",
        "--target-wear",
        type=float,
        default=70.0,
        help="Target tire wear percentage to pit at (default: 70)",
    )

    args = parser.parse_args()

    if args.wear_rate <= 0:
        print("Error: Wear rate must be positive.")
        sys.exit(1)

    strategies = calculate_strategies(
        args.wear_rate,
        args.target_wear,
        args.tire_type,
        args.laps,
        args.max_stops,
        args.fuel_consumption,
    )
    print_strategies(strategies, args.target_wear, args.wear_rate, args.tire_type)


# Maintain direct entrypoint for manual data entry
if __name__ == "__main__":
    main()
