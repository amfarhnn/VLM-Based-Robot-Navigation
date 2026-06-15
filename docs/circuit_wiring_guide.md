# Raspberry Pi 4, ESP32, and MX1508 Wiring Guide

This guide covers the remaining signal wiring for the finalized Raspberry Pi 4
physical prototype. The power system is assumed to be already assembled and
verified. Do not connect power until every signal connection has been checked.

## 1. Final Signal Architecture

```text
USB webcam --------------------------> Raspberry Pi 4 USB port
ESP32 USB data + power cable <------> Raspberry Pi 4 USB port
                                            |
                                            v
                                           ESP32
                                            |
                     +----------------------+----------------------+
                     |                      |                      |
              two HC-SR04             GY-291 / ADXL345       two MX1508
                                                                  |
                                                          four DC motors
```

USB serial is the finalized Raspberry Pi-to-ESP32 interface. It provides
communication and makes the ESP32 easy to flash and debug without consuming
Raspberry Pi or ESP32 UART GPIO pins.

## 2. Safety Before Wiring

- Switch off and disconnect the battery.
- Verify the motor and logic/compute rail voltages with a multimeter.
- Power the Raspberry Pi through a stable regulated USB-C supply.
- For the first prototype, power the ESP32 only from the Raspberry Pi USB data + power
  cable. Do not simultaneously connect a separate ESP32 5 V supply.
- Never connect motor power to Raspberry Pi or ESP32 logic pins.
- HC-SR04 Echo is normally 5 V and must be level-shifted before ESP32 GPIO.
- Keep a common ground between ESP32, both MX1508 drivers, sensors, and the
  power-system ground.
- Begin motor testing with all wheels raised.

## 3. Raspberry Pi 4 to ESP32

Connect an ESP32 USB data + power cable to any Raspberry Pi USB port.

| Raspberry Pi Connection | ESP32 Connection | Purpose |
|---|---|---|
| USB port | ESP32 USB port | Commands, sensor JSON, flashing, and debugging |

The ESP32 normally appears as `/dev/ttyUSB0` or `/dev/ttyACM0`.

Do not also connect direct UART wires during the first prototype. USB serial is
the only Raspberry Pi-to-ESP32 control connection required.

The normal USB cable also powers the ESP32. If the final robot must power the
ESP32 from a separate regulated supply, use a verified data-only USB cable or a
USB power blocker so the Raspberry Pi and external 5 V outputs are not joined.

## 4. ESP32 Final Pin Assignment

| Function | ESP32 Pin |
|---|---:|
| Front-left HC-SR04 Trigger | GPIO 5 |
| Front-left HC-SR04 Echo through level shifting | GPIO 34 |
| Front-right HC-SR04 Trigger | GPIO 18 |
| Front-right HC-SR04 Echo through level shifting | GPIO 35 |
| GY-291 SDA | GPIO 21 |
| GY-291 SCL | GPIO 22 |
| Front-left motor inputs | GPIO 25 and GPIO 26 |
| Front-right motor inputs | GPIO 27 and GPIO 14 |
| Rear-left motor inputs | GPIO 32 and GPIO 33 |
| Rear-right motor inputs | GPIO 16 and GPIO 17 |

GPIO 16 and GPIO 17 return to the rear-right motor channel because Raspberry
Pi communication uses USB serial.

## 5. ESP32 to Two MX1508 Drivers

| Driver | Channel | Motor | ESP32 Inputs |
|---|---|---|---|
| MX1508 Driver 1 | Channel A | Front-left | GPIO 25 and GPIO 26 |
| MX1508 Driver 1 | Channel B | Rear-left | GPIO 32 and GPIO 33 |
| MX1508 Driver 2 | Channel A | Front-right | GPIO 27 and GPIO 14 |
| MX1508 Driver 2 | Channel B | Rear-right | GPIO 16 and GPIO 17 |

For each MX1508:

| MX1508 Connection | Connect To |
|---|---|
| Motor-supply positive | Verified motor buck-converter positive output |
| Motor-supply ground | Motor buck-converter ground and common ground |
| Channel input pins | Assigned ESP32 GPIO pins |
| Channel output terminals | Corresponding DC motor |

Do not power motors from the ESP32 or Raspberry Pi. Confirm motor stall current
remains within the MX1508 module rating.

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

Example Echo resistor divider:

```text
HC-SR04 Echo ---- 1 kOhm ----+---- ESP32 Echo GPIO
                             |
                           2 kOhm
                             |
                            GND
```

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
3. Connect GY-291 I2C signals.
4. Connect HC-SR04 Trigger and level-shifted Echo signals.
5. Connect ESP32 control signals to both MX1508 drivers.
6. Connect each motor to its assigned MX1508 output channel.
7. Recheck continuity and verify there is no short between supply and ground.
8. Power only the logic rail.
9. Confirm no separate ESP32 5 V supply is connected, then connect the ESP32
   and webcam to Raspberry Pi USB ports.
10. Test Raspberry Pi-to-ESP32 USB serial.
11. Power the motor rail with wheels raised and test one action at a time.

## 9. Raspberry Pi-to-ESP32 Communication Test

```bash
python3 -m serial.tools.list_ports -v
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

Change `/dev/ttyUSB0` if the ESP32 appears as another device.

## 10. Motor Direction Test

Keep wheels raised:

```bash
python3 - <<'PY'
import serial, time
port = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
for command in ('FWD', 'STOP', 'LEFT', 'STOP', 'RIGHT', 'STOP'):
    print('sending', command)
    port.write((command + '\n').encode())
    time.sleep(0.5)
port.write(b'STOP\n')
port.close()
PY
```

If one wheel rotates in the wrong direction, switch off power and reverse only
that motor's two output wires.

## 11. Final Checklist

- [ ] Raspberry Pi uses a stable regulated USB-C supply.
- [ ] ESP32 uses only Raspberry Pi USB power, or the USB 5 V wire is safely
      isolated before separate ESP32 power is used.
- [ ] Webcam and ESP32 are connected to separate Raspberry Pi USB ports.
- [ ] ESP32 USB serial appears as `/dev/ttyUSB0` or `/dev/ttyACM0`.
- [ ] HC-SR04 Echo signals are level-shifted.
- [ ] Rear-right motor control uses ESP32 GPIO 16 and GPIO 17.
- [ ] All MX1508 grounds share the control-system ground.
- [ ] Motor power does not enter Raspberry Pi or ESP32 logic pins.
- [ ] Wheels are raised during the first movement test.
- [ ] `STOP` works before any floor test.
