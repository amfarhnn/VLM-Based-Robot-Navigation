# Research-Paper Method Selection for the Raspberry Pi Robot

## 1. Purpose

This document evaluates the repositories in `github-research-papers` against
the finalized project hardware:

- Raspberry Pi 4 with one USB RGB webcam
- ESP32 with two front HC-SR04 ultrasonic sensors
- GY-291 / ADXL345 accelerometer
- two MX1508 motor drivers and four DC gear motors
- USB serial communication between Raspberry Pi and ESP32

The current robot has no RGB-D camera, wheel encoders, reliable yaw sensor,
LiDAR, GPS, SLAM pose, ROS installation, or GPU accelerator. Therefore, the
best approach is to adapt selected research methods rather than attempt to run
one complete research repository.

## 2. Recommended Combined Method

The most suitable design combines ideas from four repositories:

1. **LM-Nav:** convert a language instruction into an ordered list of
   landmarks or targets.
2. **VLM-NAV:** use a small discrete action space and fuse perception,
   obstacle sensing, and previous-action information.
3. **NaVid / NaVILA:** use recent visual history and separate high-level
   decisions from the real-time safety controller.
4. **ViNT:** optionally add a simple taught-route image sequence in future
   work.

The resulting project-specific pipeline is:

```text
Natural-language instruction
        |
        v
Constrained landmark and goal extraction
        |
        v
Recent webcam frames + marker or object grounding
        |
        v
Rule-based or lightweight learned action selector
        |
        v
Restricted action: search / left / right / forward / stop
        |
        v
ESP32 obstacle, sensor-fault, invalid-command, and timeout safety
        |
        v
MX1508 motor drivers and four motors
```

## 3. Compatibility Summary

| Repository | Suitable Part | Suitability | Main Limitation |
|---|---|---:|---|
| `lm_nav` | Ordered landmark extraction and modular pipeline | High | Full graph routing requires localization and visual embeddings |
| `vlm_nav` | Discrete actions, sensor fusion, previous-action memory, tiny action network | High with adaptation | Original method assumes depth maps, heading, AirSim, and optional API VLM |
| `NaVILA` | Two-level high-level decision and low-level safety concept | High as an architecture principle | Full VLA model requires powerful GPU hardware |
| `NaVid-VLN-CE` | Recent-frame history and constrained action parsing | Medium as a lightweight adaptation | Full video VLM requires GPU and simulator stack |
| `visualnav-transformer` | Taught-route image keyframes and waypoint-control concept | Medium for future work | Full ViNT/NoMaD deployment expects ROS, odometry, and stronger compute |
| `vlmaps` | Language-indexed map and spatial instruction ideas | Low for current hardware | Requires RGB-D frames and reliable camera or robot poses |
| `HOV-SG` | Floor-room-object hierarchy for future prompt design | Low for current hardware | Requires posed RGB-D, large models, point clouds, and substantial RAM/GPU |

## 4. Methods Suitable for the Current Prototype

### 4.1 LM-Nav Ordered Landmark Extraction

LM-Nav separates instruction interpretation from visual navigation. Its
landmark-extraction stage converts a full instruction into an ordered landmark
list.

Relevant local files:

- `github-research-papers/lm_nav/lm_nav/landmark_extraction.py`
- `github-research-papers/lm_nav/lm_nav/pipeline.py`

This method fits the project title and can extend the current fixed-schema
parser without requiring a large onboard model.

Example:

```text
Instruction: Find the green marker, then find the blue marker.

Structured goal:
{
  "ordered_targets": ["green marker", "blue marker"],
  "current_target_index": 0,
  "allowed_actions": ["search", "turn_left", "turn_right", "move_forward", "stop"]
}
```

For the first prototype, keep one supported target. Ordered multi-target
navigation should only be enabled after single-target trials are reliable.

### 4.2 VLM-NAV Discrete Action and Sensor-Fusion Method

VLM-NAV uses three discrete movement actions and combines perception with
left/right distance sensing, previous action, and rule-based decisions.

Relevant local files:

- `github-research-papers/vlm_nav/vlm_nav/vlm_navigation.py`
- `github-research-papers/vlm_nav/vlm_nav/navigator.py`
- `github-research-papers/vlm_nav/vlm_nav/navigation_learner.py`

The current project already uses a compatible restricted action set. The
method can be adapted using available robot observations:

| Research Input | Project Adaptation |
|---|---|
| Depth-map regions | Marker or object visibility, centre position, and area |
| Left/right distance sensors | Front-left and front-right HC-SR04 distance |
| Relative heading | Not available; do not claim yaw from the ADXL345 |
| Previous action | Store the previous selected action |
| Three movement actions | Use left, right, and forward plus safe search and stop |

Previous-action memory is useful for reducing rapid left-right oscillation.
However, the research code sometimes resolves an opposite turn by forcing
forward movement. The physical robot must instead keep the safer turn or stop;
it must never move forward only to suppress oscillation.

### 4.3 Tiny Learned Action Selector

The VLM-NAV `Navigator` is a small fully connected network. A similarly small
classifier can run on Raspberry Pi CPU after enough robot-specific data has
been collected.

Recommended future input features:

```text
target_visible
target_center_x
target_area_ratio
front_left_cm
front_right_cm
obstacle
sensor_fault
previous_action
roll_deg
pitch_deg
motion_detected
```

Recommended output classes:

```text
search, turn_left, turn_right, move_forward, stop
```

The rule-based controller should remain the FYP1 baseline. In FYP2, manually
label safe actions, train the small model on a laptop, deploy inference on the
Raspberry Pi, and compare it against the baseline. The ESP32 safety layer must
override either method.

### 4.4 NaVILA Two-Level Control Architecture

NaVILA separates high-level language-based decisions from real-time locomotion
and obstacle avoidance.

Relevant local reference:

- `github-research-papers/NaVILA/README.md`

This principle already matches the project:

| NaVILA Concept | Project Implementation |
|---|---|
| High-level navigation command | Raspberry Pi prompt, vision, and action selection |
| Real-time locomotion and avoidance | ESP32 motor control and deterministic safety |

Use this architecture as research justification. Do not attempt to run the
full NaVILA model on Raspberry Pi 4.

### 4.5 NaVid Recent-Frame History

NaVid uses historical observations and the current image when selecting the
next action.

Relevant local files:

- `github-research-papers/NaVid-VLN-CE/agent_navid.py`
- `github-research-papers/NaVILA/llava/eval/run_navigation.py`

A lightweight version is suitable for Raspberry Pi:

1. Keep the last three to five marker detections, not full VLM features.
2. Use median target centre and area across valid detections.
3. Require repeated evidence before changing turn direction.
4. Stop if the visual history is inconsistent or sensor status is unavailable.

Do not copy NaVid's random-action fallback when model output is invalid. An
invalid decision on the physical robot must produce `stop`.

## 5. Methods Suitable Only for Later Work

### 5.1 ViNT Taught-Route Image Sequence

ViNT creates a topological map from images sampled along a demonstrated route.
The idea can become a future "teach and repeat" mode:

1. Manually drive the robot through a short indoor route.
2. Store ordered webcam keyframes.
3. Match the current image against nearby keyframes.
4. Move toward the next keyframe while ESP32 safety remains active.

For the current hardware, begin with lightweight ORB image matching rather
than the full ViNT/NoMaD neural model. Reliable metric waypoint control would
require wheel encoders and a real heading sensor.

Relevant local files:

- `github-research-papers/visualnav-transformer/deployment/src/create_topomap.py`
- `github-research-papers/visualnav-transformer/deployment/src/pd_controller.py`

### 5.2 VLMaps Spatial Language Ideas

VLMaps demonstrates object-goal and relation-aware instructions such as moving
beside or between objects. These ideas are useful for future prompt schemas,
but its actual mapping pipeline is not compatible with the present robot.

The full method requires RGB-D observations and reliable world-frame poses.
The current USB RGB webcam, ultrasonic sensors, and ADXL345 cannot provide
those inputs.

### 5.3 HOV-SG Hierarchical Scene Representation

The floor-room-object hierarchy is useful as a future language representation:

```text
floor -> room -> object -> action
```

The full HOV-SG implementation is unsuitable for Raspberry Pi 4 because it
uses posed RGB-D data, point clouds, OpenCLIP, SAM, and substantial RAM/GPU
resources.

## 6. Methods Not Recommended for This Setup

Do not use the following as the first physical implementation:

- full NaVILA, NaVid, or Uni-NaVid inference on Raspberry Pi 4
- full VLMaps or HOV-SG map construction
- full ViNT/NoMaD deployment without ROS, odometry, and stronger compute
- monocular estimated depth as the only collision-safety source
- ADXL345 roll or pitch as robot yaw or compass heading
- random movement when parsing, perception, or model output fails
- unrestricted VLM output sent directly to the ESP32

An API-based VLM can be tested as an optional comparison, but network latency,
availability, cost, and unpredictable text output make it unsuitable as the
only physical control method.

## 7. Recommended Implementation Roadmap

### FYP1: Current Basic Prototype

1. Keep the fixed-schema parser and one target: `find the green marker`.
2. Keep OpenCV marker grounding and the restricted five-action set.
3. Add previous-action logging and lightweight temporal detection history.
4. Keep all obstacle and communication safety on the ESP32.
5. Measure prompt validity, grounding correctness, action correctness,
   latency, safe-stop rate, and goal completion.

### FYP2: First Research Extension

1. Extend the parser to ordered supported landmarks.
2. Collect robot-specific observation and safe-action examples.
3. Train a tiny action classifier and compare it with the rule-based baseline.
4. Replace markers with lightweight indoor-object detection.
5. Add a short taught-route image sequence if time permits.

### Hardware Needed Before Map-Based Navigation

- wheel encoders for distance and odometry
- a gyroscope or magnetometer-capable IMU for turning or heading feedback
- preferably an RGB-D camera or LiDAR for map construction
- stronger compute or offboard GPU for large VLM, VLMaps, HOV-SG, or ViNT

## 8. Final Selection

The recommended method for this project is:

> A modular LM-Nav-inspired prompt and landmark pipeline, using a VLM-NAV-style
> restricted action selector with lightweight temporal history, while the
> Raspberry Pi performs high-level decisions and the ESP32 independently
> enforces real-time safety.

This selection is technically realistic for Raspberry Pi 4, directly supports
the project title, and leaves a clear comparison path between rule-based and
small learned action selection for FYP2.
