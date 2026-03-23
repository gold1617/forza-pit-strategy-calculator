import socket
import struct
import copy
import time

DASH_FIELDS = [
    "IsRaceOn",
    "TimestampMS",
    "EngineMaxRpm",
    "EngineIdleRpm",
    "CurrentEngineRpm",
    "AccelerationX",
    "AccelerationY",
    "AccelerationZ",
    "VelocityX",
    "VelocityY",
    "VelocityZ",
    "AngularVelocityX",
    "AngularVelocityY",
    "AngularVelocityZ",
    "Yaw",
    "Pitch",
    "Roll",
    "NormalizedSuspensionTravelFrontLeft",
    "NormalizedSuspensionTravelFrontRight",
    "NormalizedSuspensionTravelRearLeft",
    "NormalizedSuspensionTravelRearRight",
    "TireSlipRatioFrontLeft",
    "TireSlipRatioFrontRight",
    "TireSlipRatioRearLeft",
    "TireSlipRatioRearRight",
    "WheelRotationSpeedFrontLeft",
    "WheelRotationSpeedFrontRight",
    "WheelRotationSpeedRearLeft",
    "WheelRotationSpeedRearRight",
    "WheelOnRumbleStripFrontLeft",
    "WheelOnRumbleStripFrontRight",
    "WheelOnRumbleStripRearLeft",
    "WheelOnRumbleStripRearRight",
    "WheelInPuddleDepthFrontLeft",
    "WheelInPuddleDepthFrontRight",
    "WheelInPuddleDepthRearLeft",
    "WheelInPuddleDepthRearRight",
    "SurfaceRumbleFrontLeft",
    "SurfaceRumbleFrontRight",
    "SurfaceRumbleRearLeft",
    "SurfaceRumbleRearRight",
    "TireSlipAngleFrontLeft",
    "TireSlipAngleFrontRight",
    "TireSlipAngleRearLeft",
    "TireSlipAngleRearRight",
    "TireCombinedSlipFrontLeft",
    "TireCombinedSlipFrontRight",
    "TireCombinedSlipRearLeft",
    "TireCombinedSlipRearRight",
    "SuspensionTravelMetersFrontLeft",
    "SuspensionTravelMetersFrontRight",
    "SuspensionTravelMetersRearLeft",
    "SuspensionTravelMetersRearRight",
    "CarOrdinal",
    "CarClass",
    "CarPerformanceIndex",
    "DrivetrainType",
    "NumCylinders",
    "PositionX",
    "PositionY",
    "PositionZ",
    "Speed",
    "Power",
    "Torque",
    "TireTempFrontLeft",
    "TireTempFrontRight",
    "TireTempRearLeft",
    "TireTempRearRight",
    "Boost",
    "Fuel",
    "DistanceTraveled",
    "BestLap",
    "LastLap",
    "CurrentLap",
    "CurrentRaceTime",
    "LapNumber",
    "RacePosition",
    "Accel",
    "Brake",
    "Clutch",
    "HandBrake",
    "Gear",
    "Steer",
    "NormalizedDrivingLine",
    "NormalizedAIBrakeDifference",
    "TireWearFrontLeft",
    "TireWearFrontRight",
    "TireWearRearLeft",
    "TireWearRearRight",
    "TrackOrdinal",
]

DASH_FORMAT = "<iI27f4i20f5i17fH6B3b4fi"
DASH_PACKET_SIZE = struct.calcsize(DASH_FORMAT)


def parse_packet(data):
    if len(data) >= DASH_PACKET_SIZE:
        parsed_data = struct.unpack(DASH_FORMAT, data[:DASH_PACKET_SIZE])
        return dict(zip(DASH_FIELDS, parsed_data))
    return None


def _update_avg(current_avg, delta, laps_averaged):
    total_consumption = (current_avg * (laps_averaged - 1)) + delta
    return total_consumption / laps_averaged


def collect_telemetry(host="0.0.0.0", port=36792, timeout_seconds=60.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    sock.settimeout(timeout_seconds)

    print(f"Listening for Forza telemetry on {host}:{port}...")
    print(
        f"Drive some practice laps! Collection will stop automatically after {timeout_seconds} seconds of inactivity. Press Ctrl+C to stop manually."
    )

    last_valid_receive_ms = None
    start_of_lap_data = None
    last_data_packet = None
    wear_rate_fl = 0
    wear_rate_fr = 0
    wear_rate_rl = 0
    wear_rate_rr = 0
    avg_fuel_per_lap = 0
    laps_averaged = 0
    lap = 0

    try:
        while True:
            data, addr = sock.recvfrom(2048)
            packet = parse_packet(data)

            if packet and packet["IsRaceOn"] == 1 and packet["DistanceTraveled"] >= 0:
                lap = int(packet["LapNumber"])
                last_valid_receive_ms = packet["TimestampMS"]

                # Detect race restarts or rewinds
                if start_of_lap_data and lap < int(start_of_lap_data["LapNumber"]):
                    print(
                        f"\nSession restart detected (Lap {lap} < {int(start_of_lap_data['LapNumber'])}). Resetting data..."
                    )
                    start_of_lap_data = None
                    wear_rate_fl = wear_rate_fr = wear_rate_rl = wear_rate_rr = 0
                    avg_fuel_per_lap = 0
                    laps_averaged = 0

                # New lap detected
                if (
                    not last_data_packet
                    or packet["LapNumber"] > last_data_packet["LapNumber"]
                ):
                    if (
                        start_of_lap_data
                        and start_of_lap_data["LapNumber"]
                        == last_data_packet["LapNumber"]
                    ):
                        laps_averaged = laps_averaged + 1
                        delta_fl = (
                            last_data_packet["TireWearFrontLeft"]
                            - start_of_lap_data["TireWearFrontLeft"]
                        )
                        delta_fr = (
                            last_data_packet["TireWearFrontRight"]
                            - start_of_lap_data["TireWearFrontRight"]
                        )
                        delta_rl = (
                            last_data_packet["TireWearRearLeft"]
                            - start_of_lap_data["TireWearRearLeft"]
                        )
                        delta_rr = (
                            last_data_packet["TireWearRearRight"]
                            - start_of_lap_data["TireWearRearRight"]
                        )

                        # Fuel goes down over a lap, so delta is start - end
                        delta_fuel = (
                            start_of_lap_data["Fuel"] - last_data_packet["Fuel"]
                        )

                        wear_rate_fl = _update_avg(
                            wear_rate_fl, delta_fl, laps_averaged
                        )
                        wear_rate_fr = _update_avg(
                            wear_rate_fr, delta_fr, laps_averaged
                        )
                        wear_rate_rl = _update_avg(
                            wear_rate_rl, delta_rl, laps_averaged
                        )
                        wear_rate_rr = _update_avg(
                            wear_rate_rr, delta_rr, laps_averaged
                        )
                        avg_fuel_per_lap = _update_avg(
                            avg_fuel_per_lap, delta_fuel, laps_averaged
                        )

                        print(f"--- Lap {lap} Completed ---")
                        print(
                            f"  Lap Fuel Used: {delta_fuel*100:.3f}% | New Moving Avg: {avg_fuel_per_lap*100:.3f}%"
                        )
                        print(
                            f"  Lap Wear (FL/FR/RL/RR): {delta_fl*100:.3f}% / {delta_fr*100:.3f}% / {delta_rl*100:.3f}% / {delta_rr*100:.3f}%"
                        )
                        print(
                            f"  New Moving Avg Max Wear: {max(wear_rate_fl, wear_rate_fr, wear_rate_rl, wear_rate_rr)*100:.3f}%\n"
                        )

                    start_of_lap_data = copy.copy(packet)

                last_data_packet = copy.copy(packet)
            else:
                if packet and last_valid_receive_ms:
                    # Calculate diff with 32-bit unsigned wrap protection
                    diff_ms = (packet["TimestampMS"] - last_valid_receive_ms) & 0xFFFFFFFF
                    if diff_ms > (timeout_seconds * 1000):
                        # print(f"\nNo telemetry received for {diff_ms} ms. Stopping data collection.")
                        raise socket.timeout

    except socket.timeout:
        print(f"\nNo telemetry received for {timeout_seconds} seconds. Stopping data collection.")
    except KeyboardInterrupt:
        print("\nCollection stopped manually.")

    sock.close()

    if (
        wear_rate_fl == 0
        and wear_rate_fr == 0
        and wear_rate_rl == 0
        and wear_rate_rr == 0
    ):
        print("Error: Not enough data.")
        return None, None

    print(f"Recorded {laps_averaged} laps of data.")

    max_wear_rate = max(wear_rate_fl, wear_rate_fr, wear_rate_rl, wear_rate_rr)

    # Check if we need to scale from float (0.0 to 1.0 scale)
    if 0.0 < max_wear_rate < 1.0:
        max_wear_rate *= 100.0
    if 0.0 < avg_fuel_per_lap < 1.0:
        avg_fuel_per_lap *= 100.0

    return max_wear_rate, avg_fuel_per_lap
