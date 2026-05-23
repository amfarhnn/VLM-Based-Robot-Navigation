# Approach 2 Guide: Google Dev Board + ESP32 + Webcam

This approach uses a Google Dev Board as the onboard computer and an ESP32 for motor control and ultrasonic sensing. In this guide, "Google Dev Board" is assumed to mean a Google Coral Dev Board or a similar Google Edge TPU development board. If the exact board is different, the same architecture can still be used, but the software installation and model format may need to change.

This is the cleanest embedded approach if the board can run the selected model fast enough.

## 1. Purpose

The purpose of this setup is to build a more standalone mobile robot. Unlike the Raspberry Pi plus remote GPU approach, the model processing is intended to run on the onboard Google Dev Board. The ESP32 handles real-time motor and ultrasonic tasks, while the Google Dev Board handles camera capture, prompt processing, visual grounding, action selection, validation, and logging.

This approach is suitable for:

- testing a more self-contained robot
- reducing dependence on WiFi during navigation
- using an Edge TPU or embedded AI accelerator
- keeping motor timing and ultrasonic reading separate from AI processing

The main limitation is model compatibility. A Google Coral-style Edge TPU usually works best with quantized TensorFlow Lite models. Large VLMs and LLMs may not run directly onboard.

## 2. Hardware Components

| Component | Role |
|---|---|
| Google Dev Board | Onboard AI and robot decision computer |
| USB webcam or supported camera | Captures front-view image |
| ESP32 | Controls motor driver and reads ultrasonic sensors |
| Motor driver | Drives DC motors |
| DC motors and chassis | Mobile robot platform |
| Ultrasonic sensors | Detect obstacles |
| Battery pack | Powers robot |
| Voltage regulators | Provide stable voltage rails |
| Main power switch | Allows quick shutdown |

Suggested ultrasonic sensor positions:

- Front
- Left
- Right
- Rear

Suggested motor commands:

- `FWD`
- `LEFT`
- `RIGHT`
- `SEARCH`
- `STOP`

## 3. High-Level Architecture

```text
User instruction
        |
        v
Google Dev Board
        |
        +--> Camera capture
        |
        +--> Prompt parsing
        |
        +--> Onboard model inference
        |
        +--> Action selection
        |
        +--> Safety validation using ESP32 sensor status
                        |
                        v
              ESP32 motor and sensor controller
                        |
                        +--> Read ultrasonic sensors
                        |
                        +--> Control motor driver
                        |
                        v
                  Robot movement
```

## 4. Model Strategy

This approach depends heavily on what model can run on the Google Dev Board.

### Practical Model Options

| Model Type | Suitability |
|---|---|
| Rule-based prompt parser | Very suitable and lightweight |
| Small local language model | Possible only if the board has enough CPU/RAM and model support |
| TensorFlow Lite image classifier | Suitable |
| TensorFlow Lite object detector | Suitable |
| Edge TPU-compiled TFLite model | Best use of Coral-style board |
| CLIP/OpenCLIP | May be difficult unless using a small optimized model |
| Large VLM | Usually not suitable onboard |
| Remote API or GPU fallback | Optional, but reduces standalone benefit |

For an FYP prototype, a realistic baseline is:

1. Use rule-based or small-model prompt parsing.
2. Use TFLite object detection or classification for visual grounding.
3. Use rule-based safety validation.
4. Send simple motor commands to ESP32.

## 5. Data Flow

The Google Dev Board should create a structured navigation output like this:

```json
{
  "target": "door",
  "landmarks": ["door"],
  "spatial_relation": null,
  "action_goal": "find and move toward the door",
  "suggested_action": "move_forward",
  "uncertainty": "low"
}
```

The ESP32 should continuously send ultrasonic data:

```json
{
  "front_cm": 75.0,
  "left_cm": 50.0,
  "right_cm": 46.0,
  "rear_cm": 90.0,
  "min_cm": 46.0,
  "obstacle": false
}
```

After validation, the Google Dev Board sends one command to the ESP32:

```text
FWD
```

## 6. Software Stack

### Google Dev Board

Recommended software depends on the exact board. For a Coral Dev Board-style setup:

- Linux-based board image
- Python 3
- OpenCV
- pyserial
- tflite_runtime
- pycoral, if using Coral Edge TPU
- JSON logging

Possible packages:

```bash
pip install opencv-python-headless pyserial numpy pillow
```

If using Coral libraries, install the board-specific Coral runtime and PyCoral packages according to the board image.

### ESP32

Recommended tools:

- Arduino IDE, PlatformIO, or ESP-IDF
- Firmware for ultrasonic reading
- Firmware for motor control
- Serial JSON output and command input

## 7. Suggested Code Structure

```text
src/
  google_dev_board_robot/
    robot_controller.py
    camera.py
    prompt_parser.py
    tflite_grounding.py
    esp32_serial.py
    safety.py
    config.example.json
firmware/
  esp32_robot_controller/
    esp32_robot_controller.ino
```

| File | Purpose |
|---|---|
| `robot_controller.py` | Main control loop |
| `camera.py` | Captures webcam frames |
| `prompt_parser.py` | Converts instruction into structured navigation output |
| `tflite_grounding.py` | Runs TFLite or Edge TPU visual model |
| `esp32_serial.py` | Reads sensor JSON and sends motor commands |
| `safety.py` | Validates action before execution |
| `config.example.json` | Stores ports, camera index, thresholds, and model path |

## 8. Control Logic

```text
Start controller
Load config and model
Open camera
Open serial connection to ESP32
Loop:
    receive user instruction
    parse instruction into target, landmarks, relation, and suggested action
    capture camera frame
    run visual model or grounding logic
    read latest ultrasonic status from ESP32
    combine prompt output, image result, and obstacle status
    validate selected action
    send command to ESP32
    log result
```

## 9. Visual Grounding Options

### Option A: Object Detection

Use a TFLite object detection model to detect labels such as:

- door
- chair
- table
- signboard
- person
- wall

If the target is detected near the center of the image:

- choose `move_forward`

If the target is detected left:

- choose `turn_left`

If the target is detected right:

- choose `turn_right`

If target is not detected:

- choose `search`

If the robot is close to the target or the instruction says stop:

- choose `stop`

### Option B: Image Classification

Use an image classifier to classify the current scene as:

- corridor
- door area
- table area
- chair area
- signboard area

This is simpler than object detection but less precise.

### Option C: Rule-Based Baseline First

Before adding a model, start with:

- prompt parser extracts target
- manual or placeholder grounding returns `visible`, `not_visible`, or `unknown`
- action rules select movement
- ESP32 safety controls motor execution

This allows hardware testing before model integration.

## 10. ESP32 Responsibilities

The ESP32 should handle tasks that require stable timing:

- ultrasonic trigger and echo timing
- motor driver pin output
- motor timeout safety
- emergency stop behavior

Suggested local ESP32 rules:

```text
If front distance < safety threshold:
    stop motor immediately

If command timeout:
    stop motor immediately

If unknown command:
    stop motor immediately
```

## 11. Setup Procedure

### Step 1: Assemble Hardware

1. Mount the Google Dev Board on the chassis.
2. Mount ESP32 near the motor driver.
3. Mount the webcam at the front.
4. Mount ultrasonic sensors.
5. Connect ESP32 to motor driver input pins.
6. Connect ESP32 to ultrasonic sensors.
7. Connect Google Dev Board to ESP32 using USB serial or UART.
8. Connect webcam to Google Dev Board.
9. Connect grounds together.
10. Use regulated power for the Google Dev Board and ESP32.

### Step 2: Prepare Google Dev Board

1. Flash or install the supported board OS.
2. Confirm Python is available.
3. Install OpenCV and serial packages.
4. Install TensorFlow Lite or PyCoral packages if using Edge TPU.
5. Test camera capture.
6. Test model inference with a sample image.
7. Test ESP32 serial communication.

### Step 3: Flash ESP32 Firmware

The firmware should:

1. Read four ultrasonic sensors.
2. Publish JSON distance status.
3. Receive commands from the Google Dev Board.
4. Drive the motor driver.
5. Stop motors on obstacle or timeout.

### Step 4: Run Dry Test

Use a dry-run mode where the Google Dev Board prints commands but does not move the robot.

Test:

- `Go to the door`
- `Find the signboard`
- `Move toward the chair near the table`
- `Stop at the door`
- `Go there`

Expected result:

- clear targets produce valid action
- ambiguous instruction produces `stop`
- obstacle produces `stop`

### Step 5: Enable Motor Output

Only enable real movement after:

- motor directions are correct
- ultrasonic readings are stable
- STOP command works
- model output is validated
- manual power switch is reachable

## 12. Testing Plan

| Test | Expected Result |
|---|---|
| Camera test | Webcam frame captured on Google Dev Board |
| Model test | TFLite or selected model returns valid result |
| Prompt parser test | Instruction becomes structured output |
| ESP32 serial test | Sensor JSON is received correctly |
| Motor command test | `FWD`, `LEFT`, `RIGHT`, `SEARCH`, `STOP` work |
| Safety test | Obstacle causes stop |
| Timeout test | Motors stop when commands stop |
| Full scenario test | Robot performs simple indoor navigation action |

## 13. Advantages and Limitations

Advantages:

- More standalone than remote GPU setup.
- Lower WiFi dependency.
- Cleaner architecture for a real embedded robot.
- Good if using Edge TPU-compatible models.
- Good for demonstrating onboard AI decision making.

Limitations:

- Large VLMs may not run onboard.
- Model conversion to TFLite or Edge TPU may be difficult.
- Less flexible than a GPU laptop.
- Board availability and package support may become a risk.
- Prompt engineering may need to stay lightweight unless remote inference is added.

## 14. Recommended Use in the Project

This approach is suitable if the goal is to show a compact onboard prototype. It is best when the project uses lightweight visual models, rule-based prompt parsing, or TFLite object detection.

For the methodology chapter, this approach can be described as:

```text
The robot uses a Google Dev Board as the onboard AI controller and an ESP32 as the real-time motor and ultrasonic sensor controller. This creates a more self-contained robot, but the model must be selected according to the board's embedded inference capability.
```

