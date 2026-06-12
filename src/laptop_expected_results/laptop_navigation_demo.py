"""Laptop-only expected-results demo using a coloured target and webcam.

This is not a physical robot approach. It displays the movement instruction
that a person should follow while manually moving the laptop.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np


HSV_RANGES = {
    "green": ((35, 70, 50), (85, 255, 255)),
    "blue": ((90, 70, 50), (130, 255, 255)),
    "yellow": ((20, 80, 80), (35, 255, 255)),
}


def parse_instruction(instruction: str) -> dict[str, object]:
    normalized = instruction.lower()
    target = next((colour for colour in HSV_RANGES if colour in normalized), None)
    uncertainty = "low" if target else "high"
    return {
        "target": f"{target} marker" if target else None,
        "landmarks": [f"{target} marker"] if target else [],
        "spatial_relation": None,
        "action_goal": f"find and approach the {target} marker" if target else "stop",
        "suggested_action": "search" if target else "stop",
        "uncertainty": uncertainty,
    }


def select_action(mask: np.ndarray) -> tuple[str, tuple[int, int, int, int] | None]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "SEARCH: rotate or move laptop slowly", None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < 800:
        return "SEARCH: target detection is too small", None

    x, y, width, height = cv2.boundingRect(contour)
    frame_height, frame_width = mask.shape
    center_x = (x + width / 2) / frame_width
    area_ratio = width * height / (frame_width * frame_height)
    if area_ratio >= 0.32:
        action = "STOP: expected goal reached"
    elif center_x < 0.40:
        action = "TURN LEFT: move laptop left"
    elif center_x > 0.60:
        action = "TURN RIGHT: move laptop right"
    else:
        action = "MOVE FORWARD: carry laptop forward"
    return action, (x, y, width, height)


def append_log(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instruction", default="find the green marker")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--log", type=Path, default=Path("logs/laptop_expected_results.jsonl"))
    args = parser.parse_args()

    goal = parse_instruction(args.instruction)
    print(json.dumps({"structured_goal": goal}, indent=2))
    target = str(goal["target"] or "").split()[0]
    if target not in HSV_RANGES:
        raise SystemExit("Instruction must contain green, blue, or yellow.")

    camera = cv2.VideoCapture(args.camera)
    if not camera.isOpened():
        raise RuntimeError(f"Unable to open camera index {args.camera}")

    lower, upper = HSV_RANGES[target]
    last_action = None
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("Camera frame capture failed")
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            action, box = select_action(mask)
            if box:
                x, y, width, height = box
                cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
            cv2.putText(frame, action, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Laptop Expected-Results Navigation Demo", frame)
            if action != last_action:
                append_log(args.log, {"timestamp": time.time(), "goal": goal, "displayed_action": action})
                last_action = action
            if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
