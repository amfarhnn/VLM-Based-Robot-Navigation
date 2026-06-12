"""Browser webcam interface for the Docker laptop expected-results demo."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from threading import Lock

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request

from laptop_navigation_demo import HSV_RANGES, append_log, parse_instruction, select_action


app = Flask(__name__)
LOG_PATH = Path("logs/laptop_expected_results.jsonl")
last_actions: dict[str, str] = {}
log_lock = Lock()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/process")
def process_frame():
    instruction = request.form.get("instruction", "find the green marker")
    image_file = request.files.get("frame")
    if image_file is None:
        return jsonify({"error": "frame is required"}), 400

    goal = parse_instruction(instruction)
    target = str(goal["target"] or "").split()[0]
    if target not in HSV_RANGES:
        return jsonify({"goal": goal, "action": "STOP: unsupported target", "error": "Use green, blue, or yellow."})

    image_bytes = np.frombuffer(image_file.read(), dtype=np.uint8)
    frame = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "invalid image frame"}), 400

    lower, upper = HSV_RANGES[target]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    action, box = select_action(mask)

    if box:
        x, y, width, height = box
        cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 3)
    cv2.putText(frame, action, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

    with log_lock:
        if last_actions.get(instruction) != action:
            append_log(
                LOG_PATH,
                {"timestamp": time.time(), "goal": goal, "displayed_action": action, "source": "docker_web"},
            )
            last_actions[instruction] = action

    encoded_ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not encoded_ok:
        return jsonify({"error": "failed to encode result"}), 500

    return jsonify(
        {
            "goal": goal,
            "action": action,
            "annotated_frame": base64.b64encode(encoded.tobytes()).decode("ascii"),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
