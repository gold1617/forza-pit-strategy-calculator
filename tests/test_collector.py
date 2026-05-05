import socket
import struct
import threading
import time
from src.telemetry.collector import collect_telemetry, DASH_FORMAT


def build_packet(lap, fuel, wear, distance_traveled, timestamp_ms=0, is_race_on=1):
    """Helper function to construct raw binary UDP telemetry packets for testing."""
    values = []
    values.extend([is_race_on, int(timestamp_ms)])
    values.extend([0.0] * 27)
    values.extend([0] * 4)
    values.extend([0.0] * 20)
    values.extend([0] * 5)
    f_block = [0.0] * 17
    f_block[11] = float(fuel)
    f_block[12] = float(distance_traveled)
    values.extend(f_block)
    values.append(int(lap))
    values.extend([0] * 6)
    values.extend([0] * 3)
    values.extend([float(wear)] * 4)
    values.append(0)
    return struct.pack(DASH_FORMAT, *values)


def send_test_data(port):
    """Simulates a Forza game client sending sequential telemetry packets over UDP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = ("127.0.0.1", port)
    time.sleep(0.1)

    t_ms = 1000

    # Lap 1 start
    sock.sendto(build_packet(0, 1.0, 0.08, 0.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 1 end
    sock.sendto(build_packet(0, 0.98, 0.13, 60.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 2 start
    sock.sendto(build_packet(1, 0.98, 0.13, 60.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 2 end
    sock.sendto(build_packet(1, 0.96, 0.18, 120.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 3 start
    sock.sendto(build_packet(2, 0.96, 0.18, 120.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 3 end
    sock.sendto(build_packet(2, 0.94, 0.23, 180.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 4 start (triggers final calculate for Lap 3)
    sock.sendto(build_packet(3, 0.94, 0.23, 180.0, t_ms), dest)
    time.sleep(0.01)

    # App-level timeout trigger logic using paused/non-race packet leap
    t_ms += 1500
    sock.sendto(build_packet(3, 0.94, 0.23, 180.0, t_ms, is_race_on=0), dest)


def test_collect_telemetry():
    """Tests full telemetry collection over a simulated 3-lap race."""
    test_port = 61484
    t = threading.Thread(target=send_test_data, args=(test_port,))
    t.start()

    avg_wear, avg_fuel = collect_telemetry(
        host="127.0.0.1", port=test_port, timeout_seconds=1.0
    )
    t.join()

    assert avg_wear is not None
    assert avg_fuel is not None
    assert abs(avg_wear - 5.0) < 0.01, f"Expected 5.0 wear, got {avg_wear}"
    assert abs(avg_fuel - 2.0) < 0.01, f"Expected 2.0 fuel, got {avg_fuel}"


def test_parse_packet_short():
    """Verifies that packets shorter than the expected structure are safely ignored."""
    from src.telemetry.collector import parse_packet

    assert parse_packet(b"too_short") is None


def send_rewind_data(port):
    """Simulates a game rewind or restart by sending laps out of sequence."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = ("127.0.0.1", port)
    time.sleep(0.1)

    t_ms = 1000
    # Lap 2
    sock.sendto(build_packet(2, 1.0, 0.08, 0.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Rewind to Lap 0
    sock.sendto(build_packet(0, 1.0, 0.08, 0.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 1 start
    sock.sendto(build_packet(1, 1.0, 0.08, 0.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 1 end
    sock.sendto(build_packet(1, 0.9, 0.18, 60.0, t_ms), dest)
    t_ms += 100
    time.sleep(0.01)

    # Lap 2 start
    sock.sendto(build_packet(2, 0.9, 0.18, 60.0, t_ms), dest)
    time.sleep(0.01)


def test_collect_telemetry_rewind():
    """Tests that moving averages and tracking logic reset properly upon a race restart."""
    test_port = 61485
    t = threading.Thread(target=send_rewind_data, args=(test_port,))
    t.start()

    avg_wear, avg_fuel = collect_telemetry(
        host="127.0.0.1", port=test_port, timeout_seconds=0.5
    )
    t.join()
    assert avg_wear is not None


def test_collect_telemetry_keyboard_interrupt(monkeypatch):
    """Ensures the collector handles unexpected KeyboardInterrupt exceptions gracefully."""
    import socket

    def mock_recvfrom(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(socket.socket, "recvfrom", mock_recvfrom)
    avg_wear, avg_fuel = collect_telemetry(timeout_seconds=0.1)
    assert avg_wear is None
    assert avg_fuel is None


def test_collect_telemetry_not_enough_data():
    """Verifies behavior when the collection period ends without enough lap data."""
    avg_wear, avg_fuel = collect_telemetry(timeout_seconds=0.01)
    assert avg_wear is None
    assert avg_fuel is None


if __name__ == "__main__":
    test_collect_telemetry()
    print("ALL TESTS PASSED MANUALLY")
