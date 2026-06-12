"""Basic Coral Dev Board prompt-engineered robot navigation prototype.

The first prototype intentionally supports simple goals that are labels in the
selected Edge TPU detector, such as "find the chair". The Coral chooses a safe
action from a fixed set; the ESP32 remains responsible for obstacle and timeout
safety.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ACTION_TO_COMMAND = {
    "move_forward": "FWD",
    "turn_left": "LEFT",
    "turn_right": "RIGHT",
    "search": "SEARCH",
    "stop": "STOP",
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


def parse_instruction(instruction: str, available_labels: set[str]) -> Goal:
    """Convert a simple instruction into the project's fixed prompt schema."""
    normalized = instruction.lower().strip()
    targets = sorted(
        (label for label in available_labels if label and label in normalized),
        key=len,
        reverse=True,
    )
    target = targets[0] if targets else None
    if not target:
        return Goal(
            instruction=instruction,
            target=None,
            landmarks=[],
            spatial_relation=None,
            action_goal="stop because the target is unsupported or unclear",
            uncertainty="high",
        )

    relation = None
    for phrase in ("near", "beside", "left of", "right of", "in front of"):
        if phrase in normalized:
            relation = phrase
            break

    return Goal(
        instruction=instruction,
        target=target,
        landmarks=[target],
        spatial_relation=relation,
        action_goal=f"find and approach the {target}",
        uncertainty="low",
    )


class EdgeTpuDetector:
    def __init__(self, model_path: Path, labels_path: Path, threshold: float) -> None:
        import cv2
        from pycoral.adapters import common, detect
        from pycoral.utils.dataset import read_label_file
        from pycoral.utils.edgetpu import make_interpreter

        self.cv2 = cv2
        self.common = common
        self.detect = detect
        self.interpreter = make_interpreter(str(model_path))
        self.interpreter.allocate_tensors()
        self.labels = read_label_file(str(labels_path))
        self.threshold = threshold
        self.input_size = self.common.input_size(self.interpreter)

    @property
    def available_labels(self) -> set[str]:
        return {str(value).lower() for value in self.labels.values()}

    def find_target(self, frame: Any, target: str | None) -> TargetDetection | None:
        if not target:
            return None

        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        resized = self.cv2.resize(rgb, self.input_size)
        self.common.set_input(self.interpreter, resized)
        self.interpreter.invoke()

        width, height = self.input_size
        matches: list[TargetDetection] = []
        for item in self.detect.get_objects(self.interpreter, self.threshold):
            label = str(self.labels.get(item.id, item.id)).lower()
            if label != target:
                continue
            bbox = item.bbox
            matches.append(
                TargetDetection(
                    label=label,
                    score=float(item.score),
                    center_x=float((bbox.xmin + bbox.xmax) / 2 / width),
                    area_ratio=float(bbox.width * bbox.height / (width * height)),
                )
            )
        return max(matches, key=lambda item: item.score, default=None)


class Esp32Bridge:
    def __init__(self, device: str, baud: int) -> None:
        import serial

        self.port = serial.Serial(device, baudrate=baud, timeout=0)
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
    if sensors.get("front_left_cm") is None and sensors.get("front_right_cm") is None:
        return "stop", "both ultrasonic readings are unavailable"
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
    import cv2

    parser = argparse.ArgumentParser()
    parser.add_argument("--instruction", required=True, help='For example: "find the chair"')
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--serial-device", default="/dev/ttymxc2")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--stop-area-ratio", type=float, default=0.32)
    parser.add_argument("--loop-delay", type=float, default=0.20)
    parser.add_argument("--log", type=Path, default=Path("logs/coral_navigation.jsonl"))
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Enable motor commands. Without this flag, the controller always sends STOP.",
    )
    args = parser.parse_args()

    detector = EdgeTpuDetector(args.model, args.labels, args.threshold)
    goal = parse_instruction(args.instruction, detector.available_labels)
    print(json.dumps({"structured_goal": asdict(goal)}, indent=2))

    bridge = Esp32Bridge(args.serial_device, args.baud)
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
            target = detector.find_target(frame, goal.target)
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
