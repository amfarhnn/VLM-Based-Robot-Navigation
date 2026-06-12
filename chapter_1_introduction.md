# CHAPTER 1

# INTRODUCTION

## 1.1 Overview

Mobile robots are increasingly used in indoor environments for inspection,
assistance, delivery, monitoring, and research. For a robot to be useful to a
non-technical user, the interaction method should be simple and natural.
Instead of requiring coordinates, joystick control, or programming commands, a
user should be able to provide an instruction such as "Find the chair" or "Go
to the door".

Natural-language mobile robot navigation is challenging because a human
instruction must be converted into information that a robot can understand and
execute. The robot must identify the intended target, connect the instruction
with its current camera view, choose an appropriate movement action, and stop
safely when the action is uncertain or an obstacle is detected.

This Final Year Project investigates how structured prompt engineering can
support this process on one low-cost indoor mobile robot prototype. The
finalized physical system uses a Coral Dev Board for onboard prompt processing,
USB-webcam perception, Edge TPU-compatible visual grounding, action selection,
and result logging. An ESP32 performs sensor reading, local safety checks, and
four-motor control through two MX1508 motor-driver modules.

The first prototype intentionally targets a basic and repeatable goal such as
`find the chair`. It adapts the modular language-to-vision-to-action concept
demonstrated by LM-Nav and the restricted prompt-based action-selection idea
used by VLMnav. It does not attempt to reproduce a large autonomous navigation
platform or run a general-purpose large vision-language model directly on the
Coral Edge TPU.

## 1.2 Background and Motivation

Traditional mobile robot navigation commonly uses maps, localization, path
planning, and sensor feedback. These methods are effective when the destination
is represented by coordinates or predefined waypoints. However, ordinary users
normally describe destinations using natural language and visual concepts,
such as a chair, door, table, corridor, or signboard.

Prompt engineering can constrain language interpretation into a structured
response containing a target, landmarks, spatial relation, action goal, and
uncertainty. Visual grounding can then connect the structured target to an
image captured by the robot. For a physical robot, the output must also be
restricted to approved actions and checked against local safety information.

The motivation for this project is therefore to investigate a practical
division of responsibility. The Coral Dev Board performs high-level language
and visual processing, while the ESP32 performs time-sensitive sensor reading,
motor commands, obstacle detection, and command-timeout safety. This
architecture supports prompt-based robot navigation without allowing uncertain
high-level output to bypass deterministic local safety rules.

## 1.3 Problem Statement

Natural-language instructions are intuitive for humans but are not directly
usable by a mobile robot. Instructions may be ambiguous, incomplete, or
dependent on objects visible in the environment. Free-form model responses are
also difficult to connect reliably to motor control because they may contain
unsupported actions or inconsistent wording.

Low-cost mobile robot platforms introduce further constraints. A USB webcam
does not provide depth or a complete map. The Coral Dev Board can efficiently
accelerate only compatible quantized TensorFlow Lite models, not unrestricted
large language or vision-language models. Two front ultrasonic sensors provide
limited obstacle coverage, and the low-cost motor and power subsystems require
careful integration.

There is therefore a need for a focused low-cost system that can convert a
simple natural-language indoor goal into structured machine-readable
information, ground a supported target using a webcam image, restrict the
result to an approved action set, and validate the action using ESP32 safety
information before movement.

## 1.4 Research Questions

This project addresses the following research questions:

1. How can structured prompt engineering convert simple indoor navigation
   instructions into consistent machine-readable targets, actions, and
   uncertainty?
2. How can Coral Edge TPU-compatible visual grounding and ESP32 sensor feedback
   be combined to select and execute safe basic robot actions?
3. How reliably can the completed Coral Dev Board prototype perform a simple
   goal such as finding and approaching a supported indoor landmark?

## 1.5 Aim and Objectives

The aim of this project is to design and implement a Coral Dev Board-based
prompt-engineered mobile robot for basic navigation in a controlled indoor
environment.

The objectives are:

1. To develop a structured prompt-engineering pipeline that converts a simple
   natural-language navigation instruction into fixed fields and an approved
   action set.
2. To integrate a Coral Dev Board, USB webcam, ESP32, two HC-SR04 sensors,
   GY-291 / ADXL345 accelerometer, two MX1508 motor drivers, four DC gear
   motors, and the completed protected power system into one physical robot.
3. To evaluate prompt validity, visual grounding, action correctness, latency,
   local safety behaviour, and simple physical navigation success.

## 1.6 Research Scope

The project is limited to one low-cost four-wheel indoor mobile robot using a
Coral Dev Board as the only onboard high-level compute platform. The robot
operates in supervised controlled areas such as rooms, laboratories, and
simple landmark test zones.

The first physical prototype focuses on a basic single-target goal supported by
an Edge TPU-compatible detector, initially `find the chair`. The approved
action set is limited to `move_forward`, `turn_left`, `turn_right`, `search`,
and `stop`. The Coral Dev Board performs structured instruction processing,
webcam capture, visual grounding, action selection, validation, and logging.
The ESP32 reads the ultrasonic sensors and GY-291, controls four motors through
two MX1508 modules, and enforces obstacle, invalid-command, and command-timeout
stop behaviour.

The GY-291 is used for X/Y/Z acceleration, gravity-based roll and pitch tilt,
motion, vibration, and shock observations. It is not treated as a heading
sensor. Advanced functions such as full simultaneous localization and mapping,
precise coordinate navigation, wheel-encoder odometry, autonomous route
planning, LiDAR, RGB-D perception, and unrestricted large-model control are
outside the current scope.

A separate Docker-based laptop webcam demonstration may be used during FYP1 to
illustrate expected action outputs before final physical testing. A browser
captures the webcam while a local container performs Python/OpenCV processing.
It displays movement instructions for manual laptop movement and is not a
second physical project approach.

## 1.7 Significance of the Project

The project contributes a practical framework for connecting prompt engineering
with a real low-cost robot. Structured output makes navigation decisions easier
to parse, log, evaluate, and reject when unsafe. Separating Coral high-level
processing from ESP32 local control also demonstrates how model-based
navigation can be combined with deterministic safety behaviour.

The first-prototype focus makes the research achievable and measurable. A
reliable single-target demonstration provides a baseline that can later be
extended with a custom detector for doors and signboards, relation-aware
instructions, additional sensors, mapping, and stronger navigation models.

## 1.8 Organization of the Thesis

Chapter 1 introduces the project background, problem statement, research
questions, objectives, scope, and significance. Chapter 2 reviews related work
on language-guided navigation, prompt engineering, visual grounding, and
suitable low-cost hardware. Chapter 3 presents the Coral-only methodology,
system architecture, mechanical and electrical design, implementation
procedure, and validation plan. Chapter 4 presents the expected FYP1 results
and defines the physical measurements required during FYP2.

## 1.9 Summary

This chapter established the need for a focused and safety-aware approach to
natural-language mobile robot navigation. The finalized project develops one
Coral Dev Board physical prototype with one ESP32 sensor, safety, and
motor-control layer.
