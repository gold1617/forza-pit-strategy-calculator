import json
import sys
from src.telemetry.collector import collect_telemetry
from src.strategy.calculator import calculate_strategies, print_strategies


def main():
    print("=== Forza Pit Strategy Automation ===")

    # Load config
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        host = config.get("udp", {}).get("host", "0.0.0.0")
        port = config.get("udp", {}).get("port", 61482)
        timeout_seconds = config.get("udp", {}).get("timeout_seconds", 60.0)
    except Exception as e:
        print(f"Warning: Could not load config.json ({e}). Using defaults.")
        host, port = "0.0.0.0", 61482

    # Step 1: Collect Telemetry
    avg_wear, avg_fuel = collect_telemetry(host, port, timeout_seconds)

    if avg_wear is None or avg_fuel is None:
        print("\nExiting since valid telemetry could not be assessed.")
        sys.exit(1)

    print(f"\nEmpirical Average Wear per Lap:   {avg_wear:.2f}%")
    print(f"Empirical Average Fuel per Lap:   {avg_fuel:.2f}%\n")

    # Step 2: Prompt for required inputs
    print("--- Race Configuration ---")
    tire_type = input("Tire compound used during practice [s/m/h]: ").strip().lower()
    if tire_type not in ["s", "m", "h"]:
        print("Invalid compound. Choose from s, m, or h.")
        sys.exit(1)

    try:
        laps = int(input("Total laps in the race: ").strip())
    except ValueError:
        print("Invalid laps value.")
        sys.exit(1)

    stops_input = input("Max stops allowed (default 3): ").strip()
    max_stops = int(stops_input) if stops_input else 3

    wear_input = input("Target wear percentage to pit at (default 70): ").strip()
    target_wear = float(wear_input) if wear_input else 70.0

    # Step 3: Calculate Strategies
    print("\n--- Strategy Output ---")
    strategies = calculate_strategies(
        avg_wear, target_wear, tire_type, laps, max_stops, avg_fuel
    )
    print_strategies(strategies, target_wear, avg_wear, tire_type)


if __name__ == "__main__":
    main()
