# CHAPTER 3

# RESEARCH METHODOLOGY

## 3.1 Introduction

This chapter presents the finalized methodology for `Prompt Engineering for
Mobile Robot Navigation`. Following supervisor feedback, the project contains
one physical implementation only: a Coral Dev Board mobile robot with an ESP32
sensor, safety, and motor-control layer.

The methodology is inspired by the modular structure of LM-Nav and the
prompt-based action-selection idea of VLMnav. Language interpretation, visual
grounding, and navigation execution are separated so each stage can be tested.
The first prototype targets a basic goal such as `find the chair` and restricts
all output to:

- `move_forward`
- `turn_left`
- `turn_right`
- `search`
- `stop`

The laptop-only webcam demonstration is used only to produce expected-results
evidence before physical testing. Its Python/OpenCV processing runs in a Docker
container while a local browser captures the webcam. It is not a second
physical approach.

## 3.2 Research Design and Project Workflow

The project follows an iterative prototype methodology. The already-built
mechanical and power systems are completed by wiring and validating the ESP32
sensor and motor layer, integrating Coral UART communication, verifying
Edge TPU-compatible visual inference, and testing one complete basic goal.

### 3.2.1 Methodology Alignment with Research Objectives

**Table 3.1: Methodology Alignment with Research Objectives**

| Research Objective | Method Used | Expected Output | Evaluation |
|---|---|---|---|
| Objective 1: Develop a structured prompt-engineering pipeline | Convert a simple instruction into fixed navigation fields and approved actions | Parseable target, action goal, and uncertainty | Prompt validity and target-extraction accuracy |
| Objective 2: Integrate one Coral Dev Board physical robot | Connect Coral, ESP32, webcam, sensors, MX1508 drivers, motors, and completed power system | Working end-to-end robot | Wiring, sensor, motor, UART, and power tests |
| Objective 3: Evaluate basic prompt-engineered navigation | Run repeated single-target indoor trials | Measured action, latency, safety, and movement results | Detection correctness, action accuracy, safe-stop rate, and goal completion |

### 3.2.2 Overall Project Workflow

**Figure 3.1: Proposed project workflow**

```text
Define one basic goal, prompt schema, actions, and metrics
        |
        v
Complete Coral, ESP32, sensor, and motor-driver wiring
        |
        v
Validate ESP32 sensors, safety, and four-motor control
        |
        v
Install Mendel Linux and verify Coral Edge TPU inference
        |
        v
Integrate webcam, structured prompt parser, detector, and UART
        |
        v
Run dry tests, raised-wheel tests, and controlled floor tests
        |
        v
Analyse failures and report measured results
```

### 3.2.3 Development Workflow

**Table 3.2: Development Workflow**

| Stage | Activity | Expected Output |
|---|---|---|
| Stage 1 | Finalize the basic goal, action set, prompt schema, scenarios, and logging format | Common experimental definition |
| Stage 2 | Verify the completed power system and common-ground architecture | Stable compute and motor supplies |
| Stage 3 | Wire ESP32 sensors, Coral UART3, and two MX1508 drivers | Completed signal wiring |
| Stage 4 | Test ESP32 sensing, motor directions, timeout, and obstacle stop | Verified local safety and movement |
| Stage 5 | Install Mendel Linux and verify USB webcam and Edge TPU detector | Working Coral perception platform |
| Stage 6 | Integrate structured prompt processing, detection, action selection, UART, and logging | Working end-to-end prototype |
| Stage 7 | Run repeated controlled trials and calculate metrics | Final physical results |

## 3.3 Finalized System Architecture

The Coral Dev Board performs high-level processing. The ESP32 handles local
real-time sensing, safety, and motor control. Direct 3.3 V UART is used between
the boards so the Coral USB-A host port remains available for the webcam.

**Figure 3.2: Proposed system architecture**

```text
User simple natural-language goal
        |
        v
Coral Dev Board
  - structured prompt processing
  - USB webcam capture
  - Edge TPU-compatible target detection
  - restricted action selection and logging
        |
        | UART3 /dev/ttymxc2, 115200 baud
        v
ESP32
  - two HC-SR04 sensors
  - GY-291 / ADXL345
  - obstacle and command-timeout safety
  - two MX1508 motor drivers
        |
        v
Four DC gear motors with wheels
```

### 3.3.1 Hardware Roles

**Table 3.3: Finalized Hardware Roles**

| Component | Finalized Role |
|---|---|
| Coral Dev Board | Onboard prompt processing, webcam capture, Edge TPU-compatible detection, action selection, and logging |
| ESP32 | UART communication, sensor reading, deterministic safety, and motor control |
| USB webcam | Front RGB image input |
| Two HC-SR04 sensors | Front-left and front-right obstacle safety |
| GY-291 / ADXL345 | Acceleration, roll/pitch tilt, motion, vibration, and shock observations |
| Two MX1508 drivers | Four independent DC motor channels |
| Four DC gear motors | Physical forward, turn, search, and stop behaviour |

## 3.4 Requirements, Constraints, and Acceptance Criteria

**Table 3.4: Requirements and Acceptance Criteria**

| Requirement | Specification | Verification Method | Pass Criteria |
|---|---|---|---|
| Natural-language input | Accept a basic supported goal such as `find the chair` | Input test | Instruction is accepted without manual rewriting |
| Structured prompt output | Return fixed machine-readable fields | JSON validation | Required fields are present and parseable |
| Coral onboard processing | Run prompt parser, webcam, detection, action selection, and logging onboard | Integration test | Coral completes the navigation loop |
| Edge TPU visual grounding | Detect a supported target class | Camera scenario test | Correct detection or safe search response |
| Coral-to-ESP32 UART | Exchange commands and sensor JSON at 115200 baud | UART test | Stable command and status communication |
| Four-motor control | Two MX1508 modules control four motors | Raised-wheel test | Forward, left, right, search, and stop work |
| Local safety | Obstacle, timeout, or invalid command stops movement | Failure-case test | Unsafe movement is prevented |
| Power stability | Completed power system supplies stable rails | Voltage and runtime test | No unsafe voltage, reset, or severe drop |

The baseline does not include SLAM, LiDAR mapping, dense depth, or an
unrestricted large vision-language model.

## 3.5 Data, Test Environment, and Experimental Materials

### 3.5.1 Basic Goal and Scenarios

**Table 3.5: First-Prototype Scenarios**

| Scenario | Example Instruction | Expected Behaviour |
|---|---|---|
| Supported target absent | "Find the chair." | `search` |
| Target on left | "Find the chair." | `turn_left` |
| Target on right | "Find the chair." | `turn_right` |
| Target centred and distant | "Find the chair." | `move_forward` |
| Target centred and close | "Find the chair." | `stop` |
| Unsupported or ambiguous target | "Go there." | `stop` |
| Obstacle present | "Find the chair." | ESP32 forces `stop` |

### 3.5.2 Experimental Materials

**Table 3.6: Experimental Materials**

| Material | Quantity or Role |
|---|---|
| Coral Dev Board | Only onboard high-level compute board |
| ESP32 | Sensor, safety, UART, and motor-control controller |
| USB webcam | One front RGB camera |
| DC gear motor with wheel | Four motors and wheels |
| MX1508 dual motor-driver module | Two modules controlling four motors |
| Adjustable motor buck converter | Regulated motor-driver rail |
| HC-SR04 ultrasonic sensor | Two front obstacle sensors |
| GY-291 / ADXL345 accelerometer | Acceleration, roll/pitch tilt, motion, vibration, and shock sensing |
| Completed battery and power system | Mobile robot power source |
| Instruction and scenario list | Common experimental inputs |
| JSONL result logs | Store prompts, detections, sensors, actions, latency, and failures |

**Figure 3.3: Main hardware components for the finalized Coral Dev Board robot**

```text
Coral Dev Board
ESP32
USB webcam
Two HC-SR04 ultrasonic sensors
GY-291 / ADXL345
Two MX1508 motor drivers
Four DC gear motors with wheels
Completed protected power system
```

### 3.5.3 Software and Model Requirements

**Table 3.7: Software, Model, and Platform Requirements**

| Item | Purpose | Finalized Tool or Example |
|---|---|---|
| Coral operating system | Run the onboard application | Mendel Linux |
| High-level language | Prompt parser, detection control, validation, UART, and logging | Python |
| Webcam processing | Capture RGB frames | OpenCV |
| Prompt processing | Produce structured basic-goal output | Deterministic fixed-schema parser |
| Visual grounding | Detect supported target class | Quantized Edge TPU-compiled TensorFlow Lite detector |
| ESP32 firmware | Sensors, safety, UART, and two-MX1508 motor control | Arduino framework |
| Communication | Coral to ESP32 commands and status | UART3 to UART2 at 115200 baud |
| Result storage | Record experimental data | JSONL |

## 3.6 Prompt Engineering Design

The first prototype uses a deterministic structured parser because the Coral
Edge TPU cannot run a general-purpose LLM. This parser still applies the main
prompt-engineering principles required by the study: fixed fields, restricted
actions, explicit uncertainty, and safe rejection of unsupported goals.

**Table 3.8: Structured Prompt Fields**

| Field | Description | First-Prototype Example |
|---|---|---|
| `instruction` | Original user instruction | `find the chair` |
| `target` | Main supported target | `chair` |
| `landmarks` | Important detected instruction objects | `["chair"]` |
| `spatial_relation` | Relation if supported | `null` |
| `action_goal` | Short interpreted goal | `find and approach the chair` |
| `uncertainty` | Safety-oriented confidence label | `low` or `high` |

```json
{
  "instruction": "find the chair",
  "target": "chair",
  "landmarks": ["chair"],
  "spatial_relation": null,
  "action_goal": "find and approach the chair",
  "uncertainty": "low"
}
```

Unsupported or unclear instructions produce high uncertainty and `stop`.

## 3.7 Webcam-Based Visual Grounding and Action Selection

The Coral captures a USB-webcam frame and runs an Edge TPU-compatible object
detector. The highest-confidence detection matching the structured target is
used for simple action selection.

**Table 3.9: Visual Grounding and Action Decision Rules**

| Condition | Selected Action |
|---|---|
| Structured target unsupported or uncertain | `stop` |
| Target not detected | `search` |
| Target centre is left of the image centre zone | `turn_left` |
| Target centre is right of the image centre zone | `turn_right` |
| Target is centred and below the goal-size threshold | `move_forward` |
| Target reaches the configured image-area threshold | `stop` |
| ESP32 reports obstacle | `stop` |

The first model may use a COCO-compatible detector and the target `chair`.
Custom classes such as `door` and `signboard` are future extensions requiring
custom data collection, training, quantization, and Edge TPU compilation.

## 3.8 Robot Action and Command Mapping

**Table 3.10: Action Set and Motor Command Mapping**

| Action | ESP32 Command | Four-Motor Behaviour |
|---|---|---|
| `move_forward` | `FWD` | All motors move forward |
| `turn_left` | `LEFT` | Left motors reverse and right motors move forward |
| `turn_right` | `RIGHT` | Right motors reverse and left motors move forward |
| `search` | `SEARCH` | Robot rotates slowly |
| `stop` | `STOP` | All motor outputs stop |

The ESP32 accepts only these commands. Unknown commands, loss of both
ultrasonic readings, and a command delay above 1,000 ms cause `stop`.

## 3.9 Mechanical Design and Physical Integration

The finalized Fusion 360 robot design provides mounting positions for the
compute board, ESP32, USB webcam, two front ultrasonic sensors, GY-291, two
MX1508 drivers, completed power system, and four motors.

**Figure 3.4: Finalized Fusion 360 physical robot model**

![Finalized Fusion 360 physical robot model](figures/chapter_3/figure_3_4_finalized_fusion_360_robot_model.png)

The existing render records the mechanical design stage. The completed physical
prototype uses the Coral Dev Board as the only high-level compute board, with
an appropriate mounting plate or adaptor.

**Figure 3.5: Finalized Fusion 360 robot multi-view layout**

![Finalized Fusion 360 robot multi-view layout](figures/chapter_3/figure_3_5_fusion_360_robot_multi_view.png)

The views support sensor visibility, wheel clearance, component spacing, cable
access, and Coral mounting verification.

**Figure 3.6: Finalized mechanical design sketch and dimensions**

![Finalized mechanical design sketch and dimensions](figures/chapter_3/figure_3_6_mechanical_design_sketch_and_dimensions.png)

The approximate overall dimensions are 232.24 mm long, 188.91 mm wide, and
129.57 mm high.

## 3.10 Finalized Wiring Architecture

**Figure 3.7: Finalized component-based circuit architecture**

```text
Completed protected power system
        |
        +--> regulated motor rail --> two MX1508 drivers --> four motors
        |
        +--> regulated logic rail --> Coral Dev Board and ESP32

Coral USB-A --> USB webcam
Coral UART3 --> ESP32 UART2
ESP32 --> sensors and MX1508 control inputs
```

**Figure 3.8: Finalized ESP32 sensor and motor wiring**

```text
Coral UART3 TX pin 7  -> ESP32 GPIO 16 / UART2 RX
Coral UART3 RX pin 11 <- ESP32 GPIO 17 / UART2 TX
Coral GND pin 9       -> ESP32 GND

HC-SR04 front-left: Trigger GPIO 5, Echo GPIO 34 through level shifting
HC-SR04 front-right: Trigger GPIO 18, Echo GPIO 35 through level shifting
GY-291 I2C: SDA GPIO 21, SCL GPIO 22
Front-left motor: GPIO 25 and GPIO 26
Front-right motor: GPIO 27 and GPIO 14
Rear-left motor: GPIO 32 and GPIO 33
Rear-right motor: GPIO 19 and GPIO 23
```

The detailed connection and test sequence is provided in
`docs/circuit_wiring_guide.md`.

## 3.11 Software Implementation

**Table 3.11: Source Code and Documentation Modules**

| File or Module | Target | Purpose | Status |
|---|---|---|---|
| `docs/coral_dev_board_full_software_setup.md` | Documentation | Complete Coral OS-to-final-result setup | Provided |
| `docs/circuit_wiring_guide.md` | Documentation | Exact Coral, ESP32, sensor, and MX1508 wiring | Provided |
| `docs/laptop_only_expected_results_setup.md` | Documentation | Separate Docker-based FYP1 expected-results demonstration | Provided |
| `src/coral_robot/robot_controller.py` | Coral Dev Board | Prompt parser, Edge TPU detection, action selection, UART, and logging | Provided |
| `src/laptop_expected_results/web_app.py` | Docker laptop demo | Browser-webcam frame processing and expected action output | Provided |
| `docker-compose.laptop-demo.yml` | Docker laptop demo | Reproducible container build and runtime configuration | Provided |
| `firmware/esp32_robot_controller/esp32_robot_controller.ino` | ESP32 | UART, sensors, safety, and four-motor control | Provided |

## 3.12 Main Equations and Decision Rules

**Table 3.12: Main Equations and Decision Rules**

| Equation or Rule | Description | Evaluation Use |
|---|---|---|
| `d_cm = t_echo_us / 58` | HC-SR04 distance approximation | Convert Echo duration to centimetres |
| `Prompt Validity = N_valid / N_total * 100 percent` | Valid structured-output percentage | Prompt reliability |
| `Accuracy = N_correct / N_total * 100 percent` | General correctness percentage | Detection and action metrics |
| `T_total = T_prompt + T_capture + T_detection + T_sensor + T_comm` | End-to-end response time | Coral latency |
| `a_exec = stop` for invalid output, high uncertainty, obstacle, timeout, or invalid action | Safety decision rule | Safe-failure evaluation |
| `Movement Success Rate = N_success / N_scenarios * 100 percent` | Successful simple-goal percentage | Physical robot behaviour |
| `a_mag = sqrt(a_x^2 + a_y^2 + a_z^2)` | Total measured acceleration magnitude | Motion, vibration, and shock observation |

## 3.13 Implementation Procedure

**Table 3.13: Implementation Procedure**

| Stage | Activity | Verification | Expected Result |
|---|---|---|---|
| Stage 1 | Verify completed power rails and common ground | Multimeter and load test | Stable compute and motor supplies |
| Stage 2 | Wire Coral UART3, ESP32, sensors, and both MX1508 drivers | Continuity and pin-map review | Correct signal wiring |
| Stage 3 | Flash ESP32 firmware | UART `PING` and sensor status test | Stable commands and JSON status |
| Stage 4 | Test four motors with wheels raised | Individual and combined action tests | Correct movement directions |
| Stage 5 | Install Mendel Linux and test Edge TPU and webcam | Official demos and camera capture | Working Coral platform |
| Stage 6 | Run Coral controller without `--execute` | Dry-run logs | Correct prompt, detection, action, and STOP command |
| Stage 7 | Enable supervised raised-wheel movement | End-to-end command test | Correct action-to-motor behaviour |
| Stage 8 | Run controlled floor scenarios | Scenario checklist and logs | Measured basic-goal results |

## 3.14 Testing and Validation Plan

**Table 3.14: Testing and Validation Matrix**

| Test Stage | Test Setup | Metric | Pass Criteria |
|---|---|---|---|
| Prompt format test | Supported and unsupported instructions | Prompt output validity | Required fields parse correctly |
| Webcam test | USB webcam on Coral | Frame capture success | Reliable usable frames |
| Edge TPU test | Supported target in controlled views | Detection correctness | Correct match or safe search |
| UART test | Coral UART3 and ESP32 UART2 | Command/status reliability | Repeated valid exchanges |
| Ultrasonic test | Two front sensors | Distance availability and error | Both sensors report usable values |
| GY-291 test | Stationary, tilted, moved, and lightly vibrated robot | Plausibility and response | Expected changes are observable |
| Motor test | Two MX1508 modules and four motors | Movement correctness | All approved actions work |
| Safety test | Obstacle, timeout, invalid command, and uncertainty | Safe-stop rate | Robot stops safely |
| Full scenario test | Controlled chair target | Goal completion | Intended basic behaviour is completed |

## 3.15 Evaluation Metrics

**Table 3.15: Evaluation Metrics**

| Metric | Description |
|---|---|
| Prompt output validity | Percentage of outputs containing all required fields |
| Supported-target extraction accuracy | Percentage of correctly extracted supported targets |
| Visual grounding correctness | Percentage of correctly detected target conditions |
| Action-selection accuracy | Percentage of expected selected actions |
| End-to-end latency | Time from instruction and frame input to validated action |
| UART reliability | Percentage of valid command and sensor-status exchanges |
| Safe-stop rate | Percentage of unsafe cases correctly stopped |
| Movement success rate | Percentage of completed simple-goal scenarios |
| GY-291 response | Plausibility of acceleration, tilt, motion, and vibration observations |
| Power stability | Resets, voltage drops, or failures during testing |

## 3.16 Laptop-Only Expected-Results Demonstration

The separate laptop demo uses a browser webcam and coloured marker to display
expected navigation actions. A Docker container provides the isolated Flask,
OpenCV, NumPy, and logging environment. This allows the action interface and
software environment to be demonstrated reproducibly during FYP1. The user
manually moves the laptop; no motor interface or physical robot claim is made.
Final results must come from the Coral Dev Board physical robot.

## 3.17 Safety, Limitations, and Future Work

Testing must use the completed protected power system, fuse, reachable main
switch, correct regulated rails, and a common ground. Motor tests begin with
the robot raised. HC-SR04 Echo pins require level shifting.

The robot stops for invalid output, high uncertainty, obstacle detection,
unknown commands, or command timeout. Testing is supervised in a controlled
indoor area.

The USB webcam does not provide dense depth or a 3D map. Two ultrasonic sensors
provide limited obstacle coverage. The GY-291 does not provide yaw heading. The
Coral Dev Board supports only Edge TPU-compatible models, and the first
prototype supports only simple goals and detector-known target classes.

Future work may include a custom door and signboard detector, wheel encoders,
magnetometer or full IMU, RGB-D camera, LiDAR, mapping, relation-aware prompts,
and stronger navigation policies.

## 3.18 Summary

This chapter finalized the methodology around one Coral Dev Board physical
robot. The project connects structured prompt processing and Edge TPU visual
grounding to an ESP32 that independently handles sensors, safety, and four-motor
control. The first measurable target is a reliable and safe single-goal indoor
navigation demonstration.
