<p align="center">
  <img src="assets/branding/Header.jpg" alt="Prompt Engineering for Mobile Robot Navigation" width="100%">
</p>

# Prompt Engineering for Mobile Robot Navigation

<p align="center">
  A low-cost Raspberry Pi 4 and ESP32 mobile robot that converts a simple
  natural-language goal into restricted, safety-checked movement actions.
</p>

<p align="center">
  <img alt="Raspberry Pi 4" src="https://img.shields.io/badge/Raspberry%20Pi%204-High--Level%20Controller-C51A4A">
  <img alt="ESP32" src="https://img.shields.io/badge/ESP32-Safety%20%26%20Motor%20Control-1F6FEB">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-Visual%20Grounding-5C3EE8">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Laptop%20Demo-2496ED">
  <img alt="Status" src="https://img.shields.io/badge/Status-FYP1%20Complete%20%7C%20FYP2%20Planned-F59E0B">
</p>

## Final Thesis

The final FYP1 thesis, covering Chapters 1 to 5, is available here:

- [2115617_2_AmirFarhanGhaffar.pdf.docx](2115617_2_AmirFarhanGhaffar.pdf.docx)

The thesis is the source of truth for the finalized project scope, methodology,
AI-model research plan, Docker results, limitations, and planned FYP2 work.

## Prototype

<p align="center">
  <img src="figures/chapter_3/figure_3_4_finalized_fusion_360_robot_model.png" alt="Finalized Fusion 360 Raspberry Pi robot model" width="900">
</p>

The physical prototype uses:

- Raspberry Pi 4 for prompt processing, webcam perception, action selection,
  validation, and logging
- ESP32 for ultrasonic sensing, local safety, USB serial, and motor control
- USB webcam, two HC-SR04 sensors, and GY-291/ADXL345 accelerometer
- two MX1508 drivers and four DC gear motors
- protected 3S battery system, regulated power rails, main switch, and fuse

The GY-291/ADXL345 supports acceleration, roll/pitch, motion, vibration, and
shock observations. It does not provide yaw heading.

## Navigation Pipeline

```text
Natural-language instruction
        |
        v
Structured goal and approved action set
        |
        v
USB-webcam visual grounding
        |
        v
Restricted action selection
        |
        v
ESP32 safety validation and motor control
```

Approved actions:

```text
search | turn_left | turn_right | move_forward | stop
```

The ESP32 independently forces `STOP` for obstacles, sensor faults, invalid
commands, or a command timeout.

## Current Results

The completed Docker laptop demonstration accepts:

```text
find the door
```

It uses a fixed-schema prompt result and an OpenCV colour-and-shape detector
tuned to the grey-blue corridor doors used in the test area.

<p align="center">
  <img src="results/docker_demo_screenshots/Screenshot%202026-06-15%20101741.png" alt="Docker demonstration selecting TURN RIGHT for a door on the right" width="820">
</p>

Observed screenshot evidence demonstrates:

| Observed condition | Displayed action |
|---|---|
| No valid door region | `SEARCH` |
| Door detected on the right | `TURN RIGHT` |
| Door reaches the configured apparent-size threshold | `STOP` |

The Docker demonstration validates the high-level software interface. The
laptop was moved manually, and these results are not physical robot movement.

## AI Research Plan

The implemented deterministic parser, OpenCV detector, and rule-based action
selector form the measurable baseline. The thesis proposes three AI candidates
for later comparison:

| Candidate | Research role |
|---|---|
| Quantized TinyLlama | Convert instructions into the fixed navigation schema |
| MobileNetV2-SSD Lite TensorFlow Lite | Lightweight custom indoor-object grounding |
| VLM-NAV-inspired neural classifier | Compare learned and rule-based action selection |

Model output must pass deterministic validation and cannot bypass ESP32 safety.

## Project Status

| Area | Status |
|---|---|
| Final FYP1 thesis, Chapters 1-5 | Complete |
| Fusion 360 design and printable mounts | Complete |
| Mechanical chassis and protected power system | Built |
| Docker `find the door` demonstration | Working |
| Raspberry Pi controller and ESP32 firmware | Implemented |
| Final Raspberry Pi, ESP32, sensor, and motor wiring | In progress |
| Raised-wheel and controlled-floor validation | Planned for FYP2 |
| AI-model comparison and physical navigation measurements | Planned for FYP2 |

## Quick Start: Docker Demo

Requirements:

- Docker Desktop using Linux containers
- browser webcam permission
- local port `8000`

Run from the repository root:

```powershell
docker compose -f docker-compose.laptop-demo.yml up --build
```

Open <http://localhost:8000>, select **Start Camera**, and enter
`find the door`.

Stop the demonstration:

```powershell
docker compose -f docker-compose.laptop-demo.yml down
```

Full instructions:
[Docker Laptop Demonstration Setup](docs/laptop_only_expected_results_setup.md)

## Physical Robot Setup

1. Complete the signal wiring using the
   [Raspberry Pi, ESP32, and MX1508 Wiring Guide](docs/circuit_wiring_guide.md).
2. Flash
   [`firmware/esp32_robot_controller/esp32_robot_controller.ino`](firmware/esp32_robot_controller/esp32_robot_controller.ino).
3. Install Raspberry Pi OS and dependencies using the
   [Raspberry Pi 4 Full Software Setup](docs/raspberry_pi_4_full_software_setup.md).
4. Run the Raspberry Pi controller without `--execute` for the first dry test.
5. Enable movement only during supervised raised-wheel testing.

Example dry run:

```bash
python3 src/raspberry_pi_robot/robot_controller.py \
  --instruction "find the green marker" \
  --camera 0 \
  --serial-device /dev/ttyUSB0
```

The controller always sends `STOP` unless `--execute` is explicitly provided.

## Safety

- Never power motors from Raspberry Pi or ESP32 logic pins.
- Level-shift both 5 V HC-SR04 Echo signals before ESP32 GPIO.
- Keep a common ground between the battery system, power modules, ESP32,
  sensors, and motor drivers.
- Begin motor tests with all wheels raised and the main switch reachable.
- Verify `STOP`, obstacle, sensor-fault, invalid-command, and timeout behaviour
  before any controlled-floor test.

## Repository Structure

| Path | Purpose |
|---|---|
| [`2115617_2_AmirFarhanGhaffar.pdf.docx`](2115617_2_AmirFarhanGhaffar.pdf.docx) | Final FYP1 thesis, Chapters 1-5 |
| [`src/raspberry_pi_robot/`](src/raspberry_pi_robot/) | Raspberry Pi prompt, camera, action, serial, and logging controller |
| [`src/laptop_expected_results/`](src/laptop_expected_results/) | Docker browser-webcam demonstration |
| [`firmware/`](firmware/) | Main ESP32 controller and sensor-only test firmware |
| [`docs/`](docs/) | Wiring, setup, method-selection, and presentation guides |
| [`results/docker_demo_screenshots/`](results/docker_demo_screenshots/) | Captured Docker result screenshots |
| [`simulations/`](simulations/) | Assumption-based obstacle and timeout safety simulations |
| [`figures/`](figures/) | Final report and public-view figures |
| [`drawio/`](drawio/) | Editable and exported report diagrams |
| [`cad/design_sources/`](cad/design_sources/) | Fusion 360 renders, drawing, and design source |
| [`cad/stl/`](cad/stl/) | Printable robot mounts |
| [`assets/`](assets/) | README branding and hardware-component image sources |
| [`scripts/`](scripts/) | Reproducible figure-generation utilities |
| [`github-research-papers/`](github-research-papers/) | Related research implementations used for method study |

## Supporting Documentation

- [FYP1 15-Minute Presentation Script](docs/fyp1_15_minute_presentation_script.md)
- [Research-Paper Method Selection](docs/research_paper_method_selection.md)
- [Docker Laptop Demonstration Setup](docs/laptop_only_expected_results_setup.md)
- [Raspberry Pi 4 Full Software Setup](docs/raspberry_pi_4_full_software_setup.md)
- [Circuit Wiring Guide](docs/circuit_wiring_guide.md)

## Limitations

- The Docker detector is tuned to grey-blue doors in one corridor and is not a
  general semantic door-recognition model.
- Door stopping uses apparent image area, not measured physical distance.
- Two ultrasonic sensors provide limited obstacle coverage.
- The first physical baseline uses coloured-marker grounding.
- Complete physical action validation and AI-model comparison remain FYP2 work.

## Author

**Amir Farhan Bin Ghaffar**<br>
Final Year Project, Department of Mechatronics Engineering<br>
International Islamic University Malaysia
