![Header](Header.jpg)

# Prompt Engineering for Mobile Robot Navigation

`Prompt Engineering for Mobile Robot Navigation` is a research project focused on language-guided mobile robot navigation using large pre-trained models.

![3D model photo of the mobile robot navigation prototype](main.png)

*3D model photo of the proposed mobile robot navigation prototype.*

This project is centered on one primary paper:
- `LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action`

## Project Focus

The goal of this project is to study how a robot can follow natural language navigation instructions without relying on a language-annotated robot navigation dataset.

`LM-Nav` is a strong reference because it combines separate pre-trained models for:
- language understanding
- image-language grounding
- visual navigation
- long-horizon mobile robot navigation

## Selected Paper

| Paper | Authors | Venue | Publication | Code |
|---|---|---|---|---|
| LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action | Dhruv Shah, Blazej Osinski, Brian Ichter, Sergey Levine | CoRL / PMLR 2023 | [Paper](https://proceedings.mlr.press/v205/shah23b) | [Code](https://github.com/blazejosinski/lm_nav) |

## Project Documents

| Document | Description |
|---|---|
| [Chapter 2 Literature Review](https://docs.google.com/document/d/1kwpJmBAQByh0q103gmgsgumgGNn6tCbL2_T7v8mcL6s/edit?usp=sharing) | Formal literature review chapter covering `LM-Nav` and related papers. |
| [Chapter 3 Methodology](chapter_3_methodology.md) | Formal methodology chapter following the university FYP chapter format. |

## Proposed Implementation Approaches

Because the earlier single-board plan is no longer available, the project now documents three practical implementation approaches.

| Approach | Guide | Purpose |
|---|---|---|
| Raspberry Pi, ESP32, webcam, and remote GPU laptop/PC | [Approach 1 Guide](docs/approach_1_raspberry_pi_esp32_remote_gpu.md) | Real robot prototype where the Raspberry Pi handles robot-side control and the GPU computer runs the heavy model over WiFi. |
| Google Dev Board, ESP32, and webcam | [Approach 2 Guide](docs/approach_2_google_dev_board_esp32.md) | More standalone embedded robot design using a Google Dev Board for onboard AI and ESP32 for motor and ultrasonic control. |
| Laptop-only feasibility test | [Approach 3 Guide](docs/approach_3_laptop_only_model_test.md) | Early low-cost test where the laptop camera and GPU are used to evaluate model latency and live action selection before building the physical robot. |

## Core Idea

`LM-Nav` builds a navigation system from three major components:

1. `GPT-3` extracts landmark names from a natural language instruction.
2. `CLIP` grounds those landmarks in visual observations from the environment.
3. `ViNG` navigates toward the grounded landmarks using a vision-based navigation policy.

This allows the robot to follow high-level language instructions while still using visual navigation models trained on large, unannotated trajectory datasets.

## Further Research

The papers below are useful for studying how `LM-Nav` can be extended or improved.

| Paper | Research Direction | How it relates to LM-Nav |
|---|---|---|
| [VLMaps: Visual Language Maps for Robot Navigation](https://vlmaps.github.io/) | Open-vocabulary spatial mapping | Improves language grounding by building maps that connect natural language queries to spatial locations. |
| [ViNT: A Foundation Model for Visual Navigation](https://proceedings.mlr.press/v229/shah23a.html) | Visual navigation foundation models | Provides a stronger modern navigation backbone that could replace older visual navigation modules such as ViNG. |
| [NoMaD: Goal Masked Diffusion Policies for Navigation and Exploration](https://general-navigation-models.github.io/nomad/) | Diffusion-based navigation policies | Improves goal-directed navigation and exploration, especially in unseen environments. |
| [NaVid: Video-based VLM Plans the Next Step for Vision-and-Language Navigation](https://roboticsconference.org/2024/program/papers/79/) | VLM-based action planning | Uses video history and a VLM to plan next-step navigation actions from language instructions. |
| [Uni-NaVid: A Video-based Vision-Language-Action Model for Unifying Embodied Navigation Tasks](https://roboticsconference.org/program/papers/13/) | Vision-language-action navigation | Extends VLM navigation toward a unified model for instruction following, object search, tracking, and embodied question answering. |
| [NaVILA: Legged Robot Vision-Language-Action Model for Navigation](https://roboticsproceedings.org/rss21/p018.html) | Real-robot VLA navigation | Converts vision-language reasoning into movement commands for legged robot navigation. |
| [HOV-SG: Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation](https://hovsg.github.io/) | 3D scene graph grounding | Improves long-horizon grounding by organizing rooms, objects, and floors into an open-vocabulary 3D scene graph. |
| [VLN-Zero](https://arxiv.org/abs/2509.18592) | Zero-shot navigation | Uses VLM-guided exploration and scene-graph memory to reduce repeated model calls and improve transfer. |
| [VLMnav: End-to-End Navigation with Vision Language Models](https://arxiv.org/abs/2411.05755) | Prompt-based action selection | Frames navigation as VLM question answering, which is closely related to prompt engineering for robot decisions. |
| [VLM-Nav: Mapless UAV Navigation Using Monocular Vision Driven by Vision-Language Models](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0345778) | Mapless VLM navigation | Explores recent VLM-based navigation for UAVs using monocular vision and zero-shot reasoning. |

## Research Roadmap

This project treats `LM-Nav` as the baseline system design. Its central pipeline is:

1. an LLM extracts landmarks from a natural language instruction
2. CLIP grounds those landmarks in visual observations
3. a navigation model executes movement toward the grounded goals

The further research papers are organized around possible improvements to this baseline:

- `VLMaps` and `HOV-SG` are used to study stronger spatial grounding. These methods improve how language is connected to maps, objects, rooms, and 3D scene structure.
- `ViNT` and `NoMaD` are used to study stronger navigation and action models. These methods provide more capable visual navigation backbones that could replace or extend the execution component in `LM-Nav`.
- `NaVid`, `Uni-NaVid`, and `NaVILA` are used to study the latest VLM and VLA navigation direction. These works move toward models that reason over vision, language, and action in a more integrated way.
- `VLMnav` is used as the main prompt-engineering reference because it studies how a vision-language model can choose navigation actions through a question-answering formulation.

## Hardware Summary

The reviewed papers do not all use the same hardware. Some are real-robot systems, while others mainly evaluate navigation models using simulators, image streams, or action-selection frameworks.

| Paper | Hardware or Platform Reported | Board / Compute Reported | Main Sensor / Input |
|---|---|---|---|
| `LM-Nav` | Clearpath Jackal UGV | Exact onboard computer board not stated; VNM runs onboard; LLM/VLM queries are pre-computed on a remote workstation | Front and rear RGB cameras with 170-degree FOV, GPS, wheel encoders, 6-DoF IMU |
| `VLMaps` | Simulation environments and real robot demonstrations; Toyota HSR is acknowledged in project materials | Exact board not stated | RGB-D image stream, camera pose/odometry, RGB-D SLAM / RTAB-Map |
| `HOV-SG` | Boston Dynamics Spot in a real multi-floor building; Habitat-Sim for simulation | Exact board not stated | Calibrated Azure Kinect RGB-D camera and 3D LiDAR |
| `ViNT` | Multiple robots including LoCoBot, Vizbot, Unitree Go1, and Clearpath Jackal | Official deployment code was tested on LoCoBot with NVIDIA Jetson Orin Nano | RGB/fisheye camera observations; some datasets use odometry |
| `NoMaD` | LoCoBot real-world experiments | Paper notes suitability for lower-power onboard compute such as NVIDIA Jetson Orin; official deployment stack follows the ViNT/GNM robot setup | RGB observation history and optional goal image |
| `NaVid` | Simulation and real-world navigation experiments | Exact robot board not stated | Monocular RGB video stream only; no map, odometer, or depth input |
| `Uni-NaVid` | Unitree Go2 robotic dog for real-world deployment | Remote server with NVIDIA A100 GPU; robot communicates through portable Wi-Fi | RealSense D455 RGB camera at 640 x 480, 90-degree HFOV; Unitree LiDAR-L1 for local motion planning |
| `NaVILA` | Legged robot demonstrations including Unitree Go2 and humanoid platforms; Isaac Sim / Isaac Lab benchmarks | VLA runs through a server-based pipeline; exact server board/GPU not stated in the project summary | RGB video frames for VLA; LiDAR/height-map and proprioception for low-level locomotion |
| `VLN-Zero` | Unitree Go2 quadruped in an apartment demonstration; Habitat-Sim for benchmark evaluation | Compute with API access to a VLM; exact onboard board not stated | Intel RealSense D456 RGB-D camera, camera/IMU/odometry, scene-graph map |
| `VLMnav` | Habitat/ObjectNav/GOAT-style simulated embodied agent | VLM inference through API/model calls; no physical robot board reported | RGB-D image, pose, voxel map, action-choice visual prompt |
| `VLM-Nav` | AirSim multirotor UAV simulation | Simulation PC / AirSim environment; physical flight controller board not reported | Monocular RGB image, zero-shot depth estimation, left/right distance sensors, relative heading angle |

For this FYP, the current hardware direction is organized into three approaches. The first approach uses a Raspberry Pi on the robot with an ESP32 for motor-driver and ultrasonic control, while a GPU laptop or desktop runs the heavy model over WiFi. The second approach uses a Google Dev Board with an ESP32 for a more standalone physical robot. The third approach is a laptop-only feasibility test, using the built-in laptop camera and local GPU to test real-time model processing before investing further in physical robot hardware. RGB-D sensors such as RealSense or Azure Kinect, LiDAR, scene-graph mapping, and stronger learned navigation policies can be considered later if the project expands toward spatial mapping or more robust navigation.

## Baseline Implementation Code

The current implementation guides are organized by approach:

| Path | Purpose |
|---|---|
| `docs/approach_1_raspberry_pi_esp32_remote_gpu.md` | Full guide for a Raspberry Pi robot with ESP32 motor and ultrasonic control plus remote GPU inference. |
| `docs/approach_2_google_dev_board_esp32.md` | Full guide for a Google Dev Board robot with ESP32 motor and ultrasonic control. |
| `docs/approach_3_laptop_only_model_test.md` | Full guide for laptop-only camera, GPU, prompt, and live action-selection feasibility testing. |
| `firmware/esp32_robot_controller/esp32_robot_controller.ino` | ESP32 firmware template for ultrasonic sensing and motor-driver command control. |
| `firmware/esp32_ultrasonic_hub/esp32_ultrasonic_hub.ino` | Optional ESP32 sensor-only test firmware for reading four ultrasonic sensors and sending JSON distance/status output. |
| `docs/circuit_wiring_guide.md` | Text-form circuit and wiring guide for the updated ESP32-based physical robot architecture. |

## Methodology Notes

The main methodology for this project is based on [`LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action`](https://proceedings.mlr.press/v205/shah23b).

`LM-Nav` provides a clear modular approach for language-guided robot navigation:

1. use an LLM to extract landmark goals from natural language instructions
2. use CLIP to ground the extracted landmarks in visual observations
3. use a visual navigation model to execute movement toward the selected landmark

This methodology is suitable as the baseline because it connects prompt engineering, language understanding, image-text grounding, and mobile robot navigation in one complete pipeline.

Supporting methodology references:

| Paper | Methodology Role | Link |
|---|---|---|
| LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action | Main baseline methodology for landmark extraction, visual grounding, and navigation execution. | [Paper](https://proceedings.mlr.press/v205/shah23b) |
| VLMnav: End-to-End Navigation with Vision Language Models | Prompt-engineering methodology for choosing robot navigation actions through a VLM question-answering formulation. | [Paper](https://arxiv.org/abs/2411.05755) |
| VLMaps: Visual Language Maps for Robot Navigation | Spatial grounding methodology using open-vocabulary visual-language maps. | [Project](https://vlmaps.github.io/) |
| HOV-SG: Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation | Spatial reasoning methodology using hierarchical 3D scene graphs. | [Project](https://hovsg.github.io/) |
| ViNT: A Foundation Model for Visual Navigation | Navigation model methodology for stronger visual navigation execution. | [Paper](https://proceedings.mlr.press/v229/shah23a.html) |
| NoMaD: Goal Masked Diffusion Policies for Navigation and Exploration | Navigation policy methodology using diffusion-based goal-directed navigation. | [Project](https://general-navigation-models.github.io/nomad/) |

## Research Direction

This project will use `LM-Nav` as the main reference for understanding:
- how natural language instructions can be converted into landmark-based navigation goals
- how vision-language models can connect text landmarks to visual observations
- how pre-trained models can be combined without fine-tuning
- how long-horizon robot navigation can be performed from language commands
- how newer VLM, VLA, mapping, and navigation-policy methods can improve the original `LM-Nav` pipeline

## Project Goals

Possible goals for this repository include:
- summarizing the `LM-Nav` method and architecture
- reproducing a simplified version of the language-to-landmark pipeline
- experimenting with image-text grounding using CLIP or a modern VLM
- documenting the navigation pipeline, assumptions, and limitations
- comparing landmark-based navigation with simpler goal-selection baselines
- reviewing later research papers that improve landmark grounding, spatial reasoning, or navigation execution

## Notes

- This README is intentionally focused on the selected `LM-Nav` paper.
- Additional papers can be added later only if they directly support this research direction.
- The original paper appears in `Proceedings of Machine Learning Research`, volume 205, pages 492-504.
