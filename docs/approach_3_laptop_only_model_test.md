# Approach 3 Guide: Laptop-Only Feasibility Test

This approach uses only a laptop. The built-in laptop camera acts as the robot camera, and the user physically carries the laptop while walking according to the model's navigation output. There is no motor driver, robot chassis, ESP32, or ultrasonic sensor in this setup.

This is not the final robot, but it is very useful as an early model feasibility test.

## 1. Purpose

The purpose of this setup is to test whether the GPU laptop can process live camera input and navigation prompts in near real time before spending time and money on robot hardware.

This approach is suitable for:

- testing the selected model
- measuring video processing latency
- testing prompt templates
- testing visual grounding or VLM action selection
- collecting early examples and failure cases
- deciding whether a GPU laptop can support the final robot setup

The limitation is that there is no physical robot movement. The human user becomes the movement system.

## 2. Hardware Components

| Component | Role |
|---|---|
| Laptop with GPU | Runs the model and control program |
| Built-in laptop camera | Captures front-view image |
| Human operator | Carries the laptop and follows model commands |
| Optional external webcam | Gives better camera placement than built-in laptop camera |

No ESP32, motor driver, ultrasonic sensors, or chassis are needed.

## 3. High-Level Architecture

```text
User instruction
        |
        v
Laptop application
        |
        +--> Built-in camera capture
        |
        +--> Prompt parsing
        |
        +--> Visual grounding or VLM action selection
        |
        +--> Action output on screen
                        |
                        v
              Human operator follows action
                        |
                        v
              New camera view is captured
```

## 4. Action Set

The laptop-only approach should use the same action set as the robot prototype:

```text
move_forward
turn_left
turn_right
stop
search
```

For human testing, the actions can be interpreted as:

| Model Action | Human Test Meaning |
|---|---|
| `move_forward` | Walk forward slowly |
| `turn_left` | Turn body or laptop left |
| `turn_right` | Turn body or laptop right |
| `stop` | Stop walking |
| `search` | Slowly rotate to scan the area |

Keeping the same action set makes the experiment transferable to a future physical robot.

## 5. Software Stack

Recommended software:

- Python 3.10 or newer
- OpenCV for camera capture
- PyTorch if running local models
- transformers, open_clip_torch, or selected VLM tools
- pandas or JSON logging for result collection
- optional simple GUI using Streamlit, Gradio, Tkinter, or a terminal interface

Example packages:

```bash
pip install opencv-python pillow numpy pandas
```

If using CLIP/OpenCLIP:

```bash
pip install torch torchvision open_clip_torch
```

If using a VLM or Hugging Face model:

```bash
pip install torch torchvision transformers accelerate
```

The exact packages depend on the selected model and GPU setup.

## 6. Suggested Code Structure

```text
src/
  laptop_only_test/
    live_navigation_test.py
    camera.py
    prompt_parser.py
    model_runner.py
    action_display.py
    metrics.py
    config.example.json
    logs/
```

| File | Purpose |
|---|---|
| `live_navigation_test.py` | Main program for live camera and instruction loop |
| `camera.py` | Captures frames from built-in camera |
| `prompt_parser.py` | Extracts target, landmarks, relation, action goal, and uncertainty |
| `model_runner.py` | Runs CLIP, VLM, or rule-based action choice |
| `action_display.py` | Shows the chosen action on screen |
| `metrics.py` | Measures latency and logs results |
| `config.example.json` | Stores camera index, model settings, and log path |

## 7. Structured Output Format

The laptop-only setup should still produce the same JSON-style output as the final robot:

```json
{
  "target": "door",
  "landmarks": ["door"],
  "spatial_relation": null,
  "action_goal": "find and move toward the door",
  "suggested_action": "move_forward",
  "uncertainty": "low",
  "reason": "The door appears in the forward view."
}
```

This makes the laptop-only results useful for Chapter 3 and future implementation.

## 8. Live Test Flow

```text
Start laptop navigation test program
Select camera index
Enter user instruction
Loop:
    capture current camera frame
    run prompt parser
    run visual grounding or action selection
    display suggested action
    human operator follows the action
    log frame timestamp, instruction, model output, and latency
    continue until target is reached or user stops test
```

Example terminal output:

```text
Instruction: Go to the door
Target: door
Action: move_forward
Uncertainty: low
Latency: 420 ms
```

## 9. Model Options

### Option A: Prompt Parser Only

This is the simplest test. It checks whether natural language instructions can be converted into structured fields.

Example:

```text
Instruction: Move toward the chair near the table
Target: chair
Landmarks: chair, table
Spatial relation: chair near table
Suggested action: search
Uncertainty: medium
```

This does not test visual grounding.

### Option B: CLIP/OpenCLIP Grounding

The program compares the current camera image against text prompts such as:

- `a door in an indoor corridor`
- `a chair near a table`
- `a signboard on a wall`

The model selects the text with the highest similarity score.

This can test whether image-text similarity is fast enough for live video.

### Option C: VLM Action Selection

The program asks a vision-language model:

```text
Given the current camera image and the instruction "Go to the door",
choose one action from:
move_forward, turn_left, turn_right, stop, search.
Return JSON only.
```

This is closest to the final prompt-engineering goal, but it may be slower.

## 10. Manual Safety and Testing Rules

Because a human is carrying the laptop, this setup is safer than a moving robot, but the test should still be controlled.

Rules:

- Walk slowly.
- Test in a clear indoor area.
- Avoid stairs, wet floors, and crowded spaces.
- Do not stare only at the screen while walking.
- Stop immediately if the model output is confusing.
- Keep another person nearby if testing in a lab or corridor.

## 11. Logging

Each test should log:

- timestamp
- instruction
- target
- landmarks
- spatial relation
- selected action
- uncertainty
- model latency
- total loop latency
- whether the action was reasonable
- user comment

Example JSONL record:

```json
{
  "timestamp": 1710000000.0,
  "instruction": "Go to the door",
  "target": "door",
  "suggested_action": "move_forward",
  "uncertainty": "low",
  "latency_ms": 420.5,
  "human_label": "correct"
}
```

## 12. Evaluation Metrics

| Metric | Meaning |
|---|---|
| Prompt output validity | Whether the model returns all required fields |
| Landmark extraction accuracy | Whether the target is extracted correctly |
| Action selection accuracy | Whether the action matches the scene |
| Average latency | Average time from frame capture to action output |
| Real-time usability | Whether output is fast enough for walking or robot control |
| Failure-case count | Number of wrong, uncertain, or invalid outputs |

This approach can answer an important early question:

```text
Can the available GPU laptop process live camera navigation decisions fast enough for the project?
```

## 13. Setup Procedure

### Step 1: Create Python Environment

```bash
python -m venv .venv
```

Activate it, then install packages:

```bash
pip install opencv-python pillow numpy pandas
```

Install model-specific packages after choosing the model.

### Step 2: Test Camera

Run a small OpenCV script to confirm the built-in camera works.

Expected result:

- camera opens successfully
- frame is displayed or saved
- frame rate is acceptable

### Step 3: Test Prompt Parser

Use sample instructions:

- `Go to the door`
- `Find the signboard`
- `Move toward the chair near the table`
- `Stop at the door`
- `Go there`

Expected result:

- clear instruction returns low or medium uncertainty
- ambiguous instruction returns high uncertainty and `stop`

### Step 4: Test Model Latency

Run the selected model on one frame.

Record:

- camera capture time
- model inference time
- total loop time

Suggested target:

- below 1 second is usable for slow testing
- below 500 ms is better for responsive control
- above 2 seconds may be too slow for real-time movement

### Step 5: Run Walking Test

1. Start the program.
2. Enter one instruction.
3. Hold the laptop so the camera faces forward.
4. Follow the displayed action slowly.
5. Stop after reaching the target or after a fixed number of steps.
6. Save the log.

## 14. Advantages and Limitations

Advantages:

- Lowest hardware cost.
- Fastest way to test the model.
- Good for early feasibility.
- No motor safety risk.
- Useful for collecting latency and prompt failure data.

Limitations:

- Not a real mobile robot.
- No motor control.
- No ultrasonic obstacle sensing.
- Human movement may not match robot movement.
- Built-in laptop camera position may not match the final robot camera.

## 15. Recommended Use in the Project

This approach is recommended as Phase 1 before building the physical robot. It should not be presented as the final robot implementation, but it can be included in the methodology as a feasibility phase.

For the methodology chapter, this approach can be described as:

```text
Before constructing the physical robot, a laptop-only feasibility setup is used to test prompt processing, live camera input, model latency, and action-selection behavior. The human operator carries the laptop and follows the model's suggested movement actions. This reduces early hardware cost and identifies whether the selected model is suitable for real-time robot control.
```

