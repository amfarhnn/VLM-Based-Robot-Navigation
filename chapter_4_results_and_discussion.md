# CHAPTER 4

# EXPECTED RESULTS AND DISCUSSION

## 4.1 Introduction

This chapter presents the expected results for FYP1. The expectations are based
on the finalized Raspberry Pi 4 architecture, structured prompt design,
completed physical hardware, ESP32 safety logic, Docker laptop expected-results
demonstration, and planned physical validation. Final measured robot results
will be presented during FYP2.

## 4.2 Expected Basic Prototype Result

The first Raspberry Pi 4 prototype is expected to complete the simple and
repeatable goal `find the green marker`. The instruction should be converted
into a structured target and approved action set. OpenCV colour grounding
should locate the marker in the webcam view and select an action from its image
position.

**Table 4.1: Summary of Expected Basic Prototype Results**

| Condition | Expected Result |
|---|---|
| Clear supported marker instruction | Produces a valid structured target and low uncertainty |
| Unsupported or unclear instruction | Stops safely |
| Marker not visible | Selects `search` |
| Marker visible on left or right | Selects the corresponding turn action |
| Marker centred and not close | Selects `move_forward` |
| Marker reaches configured goal size | Selects `stop` |
| Ultrasonic obstacle, sensor fault, or command timeout | ESP32 forces `stop` |

## 4.3 Expected Docker Laptop Demonstration

The laptop-only Docker demonstration is expected to show the same planned
action interface before physical robot testing. A browser captures a coloured
marker through the laptop webcam and sends frames to the containerized
Python/OpenCV service. The application displays `TURN LEFT`, `TURN RIGHT`,
`MOVE FORWARD`, `SEARCH`, or `STOP`, and the user manually moves the laptop
according to the displayed action.

This demonstration provides expected-results evidence only. It is not a second
physical implementation and is not used as the final robot result.

## 4.4 Expected Safety Simulations

The ESP32 uses the minimum reading from the two front HC-SR04 sensors. With the
planned 25 cm threshold, the robot is expected to stop when either valid sensor
reading is below 25 cm.

**Figure 4.1: Expected obstacle-stop response at the planned 25 cm threshold**

```text
Minimum distance below 25 cm -> STOP
Minimum distance at or above 25 cm -> movement may be permitted
```

The ESP32 also applies a 1,000 ms command timeout. If no new valid command is
received within this period, all motor outputs are expected to stop.

**Figure 4.2: Expected motor response when the command timeout exceeds 1,000 ms**

```text
Up to 1000 ms after command -> commanded motion remains available
Above 1000 ms without command -> STOP
```

These simulations demonstrate the intended decision logic only. The final
distance threshold and physical stopping response require calibration and
repeated testing during FYP2.

## 4.5 Required FYP2 Results

**Table 4.2: Required FYP2 Measurements**

| Evaluation Area | Required Measurement |
|---|---|
| Prompt engineering | Structured output validity and supported-target extraction accuracy |
| Visual grounding | Marker-grounding correctness and safe missing-target behaviour |
| Raspberry Pi performance | OpenCV processing and end-to-end action latency |
| USB communication | Command and sensor-status reliability |
| Sensors and safety | Ultrasonic error, GY-291 response, timeout, and safe-stop success |
| Robot movement | Action correctness and simple-goal completion rate |
| Power system | Voltage stability, resets, current, and operating duration |

## 4.6 Discussion

The expected results suggest that structured prompt engineering can provide a
simple interface between a natural-language goal and a restricted robot action
set. The Raspberry Pi 4 is expected to provide a flexible environment for
Python, OpenCV, USB devices, logging, and later model experiments, while the
ESP32 independently prevents movement during obstacle, sensor-fault, timeout,
and invalid-command conditions.

The basic marker goal is intentionally limited. Demonstrating it reliably is
more valuable than claiming complex navigation without sufficient sensor
coverage, mapping, or model capability. Once the baseline is verified, the
project can extend to object detection for indoor landmarks and more complex
instructions.

## 4.7 Summary

This chapter presented the expected FYP1 outcomes for the Raspberry Pi 4
prototype, Docker laptop expected-results demonstration, and safety logic.
Final physical results will measure whether the robot can safely find and
approach a supported visual landmark.
