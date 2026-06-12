"""Expected obstacle-stop logic used for the FYP1 Chapter 4 simulation.

This is an assumption-based logic simulation, not a measured physical result.
The final threshold must be calibrated using the assembled robot during FYP2.
"""

from __future__ import annotations

import csv
from pathlib import Path


SAFE_DISTANCE_CM = 25.0
OUTPUT_PATH = Path(__file__).with_name("obstacle_stop_results.csv")


def expected_response(front_left_cm: float, front_right_cm: float) -> str:
    """Return the expected ESP32 response using the nearest front obstacle."""
    minimum_distance = min(front_left_cm, front_right_cm)
    return "STOP" if minimum_distance < SAFE_DISTANCE_CM else "MOVEMENT_MAY_BE_PERMITTED"


def main() -> None:
    distances = range(0, 61, 5)
    rows: list[tuple[int, int, str]] = []

    for distance_cm in distances:
        response = expected_response(distance_cm, distance_cm)
        rows.append((distance_cm, distance_cm, response))
        print(f"{distance_cm:>2} cm -> {response}")

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["front_left_cm", "front_right_cm", "expected_response"])
        writer.writerows(rows)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
