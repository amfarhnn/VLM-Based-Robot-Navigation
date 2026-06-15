# CHAPTER 2

# LITERATURE REVIEW

## 2.1 Introduction

This chapter reviews literature related to `Prompt Engineering for Mobile Robot Navigation`. The project investigates how a mobile robot can receive a natural language instruction, extract useful navigation information, ground the instruction using visual input, and convert the result into simple movement commands. The work is positioned as a low-cost indoor Final Year Project (FYP) research prototype rather than an industry-level autonomous navigation system.

The main baseline paper for this project is `LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action` by Shah et al. (2023a). LM-Nav is important because it presents a modular architecture for language-guided navigation. Its pipeline separates the problem into language understanding, visual grounding, and navigation execution. This structure is suitable for this FYP because the same idea can be adapted into one focused low-cost Raspberry Pi 4 robot with ESP32 low-level control.

The project does not attempt to reproduce the complete hardware capability of LM-Nav or newer large-scale navigation systems. Instead, the project adapts the core research idea into a student-level Raspberry Pi 4 physical robot. The first prototype uses the basic instruction "Find the green marker". The Raspberry Pi 4 produces structured navigation information, uses the USB-webcam image and lightweight OpenCV grounding, validates the proposed action using ESP32 sensor status, and sends a simple command such as `move_forward`, `turn_left`, `turn_right`, `stop`, or `search` to the ESP32 motor-control layer.

Several related works are reviewed to clarify the project scope. `VLMnav` is included as the main prompt and action-selection reference because it formulates navigation as a question-answering or action-choice task. `VLMaps` and `HOV-SG` are reviewed because they improve spatial grounding, but they require map construction, RGB-D sensing, or scene graph construction, so they are treated as future work rather than the main implementation. `ViNT` and `NoMaD` are reviewed as stronger navigation execution models, but they are not the main focus because this FYP emphasizes prompt engineering, visual grounding, and simple action control. More recent VLM and VLA navigation systems such as `NaVid`, `Uni-NaVid`, and `NaVILA` are also discussed as advanced research directions.

The aim of this chapter is therefore not only to describe related papers, but also to critically compare their suitability for a low-cost indoor robot prototype.

## 2.2 Mobile Robot Navigation and Natural Language Instructions

Mobile robot navigation normally requires a robot to perceive its environment, decide where to move, and execute motion safely. Traditional navigation systems often rely on a map, localization, path planning, obstacle detection, and low-level motor control. These systems are effective when the goal is specified in a robot-readable form, such as a coordinate, waypoint, or selected map location. However, this interaction style is not natural for non-technical users.

Natural language provides a more intuitive interface. A user can describe a goal using objects, places, and relations, for example "go to the door", "find the signboard", or "move toward the chair near the table". These instructions are simple for humans, but they are difficult for robots because they contain semantic meaning that must be connected to the physical environment.

Language-guided navigation therefore requires three main capabilities. First, the robot must understand the user's instruction. Second, it must ground the instruction in visual input or spatial knowledge. Third, it must convert the result into movement. This general process is shown in Figure 2.1.

**Figure 2.1: General language-guided navigation process**

```text
Natural Language Instruction
        |
        v
Prompt Engineering and Language Understanding
        |
        v
Structured Navigation Information
        |
        v
Visual Grounding with Robot Camera
        |
        v
Action or Goal Selection
        |
        v
Robot Movement and Feedback
```

For this FYP, the navigation problem is intentionally limited to indoor environments such as a corridor, room, laboratory, door area, table area, chair area, or signboard location. This limitation is necessary because the proposed hardware uses a USB webcam and simple wheeled motion, not LiDAR, RGB-D SLAM, or high-cost navigation hardware. The controlled environment makes it possible to evaluate the core research question: whether structured prompt engineering can produce useful navigation information for a simple mobile robot.

## 2.3 Prompt Engineering for Robot Navigation

Prompt engineering is the design of model instructions, examples, constraints, and output formats so that an LLM or VLM produces useful responses. In robot navigation, prompt engineering is important because the model output must be connected to a physical robot. A free-form explanation is not enough. The output should contain machine-readable information such as the target object, relevant landmarks, spatial relation, action goal, suggested action, and uncertainty level.

In an LM-Nav-style system, prompt engineering can be used to extract landmarks from a natural language command. In a VLMnav-style system, prompt engineering can ask a model to choose the best next action from a fixed set. For a low-cost robot prototype, both ideas are useful. The robot does not need a complex high-level planner in the first implementation if the prompt output can be converted into a small set of validated motor commands.

**Table 2.1: Roles of prompt engineering in mobile robot navigation**

| Role | Example Output | Purpose in This FYP |
|---|---|---|
| Landmark extraction | `door`, `chair`, `table`, `signboard` | Identify objects or places mentioned by the user |
| Target selection | `target: door` | Decide the main navigation goal |
| Spatial relation extraction | `chair near table` | Preserve relations that affect grounding |
| Route or action interpretation | `move_forward`, `turn_left` | Convert instruction meaning into simple action options |
| Structured output formatting | JSON-style response | Allow Python code on the selected compute platform to parse the result |
| Uncertainty handling | `uncertainty: high` | Prevent unsafe execution when the model is unsure |
| Visual grounding query generation | `door in indoor corridor` | Improve matching between text and webcam image |

For this project, prompt engineering is treated as the interface between human language and robot action. The prompt must not only produce a correct sentence; it must produce an output that can be checked, logged, evaluated, and used by the onboard Raspberry Pi 4 decision logic.

## 2.4 Vision-Language Grounding for Indoor Landmarks

Vision-language grounding is the process of connecting text descriptions to visual observations. For mobile robot navigation, this means matching a target word such as "door", "chair", "table", "corridor", or "signboard" with what the robot sees through its camera.

CLIP and OpenCLIP-style models are common choices for image-text grounding because they embed images and text into a shared feature space. A text query can be compared with an image using cosine similarity:

```text
score(image, text) = cosine_similarity(E_image(image), E_text(text))
```

where `E_image` is the image encoder and `E_text` is the text encoder. The image or region with the highest score can be treated as the most relevant match. A modern VLM may also be used by asking a question such as "Does this image contain a door?" or "Which action should the robot take to find the chair near the table?"

However, visual grounding remains a limitation for low-cost robots. A USB webcam provides only RGB images and does not directly provide depth, object distance, or a 3D map. The system may also struggle when multiple similar objects are visible, when lighting is poor, or when the target is partly outside the camera view. For this reason, the proposed project focuses on simple indoor landmarks and a small action set rather than full autonomous navigation in complex environments.

## 2.5 LM-Nav as the Main Baseline

### 2.5.1 Overview of LM-Nav

`LM-Nav: Robotic Navigation with Large Pre-Trained Models of Language, Vision, and Action` by Shah et al. (2023a) is the main baseline for this project. LM-Nav addresses the problem that many visual navigation systems expect a goal image, while human users naturally provide language instructions. The paper avoids collecting a large language-annotated robot navigation dataset by composing pre-trained models.

The LM-Nav pipeline contains three main stages:

1. GPT-3 extracts landmarks from the natural language instruction.
2. CLIP grounds the extracted landmarks in visual observations.
3. ViNG navigates toward the selected visual goal.

This pipeline is shown in Figure 2.2.

**Figure 2.2: LM-Nav baseline pipeline**

```text
User Language Instruction
        |
        v
LLM Landmark Extraction
        |
        v
CLIP Visual Grounding
        |
        v
Visual Navigation Model
        |
        v
Robot Navigation Toward Goal
```

### 2.5.2 Strength of LM-Nav

The main strength of LM-Nav is its modular architecture. It does not require one end-to-end model that directly maps language and images to motor commands. Instead, it separates language understanding, visual grounding, and action execution. This separation is useful for research because each module can be tested and improved independently.

LM-Nav is also important because it demonstrates that pre-trained models can be combined for robot navigation without training a new language-conditioned navigation model from scratch. This idea is suitable for an FYP because collecting a large robot dataset is not realistic within the time and cost constraints of a student project.

### 2.5.3 Limitation of LM-Nav

LM-Nav also has limitations that motivate this project. The language module mainly extracts landmarks. This may be insufficient for instructions that include spatial relations, route order, or constraints. For example, "move toward the chair near the table" should not be reduced only to `chair` and `table`; the relation `chair near table` is also important.

Another limitation is hardware and navigation complexity. LM-Nav was demonstrated with a more capable outdoor robot platform and a visual navigation model. A student FYP setup using a Raspberry Pi 4, ESP32 sensor and motor control, USB webcam, two ultrasonic sensors, and four DC motors cannot reproduce the full navigation capability directly. Therefore, this project uses LM-Nav as an architectural inspiration, not as a full implementation target.

### 2.5.4 Relevance to This Project

LM-Nav provides the central structure for the proposed prototype: language understanding, visual grounding, and action execution. The difference is that this project adapts the final execution stage into a simple action-control system. Instead of using a full visual navigation policy, the Raspberry Pi 4 chooses one of a small set of actions, checks obstacle status from the ESP32 ultrasonic module, and sends validated commands to the ESP32 motor-control layer. This makes the project realistic for a low-cost indoor robot while preserving the research value of structured prompt engineering.

## 2.6 VLMnav as a Prompt-Based Action Selection Reference

`VLMnav: End-to-End Navigation with Vision Language Models` by Goetting et al. (2024) is highly relevant because it formulates navigation as a question-answering problem. Instead of requiring the model to output a long navigation plan, the system can ask a VLM to choose among possible actions. This is close to the needs of the proposed robot because the first prototype only needs a small action set: `move_forward`, `turn_left`, `turn_right`, `stop`, and `search`.

The strength of VLMnav is that it connects visual observation, language instruction, and action selection through prompting. This supports the idea that prompt design can affect not only landmark extraction but also robot movement decisions. For example, a prompt can ask whether the current webcam image contains the target, whether the robot should turn to search, or whether it should stop because the target has been found.

The limitation is that direct VLM action selection may not be safe enough for unsupervised robot control. VLM outputs can be inconsistent, and the model may choose an action even when the target is not visible or the instruction is ambiguous. For this reason, the proposed FYP will validate the structured output, uncertainty level, model latency, and ESP32 ultrasonic obstacle status before physical motor execution. VLMnav is therefore treated as a prompt/action-selection reference, while the robot remains a controlled research prototype.

## 2.7 Spatial Grounding Methods: VLMaps and HOV-SG

Spatial grounding methods improve the connection between language and the physical environment. Two important examples are `VLMaps` and `HOV-SG`.

`VLMaps: Visual Language Maps for Robot Navigation` by Huang et al. (2023) builds an open-vocabulary visual-language map. Instead of matching a text query only to the current camera image, the robot can query a map that stores semantic visual features. The strength of VLMaps is that it provides spatial memory and can connect language to locations. Its limitation is that it requires map construction, camera pose information, and RGB-D or mapping support. This makes it more complex than the first version of the proposed FYP robot.

`HOV-SG: Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation` by Werby et al. (2024) uses a hierarchical 3D scene graph to represent floors, rooms, and objects. This is powerful for long-horizon and multi-room navigation because the robot can reason about object and room relationships. However, it requires segmentation, 3D perception, graph construction, and more advanced sensing. This is not suitable for the first low-cost prototype, but it is valuable as a future improvement direction.

Both papers show that spatial grounding is important. They also highlight a gap for this project: a low-cost robot without RGB-D mapping still needs a way to preserve spatial relations from language. Structured prompt engineering can support this by extracting fields such as `target`, `landmarks`, and `spatial_relation`, even if the first implementation only uses webcam-based grounding.

## 2.8 Navigation Execution Models: ViNT and NoMaD

The execution stage determines how a robot physically moves toward a target. In advanced systems, this may involve a learned navigation policy, obstacle avoidance, and goal-conditioned control. `ViNT` and `NoMaD` are important because they represent stronger navigation execution methods than a simple rule-based motor command system.

`ViNT: A Foundation Model for Visual Navigation` by Shah et al. (2023b) proposes a visual navigation foundation model trained across diverse robot datasets. Its strength is generalization across platforms and environments. Its limitation for this FYP is that deploying and validating a full visual navigation model is outside the main scope. This project focuses on prompt engineering, visual grounding, and simple action control, not training or deploying a foundation navigation policy.

`NoMaD: Goal Masked Diffusion Policies for Navigation and Exploration` by Sridhar et al. (2023) uses a diffusion-based policy for goal-directed navigation and exploration. Its strength is stronger navigation behavior and exploration ability. Its limitation is that it requires a more complex policy deployment pipeline and suitable robot data. For the proposed project, NoMaD is therefore best treated as future work after the basic Raspberry Pi 4 physical robot pipeline is functioning.

These works are important because they show how the simple action-control layer in this FYP could later be replaced by a stronger navigation model. However, they are not the main implementation because the research focus is prompt-engineered interpretation of natural language instructions.

## 2.9 Recent VLM and VLA Navigation Systems

Recent work has moved toward more integrated VLM and VLA navigation systems. These systems can reason over video, language, and action more directly than the earlier modular LM-Nav design.

`NaVid` by Zhang et al. (2024) uses video-based VLM planning for vision-and-language navigation. Its strength is that it uses temporal visual context rather than a single image. This is useful for robot navigation because the current view alone may not contain enough information. Its limitation is that video-based reasoning and model inference can be expensive for a small embedded robot.

`Uni-NaVid` by Zhang et al. (2026) extends the video-based approach toward a unified model for multiple embodied navigation tasks. Its strength is broad task coverage. Its limitation is that the system is more advanced and resource-intensive than a first FYP prototype.

`NaVILA` by Cheng et al. (2025) studies VLA navigation for legged robots. Its strength is the connection between vision-language reasoning and real robot movement. Its limitation for this project is that it focuses on more complex legged platforms and server-style model pipelines, while the proposed robot is a wheeled low-cost indoor platform.

These papers are relevant because they show the direction of future navigation research. However, they also reinforce the need for a realistic baseline prototype. A student project can first demonstrate prompt-engineered instruction parsing, webcam grounding, and simple action control before attempting advanced VLA navigation.

## 2.10 Critical Comparison of Related Works

The reviewed papers differ significantly in method, hardware complexity, cost, and suitability for student-level implementation. Table 2.2 compares the papers based on their main method, strength, limitation, and relevance to this project.

**Table 2.2: Critical comparison of related papers**

| Paper | Main Method | Hardware or Platform | Strength | Limitation | Relevance to This Project |
|---|---|---|---|---|---|
| `LM-Nav` | GPT-3 landmark extraction, CLIP grounding, ViNG navigation | Real robot platform with RGB cameras and navigation sensors | Clear modular baseline for language to vision to action | Landmark-only extraction may lose spatial relations; full navigation setup is more complex than this FYP | Main baseline architecture adapted into a low-cost indoor prototype |
| `VLMnav` | VLM question-answering for action choice | Simulation-style embodied navigation setup with visual observations and action choices | Strong reference for prompt-based action selection | Direct VLM actions require validation before real robot control | Supports the proposed fixed action set and prompt design |
| `VLMaps` | Open-vocabulary visual-language maps | Mapping-based setup using RGB-D or pose-supported observations | Stronger spatial grounding and language-map querying | Requires map construction and additional sensing | Future improvement for map-based grounding |
| `HOV-SG` | Hierarchical open-vocabulary 3D scene graph | 3D perception, scene graph construction, and robot/simulator experiments | Supports object, room, and floor-level reasoning | Too complex for first low-cost webcam prototype | Future improvement for structured spatial memory |
| `ViNT` | Visual navigation foundation model | Multi-robot visual navigation datasets and deployment platforms | Stronger visual navigation execution | Does not focus on prompt engineering; deployment is beyond initial scope | Possible future replacement for simple action control |
| `NoMaD` | Diffusion-based goal-conditioned navigation policy | Robot navigation experiments with visual observations | Improves exploration and goal reaching | Requires navigation policy deployment and data support | Future work after baseline prototype |
| `NaVid` | Video-based VLM next-step planning | Simulation and real-world video navigation experiments | Uses temporal context for navigation decisions | More model and compute intensive than single-webcam baseline | Future direction for video-based reasoning |
| `Uni-NaVid` | Unified video-based VLA navigation model | Advanced embodied navigation platforms | Supports multiple navigation task types | Resource-intensive and not suitable as first implementation | Long-term improvement direction |
| `NaVILA` | Vision-language-action navigation for legged robots | Legged robot demonstrations and simulation benchmarks | Connects VLA reasoning to real movement | Focuses on complex legged platforms and larger model pipelines | Relevant conceptually but not the main hardware target |

The comparison shows that LM-Nav and VLMnav are the most directly relevant to this project. LM-Nav provides the modular structure, while VLMnav supports the idea of selecting actions through prompt-based reasoning. VLMaps, HOV-SG, ViNT, NoMaD, NaVid, Uni-NaVid, and NaVILA are important, but they require additional sensing, mapping, model deployment, or compute resources that are not realistic for the first prototype.

## 2.11 Hardware Suitability for This FYP

A critical issue for this project is hardware feasibility. Many research systems use expensive robots, RGB-D cameras, LiDAR, server GPUs, or advanced navigation policies. This FYP must use a lower-cost platform while still preserving a meaningful research contribution. Table 2.3 summarizes the suitability of literature components for the proposed implementation.

**Table 2.3: Hardware and method suitability for this FYP**

| Component or Method from Literature | Used in Original Paper or Related Work | Suitability for This FYP | Decision |
|---|---|---|---|
| RGB camera or webcam | Used in LM-Nav and many VLM navigation works as visual input | Highly suitable because it is low-cost and easy to connect through USB | An unbranded 1080p USB webcam will be used as the main visual sensor |
| Raspberry Pi 4 | Related to low-cost onboard Linux robot-compute platforms | Suitable for Python, OpenCV, USB devices, lightweight inference, and flexible development | Finalized and only physical compute board |
| ESP32 microcontroller | Not central in reviewed AI navigation papers, but common in low-cost sensor and motor integration | Suitable for reading ultrasonic sensors and controlling a motor driver independently from model inference | Will be used as the motor, sensor, and local safety controller |
| Two HC-SR04 ultrasonic sensors | Not the main perception method in the reviewed VLM papers | Suitable as a low-cost front-left and front-right proximity safety aid | Will be used for simple front obstacle awareness |
| GY-291 / ADXL345 accelerometer | Not the main perception method in the reviewed VLM papers | Suitable for three-axis acceleration, roll/pitch tilt, motion, vibration, and shock observations | Will support physical movement and chassis-condition monitoring |
| Two MX1508 dual motor drivers | Common low-cost motor-control hardware rather than a reviewed AI-navigation component | Suitable for controlling four small DC gear motors after current-rating verification | Will be used as the shared motor-driver subsystem |
| Four DC motors and chassis | Common in low-cost mobile robots but not the focus of high-level papers | Suitable for simple wheeled movement | Will be used for movement execution |
| 18650 battery pack | Standard power source for small mobile robot prototypes | Suitable for mobile operation when voltage and current requirements are handled safely | Will be used as the robot power source |
| RGB-D camera | Used or required by mapping-based works such as VLMaps and HOV-SG-style pipelines | Useful but increases cost and complexity | Optional future improvement |
| LiDAR | Used in some advanced robot navigation and scene understanding systems | Useful for safety and mapping but too costly for the first prototype | Not used in the baseline prototype |
| Full 3D scene graph | Used in HOV-SG and related spatial reasoning systems | Strong for spatial reasoning but requires 3D perception and mapping | Future improvement only |
| Large VLA model or server GPU | Used in advanced VLA systems such as NaVILA or Uni-NaVid-style pipelines | Powerful but outside the finalized onboard implementation scope | Future work only |
| CLIP, OpenCLIP, or VLM grounding | Used in LM-Nav-style grounding and VLM navigation | Suitable for prototype testing with indoor images | Will be used or evaluated depending on available compute |
| Learned navigation policy such as ViNT or NoMaD | Used in advanced navigation execution research | Useful but outside the main prompt-engineering scope | Future replacement for simple action control |

This table supports the design decision to build a low-cost indoor prototype. The project will not claim full autonomy in complex environments. Instead, it will demonstrate a baseline pipeline that future researchers can improve with better sensors, mapping, and navigation policies.

The positioning of the reviewed papers around the proposed baseline is shown in Figure 2.3.

**Figure 2.3: Positioning of related works around LM-Nav**

```text
Advanced VLM/VLA Navigation
NaVid, Uni-NaVid, NaVILA
        |
        v
LM-Nav Baseline Architecture
Language Understanding -> Visual Grounding -> Navigation Execution
        |
        v
Low-Cost FYP Prototype
Raspberry Pi 4 onboard compute
Shared ESP32 sensor, safety, and motor control
        |
        v
Simple Indoor Action Set
move_forward, turn_left, turn_right, stop, search

Spatial grounding improvements: VLMaps, HOV-SG
Navigation execution improvements: ViNT, NoMaD
Prompt/action selection reference: VLMnav
```

## 2.12 Research Gap and Motivation

The literature shows that language-guided robot navigation is an active research area, but several gaps remain for a low-cost FYP prototype.

First, existing systems can perform language-guided navigation, but many require expensive hardware, complex mapping, large models, or server-level compute. These systems are valuable research contributions, but they are not directly suitable for a student prototype using a Raspberry Pi 4, ESP32, USB webcam, two ultrasonic sensors, two MX1508 motor drivers, GY-291 accelerometer, and four DC gear motors.

Second, LM-Nav provides a strong modular baseline, but its language stage mainly extracts landmarks. Natural language instructions often include spatial relations and route information, such as "near the table", "turn left after the door", or "find the signboard". A low-cost prototype still needs to preserve this information, even if the first grounding module is simple.

Third, many advanced methods improve spatial grounding or navigation execution, but they do not directly answer how structured prompt engineering can support a simple indoor robot. VLMaps and HOV-SG show the value of maps and scene graphs, while ViNT and NoMaD show stronger navigation execution. However, this project begins earlier in the pipeline by asking how natural language can be converted into structured, validated robot action information.

Fourth, there is a need for a focused baseline physical prototype that future researchers can extend. A Raspberry Pi 4 robot with webcam grounding, ESP32 safety control, acceleration and tilt feedback, and simple actions provides a practical platform for later improvements such as RGB-D sensing, LiDAR, scene graph mapping, ViNT, NoMaD, or advanced VLM/VLA models.

**Table 2.4: Research gap synthesis and project strategy**

| Research Gap | Supporting Literature | Project Strategy |
|---|---|---|
| Many language-guided navigation systems use costly or complex hardware | LM-Nav, HOV-SG, NaVILA, Uni-NaVid | Build one focused low-cost Raspberry Pi 4 prototype with ESP32 sensor, safety, and motor control |
| Landmark extraction alone may lose spatial relations and route information | LM-Nav, VLMaps, HOV-SG | Use structured prompt output with target, landmarks, spatial relation, action goal, suggested action, and uncertainty |
| VLM action selection needs validation before real robot execution | VLMnav | Check uncertainty, latency, approved actions, and ESP32 ultrasonic status before sending commands to the ESP32 motor-control layer |
| Mapping and scene-graph systems are useful but complex | VLMaps, HOV-SG | Treat RGB-D mapping and scene graphs as future work |
| Strong navigation policies are beyond the first prototype | ViNT, NoMaD | Start with simple action control and document future replacement options |

Based on these gaps, the project is motivated by the following research direction:

How can structured prompt engineering support visual grounding and simple action selection for a low-cost indoor mobile robot navigation prototype?

## 2.13 Chapter Summary

This chapter reviewed literature related to prompt engineering for mobile robot navigation. LM-Nav was identified as the main baseline because it provides a clear modular architecture of language understanding, visual grounding, and navigation execution. VLMnav was reviewed as the main prompt/action-selection reference because it frames navigation as a question-answering or action-choice task.

The chapter also reviewed VLMaps and HOV-SG as spatial grounding improvements, ViNT and NoMaD as stronger navigation execution models, and NaVid, Uni-NaVid, and NaVILA as advanced VLM/VLA navigation directions. These works show the potential of language-guided navigation, but they also reveal limitations related to cost, sensing requirements, compute resources, and implementation complexity.

The research gap is that there is a need for a low-cost indoor physical prototype that studies structured prompt engineering for simple mobile robot navigation. Chapter 3 explains how this project addresses the gap using one Raspberry Pi 4 implementation with an ESP32 motor, sensor, and safety layer.

## REFERENCE

Cheng, A.-C., Ji, Y., Yang, Z., Gongye, Z., Zou, X., Kautz, J., Biyik, E., Yin, H., Liu, S., & Wang, X. (2025). NaVILA: Legged robot vision-language-action model for navigation. *Proceedings of Robotics: Science and Systems*. https://doi.org/10.15607/RSS.2025.XXI.018

Goetting, D., Singh, H. G., & Loquercio, A. (2024). *End-to-end navigation with vision language models: Transforming spatial reasoning into question-answering*. arXiv. https://doi.org/10.48550/arXiv.2411.05755

Huang, C., Mees, O., Zeng, A., & Burgard, W. (2023). Visual language maps for robot navigation. *Proceedings of the IEEE International Conference on Robotics and Automation (ICRA)*. https://vlmaps.github.io/

Shah, D., Osinski, B., Ichter, B., & Levine, S. (2023a). LM-Nav: Robotic navigation with large pre-trained models of language, vision, and action. *Proceedings of the 6th Conference on Robot Learning, Proceedings of Machine Learning Research, 205*, 492-504. https://proceedings.mlr.press/v205/shah23b.html

Shah, D., Sridhar, A., Dashora, N., Stachowicz, K., Black, K., Hirose, N., & Levine, S. (2023b). ViNT: A foundation model for visual navigation. *Proceedings of the 7th Conference on Robot Learning, Proceedings of Machine Learning Research, 229*, 711-733. https://proceedings.mlr.press/v229/shah23a.html

Sridhar, A., Shah, D., Glossop, C., & Levine, S. (2023). *NoMaD: Goal masked diffusion policies for navigation and exploration*. arXiv. https://arxiv.org/abs/2310.07896

Werby, A., Huang, C., Buchner, M., Valada, A., & Burgard, W. (2024). Hierarchical open-vocabulary 3D scene graphs for language-grounded robot navigation. *Proceedings of Robotics: Science and Systems*. https://doi.org/10.15607/RSS.2024.XX.077

Zhang, J., Wang, K., Xu, R., Zhou, G., Hong, Y., Fang, X., Wu, Q., Zhang, Z., & Wang, H. (2024). NaVid: Video-based VLM plans the next step for vision-and-language navigation. *Proceedings of Robotics: Science and Systems*. https://doi.org/10.15607/RSS.2024.XX.079

Zhang, J., Wang, K., Wang, S., Li, M., Liu, H., Wei, S., Wang, Z., Zhang, Z., & Wang, H. (2026). Uni-NaVid: A video-based vision-language-action model for unifying embodied navigation tasks. *Robotics: Science and Systems 2026 Program*. https://roboticsconference.org/program/papers/13/
