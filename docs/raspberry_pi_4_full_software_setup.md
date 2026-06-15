# Raspberry Pi 4 Full Software Setup

This is the only finalized physical implementation for the project. The first
prototype accepts `find the green marker`, uses the USB webcam to locate the
marker, selects a restricted action, and sends the action to the ESP32 through
USB serial. The ESP32 controls the motors and independently stops for
obstacles, sensor faults, invalid commands, or command timeout.

```text
instruction -> structured goal -> webcam marker detection -> safe action
            -> Raspberry Pi USB serial -> ESP32 -> MX1508 -> robot movement
```

## 1. First-Prototype Decision

The first physical result uses a large coloured marker because it is reliable,
measurable, and does not require downloading or converting a large model.

- Prompt engineering uses a deterministic fixed-schema parser.
- Visual grounding uses OpenCV colour-marker detection.
- Supported first targets are `green marker`, `blue marker`, and
  `yellow marker`.
- The action set is `search`, `turn_left`, `turn_right`, `move_forward`, and
  `stop`.
- The ESP32 retains final authority over physical safety.

After this baseline works, OpenCV DNN, TensorFlow Lite, an API-based VLM, or a
custom landmark detector can replace the colour detector without changing the
ESP32 motor and safety layer.

## 2. Required Hardware

- Raspberry Pi 4 with microSD card
- Stable regulated Raspberry Pi supply, preferably 5.1 V / 3 A through USB-C
- ESP32 connected to the Raspberry Pi using a USB data + power cable
- USB UVC-compatible webcam connected to another Raspberry Pi USB port
- Two MX1508 motor drivers and four DC gear motors
- Two HC-SR04 sensors with level-shifted Echo signals
- GY-291 / ADXL345
- Completed protected power system, fuse, and main switch

Do not power motors from the Raspberry Pi. Keep the wheels raised until the
supervised movement test.

For the first prototype, allow the Raspberry Pi USB cable to power the ESP32
and do not connect a second ESP32 5 V source. If separate ESP32 power is later
required, use a verified data-only USB cable or USB power blocker.

## 3. Install Raspberry Pi OS

Use Raspberry Pi Imager on the development computer:

1. Select **Raspberry Pi 4**.
2. Select **Raspberry Pi OS Lite (64-bit)** for a headless robot.
3. Select the microSD card.
4. In OS customisation, configure:
   - hostname, for example `vlm-robot`
   - username and strong password
   - Wi-Fi and locale
   - SSH enabled
5. Write the image and boot the Raspberry Pi.

Connect from the development computer:

```bash
ssh <username>@vlm-robot.local
```

Official references:

- <https://www.raspberrypi.com/documentation/computers/getting-started.html>
- <https://www.raspberrypi.com/documentation/remote-access/>

## 4. Update the Raspberry Pi

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

Reconnect after reboot and confirm the 64-bit architecture:

```bash
uname -m
```

Expected result:

```text
aarch64
```

## 5. Install Required Software

```bash
sudo apt install -y \
  git \
  python3-venv \
  python3-opencv \
  python3-numpy \
  python3-serial \
  v4l-utils
```

Clone or copy this repository:

```bash
cd ~
git clone <your-repository-url> vlm-robot
cd ~/vlm-robot
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python3 -c "import cv2, numpy, serial; print('imports okay')"
```

The `--system-site-packages` option allows the virtual environment to use the
OpenCV and NumPy packages installed by Raspberry Pi OS.

## 6. Confirm the USB Webcam

Connect the webcam and list video devices:

```bash
v4l2-ctl --list-devices
ls -l /dev/video*
```

Test camera index `0`:

```bash
source ~/vlm-robot/.venv/bin/activate
python3 - <<'PY'
import cv2
camera = cv2.VideoCapture(0)
ok, frame = camera.read()
print("capture_ok=", ok, "shape=", None if frame is None else frame.shape)
camera.release()
PY
```

If capture fails, try camera index `1`.

## 7. Flash and Connect the ESP32

Flash:

```text
firmware/esp32_robot_controller/esp32_robot_controller.ino
```

Connect the ESP32 USB port to the Raspberry Pi using a USB data + power cable.
Find the serial device:

```bash
python3 -m serial.tools.list_ports -v
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Add the Raspberry Pi user to the serial-access group:

```bash
sudo usermod -aG dialout "$USER"
sudo reboot
```

The ESP32 usually appears as `/dev/ttyUSB0` or `/dev/ttyACM0`.

## 8. Test Raspberry Pi-to-ESP32 Communication

```bash
source ~/vlm-robot/.venv/bin/activate
python3 - <<'PY'
import serial, time
port = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
port.write(b'PING\n')
time.sleep(0.2)
for _ in range(5):
    print(port.readline().decode(errors='ignore').strip())
port.write(b'STOP\n')
port.close()
PY
```

Change `/dev/ttyUSB0` to the detected device if required.

Expected response includes:

```json
{"status":"ok","device":"esp32_robot_controller"}
```

Sensor JSON should also arrive repeatedly.

## 9. Run the First Dry Test

Place a large green marker in the test area. Dry-run mode processes the prompt,
camera, and sensor input but always sends `STOP`:

```bash
cd ~/vlm-robot
source .venv/bin/activate
python3 src/raspberry_pi_robot/robot_controller.py \
  --instruction "find the green marker" \
  --camera 0 \
  --serial-device /dev/ttyUSB0
```

Confirm the output and `logs/raspberry_pi_navigation.jsonl` contain:

- structured target `green marker`
- marker detection or safe `search`
- ESP32 sensor JSON
- selected action and reason
- end-to-end latency
- `sent_command: STOP` while dry-run mode is active

## 10. Run the First Physical Result

Keep wheels raised and the main switch within reach:

```bash
python3 src/raspberry_pi_robot/robot_controller.py \
  --instruction "find the green marker" \
  --camera 0 \
  --serial-device /dev/ttyUSB0 \
  --execute
```

Stop with `Ctrl+C`. The controller sends `STOP` during shutdown.

Expected behaviour:

| Camera and Sensor Condition | Expected Action |
|---|---|
| Unsupported or unclear instruction | `STOP` |
| Marker is not detected | `SEARCH` |
| Marker is on the left | `LEFT` |
| Marker is on the right | `RIGHT` |
| Marker is centred and not close | `FWD` |
| Marker reaches the configured goal size | `STOP` |
| Ultrasonic obstacle or sensor fault | ESP32 forces `STOP` |
| Raspberry Pi commands stop for more than 1 second | ESP32 forces `STOP` |

## 11. Optional Docker Engine on Raspberry Pi

Docker is optional for the physical Raspberry Pi prototype. Native execution is
recommended first because it makes USB webcam and ESP32 debugging easier.

Use Raspberry Pi OS 64-bit. Docker Engine officially supports the Debian arm64
architecture used by Raspberry Pi OS 64-bit:

<https://docs.docker.com/engine/install/debian/>

After the native physical loop is reliable, the controller may be
containerized with explicit device mappings such as:

```text
--device=/dev/video0
--device=/dev/ttyUSB0
```

## 12. Final Development Path

1. Demonstrate repeatable `find the green marker` behaviour.
2. Record prompt validity, grounding correctness, action correctness, latency,
   safe-stop rate, and movement success.
3. Calibrate motor direction, speed, ultrasonic threshold, and marker-size stop
   threshold.
4. Replace colour-marker grounding with a lightweight object detector.
5. Add targets such as chair, door, and signboard.
6. Add relation-aware prompts only after single-target movement is reliable.
7. Keep the ESP32 safety layer independent from all high-level decisions.
