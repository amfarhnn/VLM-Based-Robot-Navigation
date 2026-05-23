# Approach 1 Guide: Raspberry Pi + ESP32 + Webcam + Remote GPU PC

This approach uses a small robot with a Raspberry Pi on the robot and a GPU laptop or desktop on the same WiFi network. The Raspberry Pi handles the webcam, serial communication, local safety checks, and command routing. The GPU computer runs the heavy AI model for prompt processing, visual grounding, or VLM-based action selection.

This is the most practical approach when the navigation model is too heavy for a low-cost onboard board.

## 1. Purpose

The purpose of this setup is to build a real mobile robot while avoiding the cost and complexity of running the full model onboard. The robot still has physical movement, obstacle detection, and camera input, but the GPU workload is moved to a laptop or PC.

This approach is suitable for:

- testing real robot movement
- testing real webcam input from the robot viewpoint
- using a larger model on a GPU laptop or desktop
- reducing onboard compute cost
- keeping the robot hardware simple

The main limitation is that the robot depends on WiFi. If the connection is slow or unstable, the response time may increase.

## 2. Hardware Components

| Component | Role |
|---|---|
| Raspberry Pi | Onboard robot computer for camera capture, serial communication, safety validation, and network client |
| USB webcam | Captures the robot's front view |
| ESP32 | Controls the motor driver and reads ultrasonic sensors |
| Motor driver | Drives the DC motors according to ESP32 output |
| DC motors and chassis | Mobile robot platform |
| Ultrasonic sensors | Detect nearby obstacles |
| GPU laptop or desktop | Runs the AI model server |
| Battery pack | Powers the robot electronics and motors |
| Voltage regulators | Provide stable voltage for Raspberry Pi, ESP32, and motor driver |
| Main power switch | Allows quick manual shutdown |

Suggested motor driver options:

- TB6612FNG for small DC motors
- L298N for simple low-cost testing, although it is less efficient
- BTS7960 for higher-current motors

Suggested ultrasonic layout:

- Front sensor
- Left sensor
- Right sensor
- Rear sensor

## 3. High-Level Architecture

```text
User instruction
        |
        v
Raspberry Pi onboard client
        |
        +--> USB webcam frame capture
        |
        +--> ESP32 obstacle status over serial
        |
        +--> Send instruction + image to GPU server over WiFi
                        |
                        v
              GPU laptop/PC model server
                        |
                        v
              Structured navigation output
                        |
                        v
Raspberry Pi validates model output
        |
        +--> If unsafe: send STOP to ESP32
        |
        +--> If safe: send action command to ESP32
                        |
                        v
              ESP32 controls motor driver
                        |
                        v
                  Robot movement
```

## 4. Data Flow

The robot should use a simple request and response format.

Raspberry Pi sends this to the GPU server:

```json
{
  "instruction": "Go to the door",
  "image": "base64_encoded_jpeg",
  "allowed_actions": ["move_forward", "turn_left", "turn_right", "stop", "search"],
  "sensor_status": {
    "front_cm": 80.0,
    "left_cm": 45.0,
    "right_cm": 50.0,
    "rear_cm": 90.0,
    "obstacle": false
  }
}
```

GPU server returns:

```json
{
  "target": "door",
  "landmarks": ["door"],
  "spatial_relation": null,
  "action_goal": "find and move toward the door",
  "suggested_action": "move_forward",
  "uncertainty": "low",
  "reason": "The instruction asks the robot to approach a door and the path is clear."
}
```

The Raspberry Pi must validate the response before sending a motor command.

## 5. Software Stack

### Raspberry Pi

Recommended software:

- Raspberry Pi OS 64-bit
- Python 3.10 or newer
- OpenCV for webcam capture
- pyserial for ESP32 serial communication
- requests or httpx for GPU server communication
- JSON logging

Suggested packages:

```bash
pip install opencv-python pyserial requests
```

If OpenCV installation is heavy on the Pi, use:

```bash
pip install opencv-python-headless
```

### GPU Laptop or PC

Recommended software:

- Windows or Linux with NVIDIA GPU
- Python 3.10 or newer
- CUDA-compatible PyTorch if using local models
- FastAPI or Flask for the model server
- OpenCV or PIL for image decoding
- transformers, open_clip_torch, or the selected VLM library

Example packages:

```bash
pip install fastapi uvicorn pillow opencv-python torch torchvision transformers open_clip_torch
```

The exact packages depend on the selected model. If using an API model, the GPU server can be replaced by an API bridge.

### ESP32

Recommended software:

- Arduino IDE, PlatformIO, or ESP-IDF
- Firmware that reads ultrasonic sensors
- Firmware that accepts serial motor commands

Suggested ESP32 command protocol:

| Command | Meaning |
|---|---|
| `FWD` | Move forward |
| `LEFT` | Turn left |
| `RIGHT` | Turn right |
| `SEARCH` | Rotate slowly to search |
| `STOP` | Stop motors |
| `PING` | Check connection |

Suggested ESP32 sensor JSON:

```json
{
  "front_cm": 50.2,
  "left_cm": 40.0,
  "right_cm": 60.3,
  "rear_cm": 90.0,
  "min_cm": 40.0,
  "obstacle": false
}
```

## 6. Suggested Code Structure

```text
src/
  raspberry_pi_robot/
    robot_client.py
    camera.py
    esp32_serial.py
    safety.py
    config.example.json
    logs/
  gpu_server/
    server.py
    model_runner.py
    prompt_templates.py
    config.example.json
firmware/
  esp32_robot_controller/
    esp32_robot_controller.ino
```

### Raspberry Pi Modules

| File | Purpose |
|---|---|
| `robot_client.py` | Main loop: read instruction, capture frame, call GPU server, validate output, send command |
| `camera.py` | Webcam capture using OpenCV |
| `esp32_serial.py` | Read ultrasonic JSON and send motor commands |
| `safety.py` | Validate action, uncertainty, allowed action set, and obstacle status |
| `config.example.json` | Stores webcam index, serial port, server URL, safety threshold, and log path |

### GPU Server Modules

| File | Purpose |
|---|---|
| `server.py` | FastAPI endpoint that receives instruction and image |
| `model_runner.py` | Runs CLIP, VLM, LLM, or rule-based fallback |
| `prompt_templates.py` | Stores structured prompt templates and output schema |

## 7. Raspberry Pi Control Logic

```text
Start robot client
Load configuration
Open webcam
Open serial connection to ESP32
Loop:
    receive or enter user instruction
    capture webcam frame
    read latest ESP32 ultrasonic status
    send instruction, frame, and sensor status to GPU server
    receive structured navigation output
    validate output:
        required fields exist
        suggested_action is in approved action set
        uncertainty is not high
        obstacle is not detected for moving actions
    if valid:
        send mapped command to ESP32
    else:
        send STOP to ESP32
    log instruction, sensor status, model output, final action, and latency
```

Approved actions:

```text
move_forward, turn_left, turn_right, stop, search
```

Action mapping:

| Model Action | ESP32 Command |
|---|---|
| `move_forward` | `FWD` |
| `turn_left` | `LEFT` |
| `turn_right` | `RIGHT` |
| `stop` | `STOP` |
| `search` | `SEARCH` |

## 8. GPU Server Flow

```text
Start FastAPI server
Load selected model
Receive instruction and image from Raspberry Pi
Decode image
Run prompt parser and visual grounding or VLM action-choice logic
Return structured JSON output
```

The server should always return a safe JSON response. If the model fails, it should return:

```json
{
  "target": null,
  "landmarks": [],
  "spatial_relation": null,
  "action_goal": "model failed or uncertain",
  "suggested_action": "stop",
  "uncertainty": "high",
  "reason": "The model response could not be parsed safely."
}
```

## 9. Setup Procedure

### Step 1: Assemble Robot Hardware

1. Mount the Raspberry Pi on the chassis.
2. Mount the ESP32 near the motor driver and ultrasonic sensor wiring.
3. Mount the webcam at the front of the robot.
4. Mount the ultrasonic sensors at front, left, right, and rear positions.
5. Connect ESP32 GPIO pins to the motor driver input pins.
6. Connect motor driver outputs to the motors.
7. Connect ultrasonic trigger and echo pins to ESP32 GPIO pins.
8. Use voltage dividers or level shifters if the ultrasonic echo signal is 5 V.
9. Connect all grounds together.
10. Add a main power switch.

### Step 2: Flash ESP32 Firmware

The ESP32 firmware should:

1. Read ultrasonic sensors every 100 ms.
2. Publish distance JSON over serial.
3. Listen for motor commands.
4. Stop motors if no command is received for a timeout period.
5. Stop motors if the front distance is below the safety threshold.

### Step 3: Configure Raspberry Pi

1. Install Raspberry Pi OS.
2. Enable SSH if needed.
3. Connect the Pi to the same WiFi network as the GPU computer.
4. Install Python packages.
5. Test the webcam with OpenCV.
6. Test the ESP32 serial connection.
7. Confirm the Pi can reach the GPU server IP address.

### Step 4: Configure GPU Server

1. Install Python and GPU model dependencies.
2. Start the server on the laptop or desktop.
3. Check that the server is reachable from the Pi.
4. Test the endpoint with one saved image and instruction.

Example server URL:

```text
http://192.168.1.50:8000/navigate
```

### Step 5: Run End-to-End Test

1. Start the ESP32.
2. Start the GPU model server.
3. Start the Raspberry Pi robot client.
4. Use `dry_run` mode first, where commands are printed but motors do not move.
5. Test instructions such as:
   - `Go to the door`
   - `Find the signboard`
   - `Move toward the chair near the table`
   - `Stop at the door`
6. Enable real motor output only after dry-run results are safe.

## 10. Testing Plan

| Test | Expected Result |
|---|---|
| Webcam capture test | Pi captures image successfully |
| ESP32 sensor test | Pi receives valid ultrasonic JSON |
| ESP32 motor command test | ESP32 responds to `FWD`, `LEFT`, `RIGHT`, `SEARCH`, `STOP` |
| GPU server connection test | Pi receives structured JSON from server |
| Prompt parsing test | Model extracts target and action fields |
| Safety validation test | Robot stops for high uncertainty or obstacle |
| Latency test | Instruction-to-command delay is acceptable |
| Full robot test | Robot performs basic movement in controlled indoor area |

## 11. Safety Rules

The Raspberry Pi should force `STOP` when:

- model output is not valid JSON
- required fields are missing
- `suggested_action` is not in the approved action set
- `uncertainty` is `high`
- obstacle is detected and action is movement-related
- GPU server timeout occurs
- ESP32 serial connection is lost

The ESP32 should also stop motors when:

- no command is received within a short timeout
- front ultrasonic reading is below the local safety threshold
- unknown command is received

This double safety layer is important because WiFi and model inference can fail.

## 12. Advantages and Limitations

Advantages:

- Real robot testing is possible.
- Heavy model inference runs on a GPU.
- Raspberry Pi is easier to obtain than specialized AI boards.
- System can support larger models than an embedded board.
- Good match for early FYP prototype testing.

Limitations:

- Requires reliable WiFi.
- Latency may be higher than onboard inference.
- Robot depends on an external computer.
- GPU server setup may be complex.
- Not fully standalone.

## 13. Recommended Use in the Project

This approach is recommended as the main practical robot approach if the selected model cannot run onboard. It gives the project a real mobile robot, real camera viewpoint, real obstacle sensing, and enough compute for modern VLM or CLIP-style experiments.

For the methodology chapter, this approach can be described as:

```text
The physical robot uses an onboard Raspberry Pi for sensor communication and command validation, while the GPU laptop or desktop performs model inference over WiFi. This reduces onboard compute requirements while preserving real robot testing.
```

