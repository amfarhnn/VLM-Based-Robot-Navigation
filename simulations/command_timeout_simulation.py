"""Expected command-timeout logic used for the FYP1 Chapter 4 simulation.

This is an assumption-based logic simulation, not a measured physical result.
FYP2 testing must verify the repeated physical stop response.
"""

from __future__ import annotations

import csv
from pathlib import Path


COMMAND_TIMEOUT_MS = 1000
OUTPUT_PATH = Path(__file__).with_name("command_timeout_results.csv")


def expected_motor_state(elapsed_ms: int) -> str:
    """Return the expected motor state after the last valid command."""
    return "STOP" if elapsed_ms > COMMAND_TIMEOUT_MS else "COMMANDED_MOTION_AVAILABLE"


def main() -> None:
    elapsed_times = range(0, 1601, 100)
    rows: list[tuple[int, str]] = []

    for elapsed_ms in elapsed_times:
        state = expected_motor_state(elapsed_ms)
        rows.append((elapsed_ms, state))
        print(f"{elapsed_ms:>4} ms -> {state}")

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["elapsed_ms", "expected_motor_state"])
        writer.writerows(rows)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
