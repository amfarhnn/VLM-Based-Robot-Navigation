# Coral Dev Board Full Software Setup

This is the only finalized physical implementation for the project. The first
prototype accepts a simple instruction such as `find the chair`, detects the
target using an Edge TPU-compatible object detector, selects a restricted
action, and sends the action to the ESP32. The ESP32 controls the motors and
independently stops for obstacles, invalid commands, or command timeout.

The first prototype should prove this complete loop before adding harder goals:

```text
instruction -> structured goal -> webcam detection -> safe action
            -> Coral UART3 -> ESP32 -> MX1508 drivers -> robot movement
```

## 1. Important First-Prototype Decision

The Coral Edge TPU does not run a general-purpose large language model or
vision-language model. It accelerates compatible, fully quantized TensorFlow
Lite models. Therefore:

- Prompt engineering is first implemented as a deterministic structured parser.
- Visual grounding is first implemented with an Edge TPU object detector.
- Start with detector-supported objects such as `chair`, `bottle`, or `person`.
- Use `search`, `turn_left`, `turn_right`, `move_forward`, and `stop`.
- Train a custom Edge TPU detector later for project-specific landmarks such as
  doors or signboards.

This is a valid baseline because the prompt schema, action restrictions,
uncertainty handling, latency, and physical result can all be measured.

## 2. Required Hardware Before Software Setup

- Standard Coral Dev Board, not Dev Board Mini or Dev Board Micro
- Stable regulated 5 V, 2-3 A supply capable of powering the Coral Dev Board
- ESP32 flashed through USB from a development computer
- USB UVC-compatible webcam
- Coral UART3 to ESP32 UART2 wiring described in
  [the wiring guide](circuit_wiring_guide.md)
- Two MX1508 motor drivers and four motors
- Main switch, fuse, and the already-built protected power system

Keep the robot wheels raised until Section 10.

## 3. Install Mendel Linux on the Coral Dev Board

The official Coral setup uses a microSD flash card to install Mendel Linux into
the Dev Board's internal eMMC storage.

On a Windows 10 or Windows 11 host, install Git for Windows and use Git Bash for
the Coral command-line steps. The official guide may require these aliases:

```bash
echo "alias python3='winpty python3.exe'" >> ~/.bash_profile
echo "alias mdt='winpty mdt'" >> ~/.bash_profile
source ~/.bash_profile
```

1. On a host computer, download the official Coral Dev Board flash-card image.
2. Write `flashcard_arm64.img` to an 8 GB or larger microSD card using
   balenaEtcher.
3. Disconnect all power from the Coral.
4. Set the boot switches to SD-card mode:

```text
Switch 1 ON, Switch 2 OFF, Switch 3 ON, Switch 4 ON
```

5. Insert the microSD card and power the Coral through the `PWR` USB-C port.
6. Wait until flashing completes and the red LED turns off.
7. Disconnect power, remove the microSD card, and set eMMC boot mode:

```text
Switch 1 ON, Switch 2 OFF, Switch 3 OFF, Switch 4 OFF
```

8. Reconnect power and allow approximately three minutes for the first boot.

Official reference:
<https://coral.ai/docs/dev-board/get-started/>

## 4. Connect to the Coral and Update It

Install the Mendel Development Tool on the host computer:

```bash
python3 -m pip install --user mendel-development-tool
```

Connect the Coral `OTG` USB-C port to the host computer, then run:

```bash
mdt devices
mdt shell
```

Inside the Coral shell, connect Ethernet or configure Wi-Fi:

```bash
nmtui
```

Update the installed Mendel packages:

```bash
sudo apt-get update
sudo apt-get dist-upgrade
sudo reboot
```

Reconnect using `mdt shell` after reboot.

## 5. Confirm the Edge TPU

Run the included Edge TPU demo:

```bash
edgetpu_demo --stream
```

From the connected host computer, open:

```text
http://192.168.100.2:4664/
```

Then verify PyCoral:

```bash
mkdir -p ~/coral && cd ~/coral
git clone https://github.com/google-coral/pycoral.git
cd pycoral
bash examples/install_requirements.sh classify_image.py
python3 examples/classify_image.py \
  --model test_data/mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite \
  --labels test_data/inat_bird_labels.txt \
  --input test_data/parrot.jpg
```

Do not use `pip install pycoral` on Mendel. Use the Coral-provided Debian
packages and official examples because the native libraries must match.

## 6. Confirm the USB Webcam

Connect the webcam to the Coral USB-A host port:

```bash
sudo apt-get install v4l-utils
v4l2-ctl --list-devices
v4l2-ctl --list-formats-ext --device /dev/video1
```

The device might be `/dev/video0` or `/dev/video1`. Test frame capture:

```bash
python3 - <<'PY'
import cv2
camera = cv2.VideoCapture(0)
ok, frame = camera.read()
print("capture_ok=", ok, "shape=", None if frame is None else frame.shape)
camera.release()
PY
```

If the camera cannot open, repeat the test with camera index `1`.

## 7. Test an Edge TPU Object Detector

Download the official Coral camera examples and compiled models:

```bash
cd ~/coral
git clone https://github.com/google-coral/examples-camera.git --depth 1
cd examples-camera
sh download_models.sh
```

Test a saved or live image using the official example. For the first robot
goal, use:

```text
all_models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite
all_models/coco_labels.txt
```

The COCO detector includes `chair`, which is a suitable first physical goal.
It does not reliably provide project-specific classes such as `door` or
`signboard`; those require a custom-trained and Edge TPU-compiled detector.

## 8. Install and Copy the Robot Application

On the Coral:

```bash
sudo apt-get install python3-opencv python3-serial git
mkdir -p ~/vlm-robot/src/coral_robot ~/vlm-robot/logs
```

From the host computer, copy the application:

```bash
mdt push src/coral_robot/robot_controller.py \
  /home/mendel/vlm-robot/src/coral_robot/robot_controller.py
```

Alternatively, clone or copy this complete repository onto the Coral.

Confirm the Coral UART3 device exists:

```bash
ls -l /dev/ttymxc2
pinout
python3 -c "import cv2, serial, pycoral; print('imports okay')"
```

If `/dev/ttymxc2` reports permission denied:

```bash
sudo usermod -aG dialout mendel
sudo reboot
```

## 9. Flash and Test the ESP32

Flash:

```text
firmware/esp32_robot_controller/esp32_robot_controller.ino
```

The finalized firmware uses:

```text
ESP32 UART2 RX = GPIO 16, connected from Coral UART3 TX
ESP32 UART2 TX = GPIO 17, connected to Coral UART3 RX
Baud rate      = 115200
```

After wiring, test communication from the Coral:

```bash
python3 - <<'PY'
import serial, time
port = serial.Serial('/dev/ttymxc2', 115200, timeout=1)
port.write(b'PING\n')
time.sleep(0.2)
print(port.readline().decode(errors='ignore').strip())
port.write(b'STOP\n')
port.close()
PY
```

Expected response:

```json
{"status":"ok","device":"esp32_robot_controller"}
```

Sensor JSON should then arrive repeatedly. If not, swap the TX/RX signal wires,
confirm common ground, and confirm both sides use 115200 baud.

## 10. Run the First End-to-End Result

First use dry-run mode. Dry-run processes the instruction and camera but always
sends `STOP`:

```bash
cd ~/vlm-robot
python3 src/coral_robot/robot_controller.py \
  --instruction "find the chair" \
  --model ~/coral/examples-camera/all_models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite \
  --labels ~/coral/examples-camera/all_models/coco_labels.txt \
  --camera 0
```

Confirm the log contains:

- the structured goal with `target: chair`
- a detected chair or a safe `search` result
- ESP32 sensor JSON
- selected action and reason
- end-to-end latency
- `sent_command: STOP` while dry-run is active

With wheels raised and an emergency power switch within reach, enable movement:

```bash
python3 src/coral_robot/robot_controller.py \
  --instruction "find the chair" \
  --model ~/coral/examples-camera/all_models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite \
  --labels ~/coral/examples-camera/all_models/coco_labels.txt \
  --camera 0 \
  --execute
```

Stop the program with `Ctrl+C`. The controller sends `STOP` during shutdown.

## 11. Expected First-Prototype Behaviour

| Camera and Sensor Condition | Expected Action |
|---|---|
| Instruction target unsupported or unclear | `STOP` |
| Chair is not detected | `SEARCH` |
| Chair is on left side of image | `LEFT` |
| Chair is on right side of image | `RIGHT` |
| Chair is centred and not close | `FWD` |
| Chair fills the configured goal-size image area | `STOP` |
| Either ultrasonic sensor reports an obstacle | ESP32 forces `STOP` |
| Both ultrasonic readings become unavailable | ESP32 forces `STOP` |
| Coral command updates stop for more than 1 second | ESP32 forces `STOP` |

## 12. Final FYP Development Path

1. Demonstrate repeatable `find the chair` behaviour.
2. Record prompt validity, detection correctness, action correctness, latency,
   safe-stop rate, and movement success.
3. Calibrate motor direction, speed, ultrasonic threshold, and target-size stop
   threshold.
4. Collect images of the actual indoor landmarks.
5. Train and compile a custom detector for `door`, `signboard`, and other
   required project targets.
6. Add relation-aware prompts only after single-target navigation is reliable.
7. Keep the ESP32 safety layer independent from all model decisions.

## 13. Official References

- Coral Dev Board setup: <https://coral.ai/docs/dev-board/get-started/>
- Coral Dev Board I/O pins: <https://coral.ai/docs/dev-board/gpio/>
- Coral USB camera setup: <https://coral.ai/docs/dev-board/camera/>
- Edge TPU model requirements: <https://coral.ai/docs/edgetpu/models-intro/>
- Official camera examples: <https://github.com/google-coral/examples-camera>
- PyCoral examples: <https://github.com/google-coral/pycoral>

The original Coral Dev Board and PyCoral software stack is mature but old, and
some official repositories are archived. Preserve a working Mendel image,
package versions, model files, and setup notes once the prototype works.
