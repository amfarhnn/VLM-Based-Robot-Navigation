![Header](Header.jpg)

# Prompt Engineering for Mobile Robot Navigation

This Final Year Project develops one low-cost physical robot that connects a
simple natural-language goal with webcam perception and safe movement.

## Finalized Project Purpose

The only physical implementation uses:

- Coral Dev Board for onboard structured prompt processing, USB-webcam capture,
  Edge TPU-compatible target detection, action selection, and logging
- ESP32 for ultrasonic and GY-291 sensing, deterministic safety, UART
  communication, and four-motor control
- two MX1508 motor drivers and four DC gear motors
- the completed protected battery and power system

The first prototype targets a basic goal such as:

```text
find the chair
```

The approved action set is:

```text
move_forward, turn_left, turn_right, search, stop
```

The laptop-only Docker demo is an FYP1 expected-results aid. A browser captures
the webcam, a local Docker container processes frames, and the interface
displays actions for manual laptop movement. It is not another physical project
approach.

## Finalized Architecture

```text
Simple natural-language goal
        |
        v
Coral Dev Board
  - structured prompt parser
  - USB webcam
  - Edge TPU target detector
  - restricted action selection and logging
        |
        | UART3 /dev/ttymxc2, 115200 baud
        v
ESP32
  - two HC-SR04 sensors
  - GY-291 / ADXL345
  - obstacle and timeout safety
  - two MX1508 motor drivers
        |
        v
Four DC gear motors
```

## First Prototype Behaviour

| Condition | Action |
|---|---|
| Unsupported or unclear target | `stop` |
| Target not visible | `search` |
| Target on left or right | `turn_left` or `turn_right` |
| Target centred and not close | `move_forward` |
| Target reaches the goal-size threshold | `stop` |
| Obstacle, invalid command, or command timeout | ESP32 forces `stop` |

## Key Guides

| Document | Purpose |
|---|---|
| [Coral Full Software Setup](docs/coral_dev_board_full_software_setup.md) | Mendel Linux installation through the first physical navigation result |
| [Coral, ESP32, and MX1508 Wiring Guide](docs/circuit_wiring_guide.md) | Exact UART, sensor, and motor-driver signal wiring |
| [Docker Laptop-Only Expected-Results Setup](docs/laptop_only_expected_results_setup.md) | Containerized on-screen action demonstration for FYP1 |
| [Chapter 1 Introduction](chapter_1_introduction.md) | Finalized problem, objectives, and Coral-only scope |
| [Chapter 2 Literature Review](literature_review.md) | Related language-guided navigation research |
| [Chapter 3 Methodology](chapter_3_methodology.md) | Coral-only physical implementation methodology |
| [Chapter 4 Expected Results](chapter_4_results_and_discussion.md) | Expected FYP1 outcomes and required FYP2 measurements |

## Implementation Files

| Path | Purpose |
|---|---|
| `src/coral_robot/robot_controller.py` | Coral prompt parser, Edge TPU detection, action selection, UART, and logging |
| `firmware/esp32_robot_controller/esp32_robot_controller.ino` | ESP32 UART, sensor, safety, and four-motor firmware |
| `src/laptop_expected_results/laptop_navigation_demo.py` | Shared structured-goal and action-selection logic for the laptop demo |
| `src/laptop_expected_results/web_app.py` | Docker browser-webcam processing service |
| `docker-compose.laptop-demo.yml` | Builds and runs the laptop expected-results container |
| `simulations/` | Expected obstacle-stop and timeout simulations |
| `STL/` | Printable robot components |
| `VLM Robot Photos/` | Latest robot renders and design sources |

## Critical Wiring Summary

```text
Coral UART3 TX pin 7  -> ESP32 GPIO 16 / UART2 RX
Coral UART3 RX pin 11 <- ESP32 GPIO 17 / UART2 TX
Coral GND pin 9       -> ESP32 GND

Rear-right motor control: ESP32 GPIO 19 and GPIO 23
```

Use level shifting on both 5 V HC-SR04 Echo signals. Never connect motor power
to Coral or ESP32 logic pins.

## Generated Thesis Files

- `thesis_tables.xlsx`
- `chapter_1_introduction.docx`
- `chapter_2_literature_review.docx`
- `chapter_3_methodology.docx`
- `chapter_4_results_and_discussion.docx`
- `thesis_chapters_1_to_4.docx`
- `thesis_chapters_1_to_4.pdf`

Tables are maintained in `thesis_tables.xlsx` for manual Word insertion. The
generated DOCX files retain table captions without embedding table images.

Regenerate the Excel workbook and DOCX files with:

```powershell
uv run --with openpyxl --with pillow python scripts\build_chapter_docx.py
```

Run the laptop-only expected-results demo with:

```powershell
docker compose -f docker-compose.laptop-demo.yml up --build
```

Then open `http://localhost:8000`.

## Development Priority

1. Complete and verify the Coral-to-ESP32 and ESP32-to-MX1508 wiring.
2. Confirm `PING`, sensor JSON, `STOP`, and raised-wheel motor actions.
3. Install and verify Mendel Linux, webcam capture, and Edge TPU inference.
4. Run the Coral controller in dry-run mode.
5. Demonstrate supervised `find the chair` physical movement.
6. Record measured results before adding custom landmark classes or more
   complex instructions.
