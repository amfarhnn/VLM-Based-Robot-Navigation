# Suggested Circuit Wiring Guide

This guide describes the updated physical robot wiring architecture. It applies to the two physical approaches:

- Raspberry Pi + ESP32 + webcam + remote GPU laptop/PC
- Google Dev Board + ESP32 + webcam

The laptop-only feasibility approach does not require robot wiring because it uses the built-in laptop camera and displays actions for a human operator to follow.

Final pin numbers must be checked against the exact ESP32 board, motor driver, battery holder, ultrasonic sensor modules, Raspberry Pi or Google Dev Board, and DC motors used in the physical prototype.

## High-Level Connection

```text
User prompt
  -> high-level compute board or laptop model runtime
  -> webcam image capture
  -> ESP32 ultrasonic status check
  -> ESP32 motor-driver command
  -> motor driver outputs
  -> four DC motors
```

For the Raspberry Pi approach, heavy model inference may run on a GPU laptop or desktop over WiFi. For the Google Dev Board approach, the model or lightweight visual inference module runs onboard if supported.

## Suggested Circuit Diagram in Text Form

```text
[Battery Pack]
        |
        v
[Main Power Switch / Fuse]
        |
        +--> [Motor Power Rail] --> [Motor Driver]
        |                              |--> Front Left DC Motor
        |                              |--> Front Right DC Motor
        |                              |--> Rear Left DC Motor
        |                              |--> Rear Right DC Motor
        |
        +--> [Regulated Logic Supply] --> [Raspberry Pi or Google Dev Board]
        |                                  |--> USB Webcam
        |                                  |--> USB/UART to ESP32
        |
        +--> [Regulated 5 V or 3.3 V Supply] --> [ESP32]
                                               |--> Ultrasonic Sensor Front
                                               |--> Ultrasonic Sensor Left
                                               |--> Ultrasonic Sensor Right
                                               |--> Ultrasonic Sensor Rear
                                               |--> Motor Driver Input Pins

All controller grounds must be connected to a common ground reference.
```

## ESP32 to Ultrasonic Sensors

Each ultrasonic sensor has four typical pins:

- VCC: connect to the sensor supply voltage specified by the sensor module.
- GND: connect to common ground.
- TRIG: connect to an ESP32 output GPIO.
- ECHO: connect to an ESP32 input GPIO through level shifting if the echo voltage is higher than 3.3 V.

Suggested logical placement:

- Front sensor: detects obstacle in front of the robot.
- Left sensor: checks left-side clearance.
- Right sensor: checks right-side clearance.
- Rear sensor: optional reverse safety or rear proximity checking.

## ESP32 to Motor Driver

The ESP32 sends low-level control signals to the motor driver. Exact pins depend on the selected driver.

Typical motor-driver connections:

- ESP32 PWM pins to motor speed inputs.
- ESP32 direction pins to motor direction inputs.
- Motor driver motor outputs to the four DC motors.
- Motor power rail to the motor driver motor supply input.
- Logic supply to the motor driver logic input if required.
- Common ground between ESP32, motor driver, compute board, and battery supply.

Suggested high-level command mapping:

| Command | Motor Behavior |
|---|---|
| `FWD` | Move forward slowly |
| `LEFT` | Turn left |
| `RIGHT` | Turn right |
| `SEARCH` | Rotate slowly to scan |
| `STOP` | Stop all motors |

## Compute Board to ESP32

The high-level compute board can be either a Raspberry Pi or Google Dev Board.

- Compute board to ESP32: USB serial or UART serial for distance/status messages and motor commands.
- USB webcam to compute board: direct USB connection.
- Raspberry Pi to GPU server, if using Approach 1: WiFi network connection.

Suggested ESP32 JSON status output:

```json
{
  "front_cm": 50.2,
  "left_cm": 40.0,
  "right_cm": 60.3,
  "rear_cm": 90.0,
  "min_cm": 40.0,
  "obstacle": false
}
```

## Power Notes

- Do not power the compute board directly from an unregulated battery pack.
- Use a regulator or power module that matches the selected compute board input requirement.
- Use a separate motor power rail if motor current causes voltage drops.
- Use a main switch and preferably a fuse on the battery supply.
- Use common ground between the compute board, ESP32, motor driver, sensors, and battery system.
- If ultrasonic sensors output 5 V echo signals, do not connect Echo directly to ESP32 GPIO without level shifting.
- Test motors at low speed first and keep a manual stop available.

## Safety Notes

- The ESP32 should stop the motors if the front distance is below the safety threshold.
- The ESP32 should stop the motors if no valid command is received within a timeout.
- The high-level compute layer should send `STOP` when model output is invalid, uncertain, too slow, or unsafe.
- Keep the robot raised on a stand during the first motor-direction test.
- Confirm motor direction one wheel at a time before allowing the robot to move on the floor.
