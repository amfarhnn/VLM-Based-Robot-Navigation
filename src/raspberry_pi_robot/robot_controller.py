"""Basic Raspberry Pi 4 prompt-engineered robot navigation prototype.

The first physical milestone uses a large green, blue, or yellow marker as a
repeatable indoor landmark. The Raspberry Pi selects a restricted action while
the ESP32 remains responsible for obstacle, sensor-fault, and timeout safety.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import serial
from serial.tools import list_ports


ACTION_TO_COMMAND = {
    "move_forward": "FWD",
    "turn_left": "LEFT",
    "turn_right": "RIGHT",
    "search": "SEARCH",
    "stop": "STOP",
}

HSV_RANGES = {
    "green marker": ((35, 70, 50), (85, 255, 255)),
    "blue marker": ((90, 70, 50), (130, 255, 255)),
    "yellow marker": ((20, 80, 80), (35, 255, 255)),
}


@dataclass
class Goal:
    instruction: str
    target: str | None
    landmarks: list[str]
    spatial_relation: str | None
    action_goal: str
    uncertainty: str


@dataclass
class TargetDetection:
    label: str
    score: float
    center_x: float
    area_ratio: float


def parse_instruction(instruction: str) -> Goal:
    """Convert a simple instruction into the project's fixed prompt schema."""
    normalized = instruction.lower().strip()
    target = next((label for label in HSV_RANGES if label in normalized), None)
    if not target:
        return Goal(
            instruction=instruction,
            target=None,
            landmarks=[],
            spatial_relation=None,
            action_goal="stop because the target is unsupported or unclear",
            uncertainty="high",
        )
    return Goal(
        instruction=instruction,
        target=target,
        landmarks=[target],
        spatial_relation=None,
        action_goal=f"find and approach the {target}",
        uncertainty="low",
    )


def find_marker(frame: Any, target: str | None) -> TargetDetection | None:
    if target not in HSV_RANGES:
        return None
    lower, upper = HSV_RANGES[target]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    frame_height, frame_width = frame.shape[:2]
    if area < 800:
        return None
    x, _, width, height = cv2.boundingRect(contour)
    return TargetDetection(
        label=target,
        score=min(1.0, area / (frame_width * frame_height * 0.15)),
        center_x=(x + width / 2) / frame_width,
        area_ratio=(width * height) / (frame_width * frame_height),
    )


def discover_esp32_device() -> str:
    candidates = [
        port.device
        for port in list_ports.comports()
        if any(name in (port.description or "").lower() for name in ("cp210", "ch340", "usb serial", "uart"))
    ]
    if len(candidates) == 1:
        return candidates[0]
    raise RuntimeError(
        "Unable to uniquely identify the ESP32 USB serial device. "
        "Run `python3 -m serial.tools.list_ports -v` and pass --serial-device."
    )


class Esp32Bridge:
    def __init__(self, device: str | None, baud: int) -> None:
        self.device = device or discover_esp32_device()
        self.port = serial.Serial(self.device, baudrate=baud, timeout=0)
        self.buffer = ""
        self.latest_sensor: dict[str, Any] = {}

    def poll(self) -> dict[str, Any]:
        waiting = self.port.in_waiting
        if waiting:
            self.buffer += self.port.read(waiting).decode("utf-8", errors="ignore")
        while "\n" in self.buffer:
            raw, self.buffer = self.buffer.split("\n", 1)
            raw = raw.strip()
            if not raw.startswith("{"):
                continue
            try:
                self.latest_sensor = json.loads(raw)
            except json.JSONDecodeError:
                continue
        return self.latest_sensor

    def send(self, command: str) -> None:
        self.port.write(f"{command}\n".encode("ascii"))
        self.port.flush()

    def close(self) -> None:
        self.send("STOP")
        self.port.close()


def choose_action(
    goal: Goal,
    target: TargetDetection | None,
    sensors: dict[str, Any],
    stop_area_ratio: float,
) -> tuple[str, str]:
    if goal.uncertainty == "high":
        return "stop", "instruction target is unsupported or unclear"
    if not sensors or "obstacle" not in sensors:
        return "stop", "ESP32 sensor status is unavailable"
    if sensors.get("sensor_fault") is True:
        return "stop", "ESP32 reports unavailable ultrasonic sensing"
    if sensors.get("obstacle") is True:
        return "stop", "ESP32 reports a front obstacle"
    if target is None:
        return "search", "target is not visible"
    if target.area_ratio >= stop_area_ratio:
        return "stop", "target occupies the goal-size image area"
    if target.center_x < 0.40:
        return "turn_left", "target is left of image centre"
    if target.center_x > 0.60:
        return "turn_right", "target is right of image centre"
    return "move_forward", "target is centred and not yet close"


def append_log(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instruction", default="find the green marker")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--serial-device", help="Example: /dev/ttyUSB0 or /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--stop-area-ratio", type=float, default=0.32)
    parser.add_argument("--loop-delay", type=float, default=0.20)
    parser.add_argument("--log", type=Path, default=Path("logs/raspberry_pi_navigation.jsonl"))
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Enable motor commands. Without this flag, the controller always sends STOP.",
    )
    args = parser.parse_args()

    goal = parse_instruction(args.instruction)
    print(json.dumps({"structured_goal": asdict(goal)}, indent=2))

    bridge = Esp32Bridge(args.serial_device, args.baud)
    print(f"Using ESP32 serial device: {bridge.device}")
    camera = cv2.VideoCapture(args.camera)
    if not camera.isOpened():
        bridge.close()
        raise RuntimeError(f"Unable to open camera index {args.camera}")

    try:
        while True:
            started = time.perf_counter()
            ok, frame = camera.read()
            if not ok:
                bridge.send("STOP")
                raise RuntimeError("Camera frame capture failed")

            sensors = bridge.poll()
            target = find_marker(frame, goal.target)
            action, reason = choose_action(goal, target, sensors, args.stop_area_ratio)
            command = ACTION_TO_COMMAND[action] if args.execute else "STOP"
            bridge.send(command)

            record = {
                "timestamp": time.time(),
                "goal": asdict(goal),
                "detection": asdict(target) if target else None,
                "sensors": sensors,
                "selected_action": action,
                "sent_command": command,
                "reason": reason,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "execute_enabled": args.execute,
            }
            append_log(args.log, record)
            print(json.dumps(record, separators=(",", ":")))
            time.sleep(args.loop_delay)
    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        bridge.close()


if __name__ == "__main__":
    main()
