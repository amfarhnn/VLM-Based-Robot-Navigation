# Coral Dev Board, ESP32, and MX1508 Wiring Guide

This guide covers the remaining signal wiring for the finalized Coral Dev Board
physical prototype. The power system is assumed to be already assembled and
verified. Do not connect power until every signal connection has been checked.

This guide assumes the **standard Coral Dev Board** shown in the project
component image, not the Dev Board Mini or Dev Board Micro.

## 1. Final Signal Architecture

```text
USB webcam
    |
    v
Coral Dev Board
  UART3 TX pin 7  ----------> ESP32 GPIO 16 / UART2 RX
  UART3 RX pin 11 <---------- ESP32 GPIO 17 / UART2 TX
  GND pin 9       ----------- ESP32 GND
                                  |
                                  +--> two HC-SR04 sensors
                                  +--> GY-291 / ADXL345
                                  +--> two MX1508 drivers
                                            |
                                            +--> four DC gear motors
```

UART is the finalized Coral-to-ESP32 interface because it leaves the Coral
USB-A host port available for the USB webcam.

## 2. Safety Before Wiring

- Switch off and disconnect the battery.
- Verify the motor rail and logic/compute rail voltages with a multimeter.
- Never connect motor power to the Coral or ESP32 logic pins.
- Coral and ESP32 signal pins use 3.3 V logic.
- HC-SR04 Echo is normally 5 V and must be level-shifted before ESP32 GPIO.
- Keep a common ground between Coral, ESP32, both MX1508 drivers, sensors, and
  the power-system ground.
- Begin motor testing with all wheels raised.

## 3. Coral Dev Board to ESP32 UART

Use Coral **UART3**, not UART1. UART1 is shared with the Linux serial console.

| Coral 40-Pin Header | Coral Function | Connect To | Direction |
|---:|---|---|---|
| Pin 7 | UART3 TXD, `/dev/ttymxc2` | ESP32 GPIO 16, UART2 RX | Coral to ESP32 |
| Pin 11 | UART3 RXD, `/dev/ttymxc2` | ESP32 GPIO 17, UART2 TX | ESP32 to Coral |
| Pin 9 | Ground | ESP32 GND | Common reference |

Important:

- TX connects to RX.
- RX connects to TX.
- Do not connect Coral 5 V or 3.3 V header power to the ESP32 when the ESP32 is
  already powered by the robot's regulated supply.
- Do not use an RS-232 adapter; this is direct 3.3 V TTL UART.
- Both devices use `115200 8N1`.

Coral UART test:

```bash
ls -l /dev/ttymxc2
pinout
```

## 4. ESP32 Final Pin Assignment

The firmware file
`firmware/esp32_robot_controller/esp32_robot_controller.ino` uses this mapping:

| Function | ESP32 Pin |
|---|---:|
| ESP32 UART2 receive from Coral | GPIO 16 |
| ESP32 UART2 transmit to Coral | GPIO 17 |
| Front-left HC-SR04 Trigger | GPIO 5 |
| Front-left HC-SR04 Echo through level shifting | GPIO 34 |
| Front-right HC-SR04 Trigger | GPIO 18 |
| Front-right HC-SR04 Echo through level shifting | GPIO 35 |
| GY-291 SDA | GPIO 21 |
| GY-291 SCL | GPIO 22 |
| Front-left motor inputs | GPIO 25 and GPIO 26 |
| Front-right motor inputs | GPIO 27 and GPIO 14 |
| Rear-left motor inputs | GPIO 32 and GPIO 33 |
| Rear-right motor inputs | GPIO 19 and GPIO 23 |

GPIO 16 and GPIO 17 were reserved for Coral communication. Therefore, the
rear-right motor channel uses GPIO 19 and GPIO 23.

## 5. ESP32 to Two MX1508 Drivers

Each MX1508 module controls two motors. Module labels differ by supplier; verify
which terminals are motor outputs and which terminals are logic inputs before
powering the system.

| Driver | Channel | Motor | ESP32 Inputs |
|---|---|---|---|
| MX1508 Driver 1 | Channel A | Front-left | GPIO 25 and GPIO 26 |
| MX1508 Driver 1 | Channel B | Rear-left | GPIO 32 and GPIO 33 |
| MX1508 Driver 2 | Channel A | Front-right | GPIO 27 and GPIO 14 |
| MX1508 Driver 2 | Channel B | Rear-right | GPIO 19 and GPIO 23 |

For each MX1508:

| MX1508 Connection | Connect To |
|---|---|
| Motor-supply positive | Verified motor buck-converter positive output |
| Motor-supply ground | Motor buck-converter ground and common ground |
| Channel input pins | Assigned ESP32 GPIO pins |
| Channel output terminals | Corresponding DC motor |

Do not power a motor from the ESP32. Confirm motor stall current remains within
the MX1508 module rating.

## 6. ESP32 to HC-SR04 Sensors

| Sensor | Pin | Connection |
|---|---|---|
| Front-left HC-SR04 | VCC | Verified 5 V sensor supply |
| Front-left HC-SR04 | GND | Common ground |
| Front-left HC-SR04 | Trigger | ESP32 GPIO 5 |
| Front-left HC-SR04 | Echo | Level shifter or resistor divider, then GPIO 34 |
| Front-right HC-SR04 | VCC | Verified 5 V sensor supply |
| Front-right HC-SR04 | GND | Common ground |
| Front-right HC-SR04 | Trigger | ESP32 GPIO 18 |
| Front-right HC-SR04 | Echo | Level shifter or resistor divider, then GPIO 35 |

A common resistor-divider example for each Echo signal is:

```text
HC-SR04 Echo ---- 1 kOhm ----+---- ESP32 Echo GPIO
                             |
                           2 kOhm
                             |
                            GND
```

This reduces a 5 V Echo signal to approximately 3.3 V.

## 7. ESP32 to GY-291 / ADXL345

| GY-291 Pin | Connection |
|---|---|
| VCC | Supply voltage supported by the exact module |
| GND | Common ground |
| SDA | ESP32 GPIO 21 |
| SCL | ESP32 GPIO 22 |

The GY-291 supports acceleration, roll/pitch estimation, motion, vibration, and
shock observations. It does not provide yaw or compass heading.

## 8. Recommended Wiring Order

1. Disconnect battery power.
2. Connect all common-ground wires.
3. Connect Coral UART3 TX/RX to ESP32 UART2 RX/TX.
4. Connect GY-291 I2C signals.
5. Connect HC-SR04 Trigger and level-shifted Echo signals.
6. Connect ESP32 control signals to both MX1508 drivers.
7. Connect each motor to its assigned MX1508 output channel.
8. Recheck continuity and verify there is no short between supply and ground.
9. Power only the logic rail and test Coral-to-ESP32 communication.
10. Power the motor rail with wheels raised and test one motor channel at a
    time.

## 9. Coral-to-ESP32 Communication Test

After flashing the ESP32 firmware, run this on the Coral:

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

The ESP32 also forces `STOP` if both ultrasonic readings are unavailable.

## 10. Motor Direction Test

Keep wheels raised and send one command at a time:

```bash
python3 - <<'PY'
import serial, time
port = serial.Serial('/dev/ttymxc2', 115200, timeout=1)
for command in ('FWD', 'STOP', 'LEFT', 'STOP', 'RIGHT', 'STOP'):
    print('sending', command)
    port.write((command + '\n').encode())
    time.sleep(0.5)
port.write(b'STOP\n')
port.close()
PY
```

If one wheel rotates in the wrong direction, switch off power and reverse only
that motor's two output wires. Do not change several motors at once.

## 11. Final Checklist

- [ ] Coral pin 7 connects to ESP32 GPIO 16.
- [ ] Coral pin 11 connects to ESP32 GPIO 17.
- [ ] Coral pin 9 connects to ESP32 ground.
- [ ] Both UART ends use 115200 baud.
- [ ] HC-SR04 Echo signals are level-shifted.
- [ ] Rear-right motor control uses ESP32 GPIO 19 and GPIO 23.
- [ ] All MX1508 grounds share the control-system ground.
- [ ] Motor power does not enter Coral or ESP32 logic pins.
- [ ] Wheels are raised during the first movement test.
- [ ] `STOP` works before any floor test.

Official Coral pinout reference: <https://coral.ai/docs/dev-board/gpio/>
