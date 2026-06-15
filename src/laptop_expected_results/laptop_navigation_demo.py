"""Laptop-only expected-results demo using a specific door and webcam.

This is not a physical robot approach. It displays the movement instruction
that a person should follow while manually moving the laptop.

The default ``find the door`` goal detects the tall grey-blue door used in the
project test area. The lightweight colour-and-shape detector is intentionally
tuned to that door and does not claim general semantic door detection.
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

# Tuned for the project's grey-blue door under indoor corridor lighting.
DOOR_HSV_LOWER = (35, 12, 45)
DOOR_HSV_UPPER = (115, 125, 205)
DOOR_MIN_AREA_RATIO = 0.025
DOOR_MIN_HEIGHT_RATIO = 0.30
DOOR_MIN_ASPECT_RATIO = 1.20
DOOR_MAX_ASPECT_RATIO = 4.50
DOOR_MIN_RECTANGULARITY = 0.35


def parse_instruction(instruction: str) -> dict[str, object]:
    normalized = instruction.lower()
    if "door" in normalized:
        target = "door"
        detector = "grey-blue door colour-and-shape detector"
        grounding_colour = None
        visual_target = "tall grey-blue door"
    else:
        grounding_colour = next((colour for colour in HSV_RANGES if colour in normalized), None)
        target = f"{grounding_colour} marker" if grounding_colour else None
        detector = "colour marker detector" if target else None
        visual_target = target

    uncertainty = "low" if target else "high"
    return {
        "instruction": instruction,
        "target": target,
        "landmarks": [target] if target else [],
        "spatial_relation": None,
        "action_goal": f"find and approach the {target}" if target else "stop",
        "suggested_action": "search" if target else "stop",
        "uncertainty": uncertainty,
        "detector": detector,
        "grounding_colour": grounding_colour,
        "visual_target": visual_target,
    }


def grounding_colour(goal: dict[str, object]) -> str | None:
    colour = goal.get("grounding_colour")
    return str(colour) if colour in HSV_RANGES else None


def detect_door(frame: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int] | None]:
    """Detect the project's tall grey-blue door using colour and geometry."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(DOOR_HSV_LOWER), np.array(DOOR_HSV_UPPER))

    # Remove horizontal floor strips before joining recessed door panels.
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 41)),
    )
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (17, 25)),
        iterations=1,
    )
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 9)),
    )

    frame_height, frame_width = mask.shape
    frame_area = frame_height * frame_width
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_box = None
    best_score = 0.0
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        x, y, width, height = cv2.boundingRect(contour)
        box_area = width * height
        if box_area == 0:
            continue

        area_ratio = box_area / frame_area
        height_ratio = height / frame_height
        aspect_ratio = height / width
        rectangularity = contour_area / box_area
        valid_aspect_ratio = (
            DOOR_MIN_ASPECT_RATIO <= aspect_ratio <= DOOR_MAX_ASPECT_RATIO
            or (area_ratio >= 0.28 and 0.75 <= aspect_ratio <= DOOR_MAX_ASPECT_RATIO)
        )
        reaches_lower_half = y + height > frame_height * 0.48
        begins_above_middle = y < frame_height * 0.55
        if not (
            area_ratio >= DOOR_MIN_AREA_RATIO
            and height_ratio >= DOOR_MIN_HEIGHT_RATIO
            and valid_aspect_ratio
            and rectangularity >= DOOR_MIN_RECTANGULARITY
            and reaches_lower_half
            and begins_above_middle
        ):
            continue

        # Prefer large, solid, vertical candidates without assuming image side.
        vertical_score = min(aspect_ratio / 2.0, 1.0)
        score = area_ratio * 4.0 + rectangularity + height_ratio + vertical_score
        if score > best_score:
            best_score = score
            best_box = (x, y, width, height)

    return mask, best_box


def select_action_from_box(
    frame_shape: tuple[int, ...],
    box: tuple[int, int, int, int] | None,
) -> str:
    if box is None:
        return "SEARCH: rotate or move laptop slowly"

    frame_height, frame_width = frame_shape[:2]
    x, _y, width, height = box
    center_x = (x + width / 2) / frame_width
    area_ratio = width * height / (frame_width * frame_height)
    if area_ratio >= 0.32:
        return "STOP: expected goal reached"
    if center_x < 0.40:
        return "TURN LEFT: move laptop left"
    if center_x > 0.60:
        return "TURN RIGHT: move laptop right"
    return "MOVE FORWARD: carry laptop forward"


def select_action(mask: np.ndarray) -> tuple[str, tuple[int, int, int, int] | None]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "SEARCH: rotate or move laptop slowly", None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < 800:
        return "SEARCH: target detection is too small", None

    x, y, width, height = cv2.boundingRect(contour)
    action = select_action_from_box(mask.shape, (x, y, width, height))
    return action, (x, y, width, height)


def process_navigation_frame(
    frame: np.ndarray,
    goal: dict[str, object],
) -> tuple[str, tuple[int, int, int, int] | None, np.ndarray]:
    if goal.get("target") == "door":
        mask, box = detect_door(frame)
        return select_action_from_box(frame.shape, box), box, mask

    target_colour = grounding_colour(goal)
    if target_colour is None:
        return "STOP: unsupported target", None, np.zeros(frame.shape[:2], dtype=np.uint8)

    lower, upper = HSV_RANGES[target_colour]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    action, box = select_action(mask)
    return action, box, mask


def append_log(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instruction", default="find the door")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--log", type=Path, default=Path("logs/laptop_expected_results.jsonl"))
    args = parser.parse_args()

    goal = parse_instruction(args.instruction)
    print(json.dumps({"structured_goal": goal}, indent=2))
    if goal["target"] is None:
        raise SystemExit("Instruction must contain door, green, blue, or yellow.")

    camera = cv2.VideoCapture(args.camera)
    if not camera.isOpened():
        raise RuntimeError(f"Unable to open camera index {args.camera}")

    last_action = None
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("Camera frame capture failed")
            action, box, _mask = process_navigation_frame(frame, goal)
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
