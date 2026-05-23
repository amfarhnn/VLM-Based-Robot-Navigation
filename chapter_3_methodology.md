# CHAPTER 3

# RESEARCH METHODOLOGY

## 3.1 Introduction

Chapter 2 identified a research gap in low-cost language-guided mobile robot navigation. Existing systems such as LM-Nav, VLMaps, HOV-SG, ViNT, NoMaD, VLMnav, NaVid, Uni-NaVid, and NaVILA show that language, vision, and action can be combined for robot navigation. However, many of these systems require expensive robot platforms, RGB-D cameras, LiDAR, mapping pipelines, server-level models, or complex navigation policies. This creates a practical gap for student-level implementation.

The earlier single-board hardware direction is removed from the methodology because the board is not currently available for the project. The methodology is therefore updated around three practical implementation approaches:

- **Approach 1:** Raspberry Pi, ESP32, USB webcam, motor driver, ultrasonic sensors, and a GPU laptop or desktop connected through WiFi.
- **Approach 2:** Google Dev Board, ESP32, USB webcam, motor driver, and ultrasonic sensors.
- **Approach 3:** Laptop-only feasibility test using the built-in laptop camera and local GPU, where the human operator follows the model's suggested movement actions.

The methodology is inspired by the modular structure of LM-Nav and the prompt-based action-selection idea of VLMnav. LM-Nav motivates the separation between language understanding, visual grounding, and navigation execution. VLMnav motivates asking a model to choose from a fixed set of navigation actions. This project adapts those ideas into a low-cost indoor prototype and a feasibility-testing workflow.

The intended action set is limited to:

- `move_forward`
- `turn_left`
- `turn_right`
- `stop`
- `search`

This restricted action set is suitable because it can be tested in the laptop-only setup and later mapped to motor commands in the physical robot approaches. The main contribution of the methodology is the design, implementation, and evaluation of a prompt-engineered indoor navigation pipeline that can be tested first with a laptop and then transferred to a low-cost robot platform.

## 3.2 Research Design and Project Workflow

The project follows an iterative prototyping methodology. This approach is suitable because the system contains prompt engineering, computer vision, model inference, safety validation, and optional physical motor-control components. Each component must be tested separately before the complete robot is evaluated in indoor navigation scenarios.

The methodology is organized around three main activities. First, the laptop-only setup is used to test model latency, prompt output, live camera processing, and action-selection behavior. Second, the physical robot alternatives are prepared and compared. Third, the selected physical approach connects webcam input, model output, ESP32 ultrasonic readings, and motor-driver commands to evaluate simple indoor robot movement.

### 3.2.1 Methodology Alignment with Research Objectives

The methodology is aligned with the project objectives as shown in Table 3.1.

**Table 3.1: Methodology Alignment with Research Objectives**

| Research Objective | Method Used | Expected Output | Evaluation |
|---|---|---|---|
| Objective 1: To test whether the selected model can process live camera input and prompt-based navigation decisions | Use the laptop-only feasibility setup with the built-in laptop camera and local GPU | Model latency, structured prompt output, and action recommendation results | Camera capture test, prompt validity test, action selection test, latency measurement |
| Objective 2: To compare practical low-cost implementation approaches for the physical robot | Compare Raspberry Pi with remote GPU, Google Dev Board onboard inference, and laptop-only feasibility testing | Selected implementation path or justified development sequence | Hardware availability, model compatibility, latency, cost, wiring complexity, reliability |
| Objective 3: To connect prompt output, webcam input, and obstacle sensing to simple robot actions | Use visual grounding or VLM-based action selection to choose from `move_forward`, `turn_left`, `turn_right`, `stop`, and `search`, then validate against ESP32 distance readings in physical approaches | Validated action command sent to the ESP32 motor-control layer | Visual grounding correctness, action selection accuracy, obstacle stop behavior, movement success, latency, failure analysis |

### 3.2.2 Overall Project Workflow

The workflow begins with the laptop-only test. This first phase checks whether the available GPU laptop can process live video and produce useful navigation actions quickly enough. If the model is too slow, the prompt, model, image resolution, or inference strategy must be adjusted before building the robot.

After the laptop-only test, the physical robot approaches are compared. Approach 1 uses a Raspberry Pi on the robot and a GPU laptop or desktop as a remote model server. Approach 2 uses a Google Dev Board for more standalone onboard inference. Both physical approaches use an ESP32 to handle the motor driver and ultrasonic sensors.

The workflow is summarized in Figure 3.1.

**Figure 3.1: Proposed project workflow**

```text
Define Navigation Action Set and Prompt Output Schema
        |
        v
Run Laptop-Only Feasibility Test
        |
        v
Measure Model Latency and Prompt Validity
        |
        v
Compare Physical Robot Approaches
        |
        +--> Raspberry Pi + ESP32 + Remote GPU
        |
        +--> Google Dev Board + ESP32
        |
        v
Select Practical Implementation Path
        |
        v
Integrate Webcam, ESP32, Motor Driver, and Model Output
        |
        v
Validate Action with Obstacle Status
        |
        v
Execute or Display Action
        |
        v
Evaluate Scenario Result

If output is invalid, uncertain, too slow, or unsafe:
        -> stop, log failure, adjust prompt, model, or hardware approach
```

### 3.2.3 Development Workflow

The development workflow is divided into stages so that model and hardware risks can be reduced before full robot integration.

**Table 3.2: Development Workflow**

| Stage | Activity | Expected Output |
|---|---|---|
| Stage 1 | Define the navigation action set, structured output fields, and test instructions | Fixed schema and approved action list |
| Stage 2 | Build the laptop-only feasibility test using laptop camera and local GPU | Working live-camera action-selection test |
| Stage 3 | Measure model latency, prompt validity, action selection behavior, and failure cases | Evidence for whether the GPU laptop can support real-time testing |
| Stage 4 | Prepare Approach 1 design: Raspberry Pi, ESP32, webcam, motor driver, ultrasonic sensors, and remote GPU server | Physical robot architecture using remote inference |
| Stage 5 | Prepare Approach 2 design: Google Dev Board, ESP32, webcam, motor driver, and ultrasonic sensors | Physical robot architecture using onboard embedded inference |
| Stage 6 | Compare both physical approaches using cost, availability, latency, model compatibility, and wiring complexity | Selected physical implementation path |
| Stage 7 | Flash ESP32 firmware for ultrasonic sensing and motor-driver control | ESP32 can report distance and execute basic movement commands |
| Stage 8 | Integrate camera capture, model output, ESP32 status, and safety validation | End-to-end command flow from instruction to safe action |
| Stage 9 | Test controlled indoor scenarios with door, signboard, chair, table, and corridor targets | Scenario results and movement observations |
| Stage 10 | Collect, analyse, and report results, limitations, and future improvements | Final evaluation and discussion |

## 3.3 Proposed System Architecture

The proposed system architecture adapts the LM-Nav idea into a practical low-cost workflow. LM-Nav separates language understanding, visual grounding, and navigation execution. In this project, those stages are implemented as prompt processing, structured navigation output generation, webcam-based visual grounding or VLM action selection, safety validation, and either displayed human-followed actions or ESP32-based motor-driver control.

**Figure 3.2: Proposed system architecture**

```text
User Natural Language Prompt
        |
        v
Prompt Engineering Module
        |
        v
Structured Navigation Output
        |
        v
Webcam Image Capture
        |
        v
Visual Grounding or VLM Action Selection
        |
        v
Decision and Safety Validation Logic
        |
        +--> Laptop-Only Test: Display Action to Human Operator
        |
        +--> Physical Robot: Check ESP32 Ultrasonic Status
                    |
                    v
              Send Command to ESP32
                    |
                    v
              Motor Driver and DC Motors
                    |
                    v
              Robot Movement in Indoor Test Area
```

The architecture is intentionally modular. If the system fails, the failure can be traced to a specific component: prompt output, visual grounding, action selection, model latency, ESP32 communication, motor-driver control, or physical movement. This is important for an FYP because the project must be evaluated systematically rather than only judged by whether the robot moves.

### 3.3.1 Implementation Approaches and Hardware Roles

The three implementation approaches are shown in Table 3.3.

**Table 3.3: Proposed Implementation Approaches and Hardware Roles**

| Approach | Main Components | Role in the Project | Main Risk |
|---|---|---|---|
| Approach 1: Raspberry Pi with remote GPU | Raspberry Pi, USB webcam, ESP32, motor driver, ultrasonic sensors, DC motors, chassis, GPU laptop or desktop over WiFi | Real robot approach where the Raspberry Pi handles robot-side camera, communication, and safety validation while the GPU computer performs model inference | WiFi latency and dependence on external GPU computer |
| Approach 2: Google Dev Board with ESP32 | Google Dev Board, USB webcam, ESP32, motor driver, ultrasonic sensors, DC motors, chassis | More standalone physical robot approach where the Google Dev Board runs onboard model or TFLite-style inference and ESP32 handles motors and sensors | Model compatibility and embedded inference speed |
| Approach 3: Laptop-only feasibility test | GPU laptop and built-in laptop camera or external webcam | Early feasibility approach for testing prompts, live camera input, model latency, and action choice before buying or wiring full robot hardware | Not a physical robot and has no motor or ultrasonic sensing |

For the physical robot approaches, the ESP32 is responsible for real-time ultrasonic reading and motor-driver control. This keeps timing-sensitive tasks separate from AI inference. The AI layer should only send validated high-level commands such as `FWD`, `LEFT`, `RIGHT`, `SEARCH`, and `STOP`.

## 3.4 System Requirements, Constraints, and Acceptance Criteria

The system requirements are defined according to the actual scope of the updated project. The prototype must be able to accept a simple navigation instruction, process the instruction into a structured format, use webcam input for grounding or action selection, and either display a recommended movement in the laptop-only setup or move the robot using validated ESP32 commands in the physical setup.

**Table 3.4: Requirements and Acceptance Criteria**

| Requirement | Specification | Verification Method | Pass Criteria |
|---|---|---|---|
| Natural language input | The system accepts simple indoor navigation instructions | Instruction input test | Instruction is received without manual rewriting |
| Structured prompt output | The prompt produces a machine-readable response | JSON validation | Required fields are present and parseable |
| Landmark extraction | The system identifies target objects such as door, signboard, chair, table, or corridor | Comparison with expected labels | Correct target or landmark is extracted |
| Spatial relation extraction | The system identifies relations such as near, beside, after, or toward when present | Manual annotation comparison | Relevant relation is represented correctly |
| Webcam capture | Laptop, Raspberry Pi, or Google Dev Board captures the current indoor scene | OpenCV or camera test | Image frame is captured successfully |
| Visual grounding or action selection | The system connects the prompt output and image to an action decision | Scenario-based test | Selected action is relevant to the instruction and current view |
| Model latency | The selected model produces an action within an acceptable delay | Latency logging | Delay is acceptable for slow indoor testing |
| Ultrasonic sensing | ESP32 reads ultrasonic sensors and reports basic proximity status in physical approaches | ESP32 serial/status test | Distance values are received and can trigger stop behavior |
| Motor-driver control | ESP32 sends valid output to the motor driver in physical approaches | Movement test | Robot performs the intended basic motion |
| Safety validation | Uncertain, invalid, or unsafe AI output is not executed directly | Failure-case test | System stops or refuses uncertain action instead of moving unsafely |

The project has several constraints. The physical robot operates only in controlled indoor environments. The webcam does not provide direct depth information. The baseline project does not include full SLAM, LiDAR mapping, large VLA model deployment, or advanced learned navigation policies. These constraints are acceptable because the goal is to build and evaluate a baseline prompt-engineered prototype.

## 3.5 Data, Test Environment, and Experimental Materials

The project uses simple indoor navigation instructions and webcam images from controlled test areas. The instruction set is designed to represent common commands that a user may give to a small indoor mobile robot.

**Table 3.5: Instruction Categories and Indoor Landmarks**

| Category | Example Instruction | Target Landmark or Relation | Purpose |
|---|---|---|---|
| Single landmark | "Go to the door." | door | Test basic target extraction |
| Object search | "Find the signboard." | signboard | Test search behavior when target may not be centered |
| Landmark with relation | "Move toward the chair near the table." | chair near table | Test spatial relation extraction |
| Corridor navigation | "Move forward in the corridor." | corridor | Test action interpretation from scene context |
| Stop condition | "Stop at the door." | door and stop action | Test stopping behavior when target is detected |
| Ambiguous instruction | "Go there" or "Find it" | unclear target | Test uncertainty handling and safe stop behavior |

The indoor test environment will include simple visual landmarks such as a door, table, chair, signboard, corridor, wall, and room entrance. The environment should be controlled enough for safe movement but varied enough to test different prompt and grounding outcomes.

**Table 3.6: Experimental Materials**

| Material | Function |
|---|---|
| Navigation instruction list | Input for prompt engineering experiments |
| Expected landmark labels | Ground truth for extraction accuracy |
| Webcam images or live camera frames | Input for visual grounding and action selection |
| GPU laptop | Runs laptop-only testing and may run the remote model server for Approach 1 |
| Built-in laptop camera or external webcam | Provides RGB input for the laptop-only feasibility setup |
| Raspberry Pi | Robot-side controller for Approach 1 |
| Google Dev Board | Onboard embedded inference controller for Approach 2 |
| ESP32 | Reads ultrasonic sensors and controls the motor driver in physical robot approaches |
| Motor driver | Receives ESP32 control signals and drives DC motors |
| Ultrasonic sensors | Provide simple obstacle or proximity readings through the ESP32 |
| Four DC motors and chassis | Physical robot movement platform |
| Battery pack and voltage regulators | Provide mobile power for the robot electronics and motors |
| Result log file | Stores instructions, prompt outputs, selected actions, movement results, latency, and failures |

**Table 3.7: Software, Model, and Platform Requirements**

| Item | Purpose | Planned Tool or Example |
|---|---|---|
| Programming language | Implement prompt processing, camera capture, decision logic, communication, and logging | Python |
| Webcam processing | Capture and process RGB frames | OpenCV |
| Prompt processing model | Extract structured navigation information | GPT-style model, local LLM, rule-based parser, or available API model |
| Visual grounding model | Match text target with webcam image or answer visual questions | CLIP, OpenCLIP, VLM, TFLite model, or rule-based fallback |
| Laptop-only runtime | Run early feasibility test with camera and GPU | Python, OpenCV, PyTorch or selected model runtime |
| Remote GPU server | Run heavier model inference for Approach 1 | FastAPI or Flask server on GPU laptop or desktop |
| Raspberry Pi robot client | Capture frames, call GPU server, read ESP32 status, and validate action | Python, OpenCV, pyserial, requests or httpx |
| Google Dev Board runtime | Run onboard embedded inference for Approach 2 | Python, OpenCV, TFLite runtime, PyCoral if applicable |
| ESP32 firmware | Read ultrasonic sensors and control motor driver | Arduino IDE, PlatformIO, or ESP-IDF |
| Result storage | Record output and evaluation data | CSV, JSON, Markdown table, or spreadsheet |

## 3.6 Prompt Engineering Design

Prompt engineering is the central research element of the project. The prompt must convert a user instruction into a structured navigation representation that can be parsed by the selected compute platform. The output should be simple enough for laptop-only testing and physical robot execution, but detailed enough to preserve target, landmark, relation, action goal, and uncertainty information.

**Table 3.8: Prompt Templates for Evaluation**

| Prompt Type | Description | Expected Output |
|---|---|---|
| Baseline landmark prompt | Extracts only the main landmark from the instruction | Target landmark list |
| Structured navigation prompt | Requires fixed JSON fields for target, landmarks, relation, action goal, suggested action, and uncertainty | Parseable JSON-style navigation output |
| Relation-aware prompt | Emphasizes spatial phrases such as near, beside, toward, after, and at | Target plus spatial relation |
| Action-choice prompt | Restricts the model to choose from `move_forward`, `turn_left`, `turn_right`, `stop`, and `search` | Valid action label |
| Safety-aware prompt | Requires the model to return high uncertainty or stop when instruction is unclear | Safe output for ambiguous instructions |

The structured output format is shown below.

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

For a relation-based instruction, the expected output may be:

```json
{
  "target": "chair",
  "landmarks": ["chair", "table"],
  "spatial_relation": "chair near table",
  "action_goal": "move toward the chair that is near the table",
  "suggested_action": "search",
  "uncertainty": "medium"
}
```

**Table 3.9: Structured Output Fields**

| Field | Description | Example |
|---|---|---|
| `target` | Main object or place the robot should find or approach | `door` |
| `landmarks` | Important objects or places mentioned in the instruction | `["chair", "table"]` |
| `spatial_relation` | Relation between target and reference object, if present | `chair near table` |
| `action_goal` | Short natural-language goal for decision logic or logging | `find and move toward the door` |
| `suggested_action` | Proposed action from the fixed action set | `move_forward` |
| `uncertainty` | Confidence label used for safety validation | `low`, `medium`, or `high` |

The selected compute platform will validate this output before execution or display. If required fields are missing, if the action is outside the approved action set, if uncertainty is high, or if ESP32 ultrasonic readings indicate that the path is too close to an obstacle, the system should stop and log the failure instead of moving.

## 3.7 Webcam-Based Visual Grounding and Action Selection

After the prompt output is generated, the system captures an image from the webcam. The image is used to decide whether the target appears in the current view and which action should be taken. The visual grounding stage may use CLIP, OpenCLIP, a VLM, a TFLite model, or a simplified image-based method depending on the selected implementation approach.

For CLIP or OpenCLIP-style grounding, the text query may be the target alone, such as `door`, or a prompt-expanded query, such as `an indoor door in a corridor`. The basic score is:

```text
score(image, text) = cosine_similarity(E_image(image), E_text(text))
```

For VLM-style action selection, the model may be asked to choose the best action from the approved action set based on the instruction and current image. This follows the idea of VLMnav but is simplified for the FYP robot.

**Table 3.10: Visual Grounding and Action Selection Strategies**

| Strategy | Description | Suitability for This Prototype |
|---|---|---|
| Direct target grounding | Compare webcam image with the target word such as `door` or `chair` | Simple baseline for single-landmark instructions |
| Prompt-expanded grounding | Use a richer text query such as `a signboard on an indoor wall` | Useful when target needs more context |
| Relation-aware grounding | Include relation text such as `chair near table` | Useful for relation-based instructions, but may be harder with a single RGB image |
| VLM action-choice prompt | Ask the model to choose from the fixed action set using image and instruction | Useful for direct decision making, but output must be validated |
| TFLite or Edge TPU model | Use a lightweight classifier or detector on the Google Dev Board | Suitable if the model is compatible with embedded inference |
| Rule-based fallback | If target is uncertain, use `search` or `stop` | Important for safety and baseline robustness |

The grounding result is not treated as perfect. The system will log cases where the target is not visible, the model selects the wrong action, or the robot needs to search.

## 3.8 Robot Action Set and Motor Command Mapping

The robot uses a small action set because the prototype is intended for controlled indoor testing. In the laptop-only approach, the selected action is displayed to the human operator. In the physical robot approaches, the selected high-level action is mapped to an ESP32 command, and the ESP32 controls the motor driver.

**Table 3.11: Action Set and Motor Command Mapping**

| Action | Meaning | Laptop-Only Behavior | ESP32 Motor-Driver Command |
|---|---|---|---|
| `move_forward` | Move forward slowly | Human operator walks forward slowly | `FWD` |
| `turn_left` | Rotate or steer left | Human operator turns laptop/body left | `LEFT` |
| `turn_right` | Rotate or steer right | Human operator turns laptop/body right | `RIGHT` |
| `stop` | Stop movement immediately | Human operator stops | `STOP` |
| `search` | Rotate slowly or scan for target | Human operator slowly scans the area | `SEARCH` |

The ESP32 should stop the motors if it receives an unknown command, if no command is received within a timeout, or if an obstacle is detected within the selected safety threshold.

## 3.9 Approach Comparison and Selection Criteria

The project does not assume that all three approaches are final physical robots. Instead, they are used as a staged development and selection strategy. Approach 3 reduces early hardware cost and tests whether the model is fast enough. Approach 1 is the strongest physical robot option if heavy model inference is needed. Approach 2 is the most standalone option if the selected model can run efficiently on the Google Dev Board.

**Table 3.12: Comparison of Implementation Approaches**

| Criterion | Approach 1: Raspberry Pi + Remote GPU | Approach 2: Google Dev Board | Approach 3: Laptop-Only Test |
|---|---|---|---|
| Physical robot movement | Yes | Yes | No |
| Motor and ultrasonic sensing | ESP32 handles both | ESP32 handles both | Not included |
| Camera source | Robot-mounted USB webcam | Robot-mounted USB webcam | Built-in laptop camera or external webcam |
| Model compute | GPU laptop or desktop over WiFi | Onboard embedded board | Local GPU laptop |
| Main strength | Supports heavier models while keeping robot hardware simple | More standalone embedded robot design | Lowest-cost feasibility test |
| Main weakness | WiFi latency and external-computer dependence | Model compatibility and limited onboard compute | Not a true robot platform |
| Best use | Main physical robot if VLM or CLIP inference is heavy | Physical robot if lightweight model is sufficient | Phase 1 model and latency testing |

The final physical approach should be chosen based on hardware availability, measured latency, model compatibility, and implementation time.

## 3.10 Mechanical Design and Physical Integration

The physical robot chassis will be designed as a purpose-built low-cost platform if Approach 1 or Approach 2 is selected for physical testing. The design is prepared in Autodesk Fusion 360 so that the Raspberry Pi or Google Dev Board, ESP32, webcam, ultrasonic sensors, motor driver, battery holder, and four DC motors can be mounted in a controlled and repeatable layout. The 3D model is not treated as the main research contribution, but it is important because the sensor placement and component arrangement affect the reliability of the indoor navigation experiment.

The proposed chassis should provide mounting space for the webcam at the front of the robot, ultrasonic sensors around the robot body, and accessible mounting positions for the controller boards. The battery holder should be placed low on the chassis to improve stability. The design should also allow the wiring to be routed safely so that cables do not touch the wheels or motors.

**Figure 3.3: Placeholder for proposed Fusion 360 3D robot model**

```text
Insert Fusion 360 3D model image here.

Suggested image content:
- Isometric view of the complete 3D-printed chassis
- Mounting position for Raspberry Pi or Google Dev Board
- Mounting position for ESP32
- Mounting position for motor driver
- Webcam position
- Ultrasonic sensor positions
- Four DC motor and wheel positions
- Battery holder position
```

### 3.10.1 Suggested Circuit Architecture

The circuit architecture is divided into three layers: computing, sensing/control, and motion. The Raspberry Pi or Google Dev Board performs high-level prompt processing and decision logic in the physical robot approaches. The ESP32 handles ultrasonic sensor readings and motor-driver commands. This separation is suitable for an FYP prototype because each layer can be tested independently before full integration.

**Figure 3.4: Suggested circuit architecture**

```text
Battery Pack
        |
        v
Main Power Switch and Fuse
        |
        +--> Motor Power Rail
        |       |
        |       v
        |   Motor Driver
        |       |
        |       +--> Front Left DC Motor
        |       +--> Front Right DC Motor
        |       +--> Rear Left DC Motor
        |       +--> Rear Right DC Motor
        |
        +--> Regulated Logic Supply
                |
                +--> Raspberry Pi or Google Dev Board
                |       |
                |       +--> USB Webcam
                |       +--> USB or UART link to ESP32
                |
                +--> ESP32
                        |
                        +--> Front Ultrasonic Sensor
                        +--> Left Ultrasonic Sensor
                        +--> Right Ultrasonic Sensor
                        +--> Rear Ultrasonic Sensor
                        +--> Motor Driver Input Pins

All grounds are connected to a common ground reference.
```

The final circuit diagram should show the battery connection, power switch, regulator, selected compute board, ESP32, ultrasonic sensors, motor driver outputs, and motors. If the ultrasonic sensors are powered at 5 V, the echo signals should be reduced to 3.3 V before entering ESP32 input pins. This can be done using a voltage divider or logic-level shifter. The exact pin numbers should be confirmed after the physical boards and connectors are finalized.

**Figure 3.5: Placeholder for final circuit diagram**

```text
Insert final circuit diagram picture here.

Suggested circuit diagram content:
- Battery pack, switch, fuse, and regulator
- Raspberry Pi or Google Dev Board power input and USB webcam connection
- Compute board serial connection to ESP32
- ESP32 trigger and echo pins to ultrasonic sensors
- ESP32 motor-control pins to motor driver input
- Motor driver output to four DC motors
- Common ground connection
- Emergency stop or manual power switch
```

## 3.11 Company, Software, and Tool Involvement

The project does not involve industrial sponsorship. However, several hardware and software vendors, chip manufacturers, and open-source tools are used in the prototype. Table 3.13 identifies the companies or organizations related to the selected components and software tools. For final submission, the exact supplier name should be checked against the purchase receipt or product label, especially for unbranded or third-party motor-driver boards.

**Table 3.13: Company, Component, and Software Involvement**

| Component or Tool | Company or Organization | Involvement in This Project | Notes for Final Report |
|---|---|---|---|
| Raspberry Pi | Raspberry Pi Ltd | Candidate robot-side controller for Approach 1 | Used if remote GPU architecture is selected |
| Google Dev Board or Coral-style board | Google | Candidate onboard embedded AI controller for Approach 2 | Exact board and inference support must be confirmed |
| ESP32 microcontroller | Espressif Systems | Ultrasonic sensor controller and motor-driver command controller | Used in physical robot approaches |
| GPU laptop or desktop | Exact manufacturer depends on available machine | Runs laptop-only feasibility test and may run the remote model server | Record GPU model and memory for latency reporting |
| USB webcam or built-in laptop camera | Manufacturer depends on available camera | RGB visual input for indoor scene capture | Webcam is treated as a low-cost RGB camera |
| Motor driver | Supplier to be confirmed | Converts ESP32 motor-control signals into motor power output | Exact driver should be recorded after purchase |
| Autodesk Fusion 360 | Autodesk | 3D modelling software for the robot chassis design | Used for mechanical design documentation |
| Python | Python Software Foundation | Main programming language for prompt parsing, decision logic, camera capture, communication, and logging | Used in all three approaches |
| OpenCV | OpenCV project | Webcam frame capture and basic image processing | Used before advanced CLIP or VLM grounding is added |
| Arduino IDE, PlatformIO, or ESP-IDF | Arduino, PlatformIO Labs, or Espressif Systems | Firmware development for ESP32 | Tool choice depends on the final firmware workflow |
| diagrams.net or draw.io | JGraph or diagrams.net project | Diagram preparation for system architecture and circuit documentation | Used for report figures and flowcharts |

## 3.12 Software Implementation and Coding

The baseline coding is divided according to the three approaches. The laptop-only program runs the camera, model, and action display on the GPU laptop. The Raspberry Pi approach uses a robot-side client and a remote GPU server. The Google Dev Board approach uses an onboard embedded inference controller. The ESP32 firmware is shared by the two physical robot approaches and handles ultrasonic sensing and motor-driver control.

**Table 3.14: Source Code Modules for Baseline Implementation**

| File or Module | Hardware Target | Purpose | Status |
|---|---|---|---|
| `docs/approach_1_raspberry_pi_esp32_remote_gpu.md` | Documentation | Full build guide for Raspberry Pi, ESP32, webcam, motor driver, and remote GPU setup | Provided |
| `docs/approach_2_google_dev_board_esp32.md` | Documentation | Full build guide for Google Dev Board, ESP32, webcam, motor driver, and ultrasonic setup | Provided |
| `docs/approach_3_laptop_only_model_test.md` | Documentation | Full build guide for laptop-only feasibility testing | Provided |
| `src/laptop_only_test/live_navigation_test.py` | GPU laptop | Planned main program for laptop-only camera, model inference, action display, and logging | Planned |
| `src/raspberry_pi_robot/robot_client.py` | Raspberry Pi | Planned robot-side client for camera capture, ESP32 communication, remote GPU request, and safety validation | Planned |
| `src/gpu_server/server.py` | GPU laptop or desktop | Planned remote model server for Approach 1 | Planned |
| `src/google_dev_board_robot/robot_controller.py` | Google Dev Board | Planned onboard controller for camera capture, embedded inference, ESP32 communication, and validation | Planned |
| `firmware/esp32_robot_controller/esp32_robot_controller.ino` | ESP32 | Firmware template for ultrasonic sensing and motor-driver command control | Provided |
| `firmware/esp32_ultrasonic_hub/esp32_ultrasonic_hub.ino` | ESP32 | Optional sensor-only firmware for testing ultrasonic JSON output before motor integration | Provided |
| `docs/circuit_wiring_guide.md` | Documentation | Text-form wiring guidance for the updated physical robot architecture | Draft guide |

The common control logic follows the structure shown below:

```text
Receive user instruction
Generate structured prompt output
Capture webcam frame
Run visual grounding or action-selection model
Select proposed action from fixed action set
If output is invalid, uncertainty is high, latency is unacceptable, or obstacle is detected:
    execute or display stop
Else:
    display action in laptop-only setup
    or send validated command to ESP32 in physical setup
Log instruction, structured output, sensor status if available, final action, and latency
```

This coding structure is influenced by LM-Nav and VLMnav but simplified for the proposed hardware. CLIP, OpenCLIP, TFLite, or a VLM can be added depending on the selected approach. VLMaps, HOV-SG, ViNT, NoMaD, NaVid, Uni-NaVid, and NaVILA are not implemented in the first prototype because they require additional sensors, mapping, model deployment, or compute resources beyond the initial FYP scope.

## 3.13 Equations and Decision Rules

The project uses simple equations and decision rules to evaluate the prototype. The equations are not intended to represent a complete navigation theory; they provide measurable criteria for prompt quality, visual grounding, action selection, ultrasonic safety checking, and response time.

**Table 3.15: Main Equations and Decision Rules**

| Equation or Rule | Description | Use in Evaluation |
|---|---|---|
| `d_cm = t_echo_us / 58` | Approximate ultrasonic distance where `t_echo_us` is the echo pulse duration in microseconds | Converts ESP32 ultrasonic timing into distance in centimetres |
| `S(I,T) = cosine(E_image(I), E_text(T))` | CLIP or OpenCLIP similarity between image embedding and text embedding | Optional visual grounding score when CLIP-style grounding is used |
| `Prompt Validity = N_valid / N_total * 100 percent` | Percentage of prompt outputs that contain required fields and valid JSON structure | Measures structured output reliability |
| `Accuracy = N_correct / N_total * 100 percent` | General accuracy formula for landmark extraction, relation extraction, grounding, or action selection | Allows consistent metric reporting |
| `T_total = T_prompt + T_capture + T_grounding + T_sensor + T_comm` | Total response time from instruction input to action output | Measures system latency |
| `a_exec = stop if invalid output, high uncertainty, unsafe distance, timeout, or invalid action; otherwise a_selected` | Safety validation rule before displaying or executing an action | Prevents uncertain AI output from becoming unsafe movement |
| `Movement Success Rate = N_success / N_scenarios * 100 percent` | Percentage of indoor scenarios where the robot or human-followed test performs the intended simple action | Measures scenario performance |

For ultrasonic sensing, an obstacle is considered present when the smallest valid distance from the ESP32 is lower than the selected safety threshold. In the baseline configuration, the threshold may begin at 25 cm, but this value should be adjusted during testing depending on robot speed, braking distance, and sensor reliability.

## 3.14 Implementation Procedure

The implementation procedure follows ten stages. Each stage has a verification method so that the project can be developed and tested systematically.

**Table 3.16: Implementation Procedure**

| Stage | Activity | Verification | Expected Result |
|---|---|---|---|
| Stage 1 | Define action set, prompt schema, test instructions, and logging format | Review schema and sample instructions | Common evaluation format is ready |
| Stage 2 | Set up laptop-only camera capture and model runtime | Run camera and model test scripts | Laptop captures images and produces action output |
| Stage 3 | Measure laptop-only latency and prompt output quality | Log response time and JSON validity | Model feasibility is confirmed or limitations are identified |
| Stage 4 | Prepare Raspberry Pi and remote GPU server design | Test network request from Pi to GPU server | Approach 1 communication path is verified |
| Stage 5 | Prepare Google Dev Board model runtime | Test camera and embedded inference | Approach 2 onboard processing feasibility is verified |
| Stage 6 | Flash and test ESP32 firmware for ultrasonic sensing and motor-driver control | Compare sensor output with measured distances and send motor commands | ESP32 reports usable distance and controls motor outputs |
| Stage 7 | Compare physical approaches and select implementation path | Decision table and latency/cost comparison | Selected physical prototype path is justified |
| Stage 8 | Integrate selected compute platform, webcam, ESP32 status, and action validation | End-to-end dry-run test | System produces safe validated commands |
| Stage 9 | Test indoor navigation scenarios with door, signboard, chair, table, and corridor | Scenario checklist and video/log review | System performs basic movement or action recommendations |
| Stage 10 | Collect and analyse results | Metric calculation and failure-case analysis | Final performance, limitations, and future work are documented |

## 3.15 Testing and Validation Plan

Testing is divided into module testing, integration testing, and scenario testing. Module testing checks the prompt, webcam, model inference, ESP32 ultrasonic sensing, communication, and motor-driver control separately. Integration testing checks whether the system can process an instruction, capture an image, select an action, check ESP32 proximity readings when available, and display or execute a safe command. Scenario testing evaluates the system in controlled indoor environments.

**Table 3.17: Testing and Validation Matrix**

| Test Stage | Test Setup | Metric | Pass Criteria |
|---|---|---|---|
| Prompt format test | Input instructions only | Prompt output validity | Output follows required JSON fields |
| Landmark extraction test | Instructions with known targets | Landmark extraction accuracy | Correct target and landmark list are extracted |
| Spatial relation test | Instructions with relation labels | Spatial relation extraction accuracy | Relation such as `chair near table` is represented correctly |
| Laptop camera test | Built-in laptop camera or external webcam | Frame capture success | Image frame is captured reliably |
| Physical robot webcam test | USB webcam connected to Raspberry Pi or Google Dev Board | Frame capture success | Image frame is captured reliably |
| Model latency test | Laptop GPU, remote GPU, or Google Dev Board | Response time | Command is produced within acceptable delay for prototype testing |
| Visual grounding test | Webcam image and target text | Grounding correctness | Correct target is identified or uncertainty is reported |
| Action selection test | Instruction and current webcam view | Action selection accuracy | Selected action matches expected behavior |
| ESP32 ultrasonic test | Ultrasonic sensors connected to ESP32 | Distance reading availability | ESP32 readings are available for simple safety checks |
| ESP32 motor-driver test | ESP32 connected to motor driver | Movement correctness | Motors move forward, turn, search, or stop correctly |
| Full scenario test | Indoor target such as door, signboard, chair, table, or corridor | Scenario success | System performs the intended simple navigation behavior |
| Safety test | Ambiguous instruction, invalid model output, obstacle, or timeout | Safe failure behavior | System stops or refuses uncertain action |

## 3.16 Evaluation Metrics

The evaluation focuses on both AI output quality and robot behavior. This is important because a prompt may produce a correct text output while the robot still fails to move correctly, or the robot may move correctly even when visual grounding is weak.

**Table 3.18: Evaluation Metrics**

| Metric | Description |
|---|---|
| Prompt output validity | Percentage of outputs that contain all required structured fields |
| Landmark extraction accuracy | Percentage of instructions where the correct target or landmarks are extracted |
| Spatial relation extraction accuracy | Percentage of relation-based instructions where the relation is correctly represented |
| Visual grounding correctness | Percentage of cases where the target is correctly matched or identified in the webcam view |
| Action selection accuracy | Percentage of cases where the selected action matches the expected action |
| Latency or response time | Time from user instruction and frame capture to selected command |
| Robot movement success | Percentage of physical robot scenarios where the robot performs the intended basic movement |
| Human-followed scenario success | Percentage of laptop-only scenarios where the displayed action reasonably guides the human operator |
| Safe stop rate | Percentage of uncertain, invalid, timeout, or obstacle cases where the system stops instead of executing unsafe output |
| Failure-case count | Number and type of failures such as wrong target, invalid JSON, weak grounding, wrong turn, communication error, motor error, or unsafe suggestion |

Qualitative analysis will also be conducted. Failure cases will be grouped into prompt errors, grounding errors, action-selection errors, latency errors, serial communication errors, motor-control errors, and environmental limitations. This helps identify whether future work should improve prompts, visual grounding, hardware, or navigation control.

## 3.17 Safety, Ethics, and Practical Considerations

Safety is important even though the robot is a low-cost indoor prototype. For the laptop-only setup, the human operator must walk slowly, avoid crowded or unsafe areas, and stop immediately if the action output is unclear. For the physical robot setup, the robot should move at low speed during testing. All tests should be conducted in a controlled indoor area with sufficient space. A manual stop or emergency power switch should be available during movement tests.

The ESP32 ultrasonic sensors should be used as a simple proximity safety layer in physical robot approaches, but testing must still be supervised manually because ultrasonic sensors do not provide complete obstacle understanding.

The system should not execute uncertain AI output directly. If the structured output is invalid, if the selected action is not in the approved action set, if the uncertainty is high, if the model times out, or if the ESP32 reports an unsafe obstacle distance, the system should stop and log the case. This prevents a hallucinated or ambiguous model response from becoming an unsafe movement command.

Privacy must also be considered when using a webcam. Testing should avoid capturing identifiable people unless permission is obtained. Images and logs should be used only for project evaluation.

## 3.18 Limitations and Future Work

The proposed prototype has clear limitations. It uses a webcam, so it does not directly estimate dense depth or build a 3D map. The ESP32-based ultrasonic sensing module provides only simple distance cues and is not equivalent to LiDAR or RGB-D mapping. The system uses a simple action set, so it cannot perform full path planning. The laptop-only setup is useful for feasibility testing but is not a physical robot. The Raspberry Pi with remote GPU setup depends on WiFi. The Google Dev Board setup depends on model compatibility and embedded inference speed.

These limitations are acceptable because the project is designed as a baseline research prototype. Future work can improve the system by adding an RGB-D camera, LiDAR, stronger obstacle sensing, map building, VLMaps-style visual-language maps, HOV-SG-style scene graphs, ViNT or NoMaD navigation policies, or more advanced VLM/VLA models. The baseline prototype provides a practical platform for these improvements by establishing the connection between natural language prompts, webcam-based grounding, action selection, ESP32-based ultrasonic safety checking, and motor-driver-based robot movement.

## 3.19 Summary

This chapter presented the methodology for the updated low-cost indoor mobile robot navigation project. The previous unavailable-board plan was removed. The updated methodology is organized around three practical approaches: Raspberry Pi with ESP32 and remote GPU inference, Google Dev Board with ESP32 and onboard embedded inference, and laptop-only feasibility testing using the laptop camera and GPU.

The methodology defines the system architecture, implementation approaches, hardware roles, software tools, prompt engineering design, structured output format, visual grounding and action-selection process, action set, motor-command mapping, implementation stages, testing plan, evaluation metrics, safety considerations, and future work. The project is positioned as a baseline prototype that investigates how structured prompt engineering can support simple indoor navigation decisions while allowing the final physical robot approach to be chosen based on availability, latency, model compatibility, and cost.
