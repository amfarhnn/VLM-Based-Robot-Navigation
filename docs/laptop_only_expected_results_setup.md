# Docker Laptop-Only Expected-Results Setup

This setup is a separate FYP1 feasibility and expected-results demonstration.
It is **not** another physical robot implementation and does not change the
finalized Raspberry Pi 4 hardware purpose.

The browser captures the laptop webcam and sends frames to a local Docker
container. The container performs the Python/OpenCV processing and returns
`TURN LEFT`, `TURN RIGHT`, `MOVE FORWARD`, `SEARCH`, or `STOP`. The user
manually moves the laptop according to the displayed instruction.

```text
Laptop webcam -> browser -> Docker Python/OpenCV service
                         -> structured goal and displayed action
                         -> JSONL result log
```

This design is used because Docker Desktop on Windows does not reliably expose
the laptop webcam as a Linux `/dev/video` device. Browser camera capture works
cleanly while the processing environment remains isolated and reproducible.

## Purpose

Use this option before the physical robot is ready to demonstrate:

- structured interpretation of a simple goal
- live webcam perception
- restricted action selection
- expected action changes when the target moves in the image
- repeatable containerized software setup
- result logging for Chapter 4 expected-results discussion

## First Demo Goal

Use the grey-blue corridor door shown in the selected project test area:

```text
find the door
```

The structured output identifies the target as `door`. OpenCV detects this
specific door using its grey-blue colour, tall rectangular shape, area, and
vertical position. The detector is intentionally tuned to this test door and
must not be presented as a general door-recognition model. This lightweight
method is easy to reproduce and does not require downloading a large model.

If corridor lighting changes significantly, tune `DOOR_HSV_LOWER` and
`DOOR_HSV_UPPER` in
`src/laptop_expected_results/laptop_navigation_demo.py`. Keep the door visible
from top to bottom during the first tests so its vertical shape can be checked.

## Requirements

- Windows 10 or Windows 11 laptop
- Docker Desktop using Linux containers
- Working browser webcam permission
- Available local port `8000`

Confirm Docker is running:

```powershell
docker --version
docker compose version
```

## Build and Run

From the project root:

```powershell
docker compose -f docker-compose.laptop-demo.yml up --build
```

Open:

```text
http://localhost:8000
```

Select **Start Camera** and allow browser camera access, then point and manually
move the laptop toward the grey-blue test door.

The container health endpoint is:

```text
http://localhost:8000/health
```

## Stop the Demo

Press `Ctrl+C` in the Docker terminal, then run:

```powershell
docker compose -f docker-compose.laptop-demo.yml down
```

To rebuild after changing Python or web-interface code:

```powershell
docker compose -f docker-compose.laptop-demo.yml build --no-cache
docker compose -f docker-compose.laptop-demo.yml up
```

## Expected Displayed Actions

| Webcam Result | Displayed Instruction | Manual User Action |
|---|---|---|
| Door not detected | `SEARCH` | Rotate or move the laptop slowly |
| Door appears on left | `TURN LEFT` | Move the laptop view left |
| Door appears on right | `TURN RIGHT` | Move the laptop view right |
| Door is centred | `MOVE FORWARD` | Carry the laptop toward the door |
| Door fills a large image area | `STOP` | Stop moving |

## Docker Files

| File | Purpose |
|---|---|
| `docker-compose.laptop-demo.yml` | Builds, starts, and maps the service to port 8000 |
| `src/laptop_expected_results/Dockerfile` | Defines the Python container |
| `src/laptop_expected_results/requirements.txt` | Pins Flask, OpenCV, NumPy, and Gunicorn |
| `src/laptop_expected_results/web_app.py` | Processes browser webcam frames |
| `src/laptop_expected_results/templates/index.html` | Browser webcam and result interface |
| `src/laptop_expected_results/laptop_navigation_demo.py` | Shared structured-goal and action logic |

## Expected-Results Evidence

The host project receives the container log through a bind mount:

```text
logs/laptop_expected_results.jsonl
```

For FYP1, record:

- screenshots showing each displayed action
- ten or more repeated runs
- whether the displayed action matches the target position
- action-change response time
- the Docker image/build version used
- failure cases caused by lighting, similar colours, or partial target view

## Troubleshooting

### Browser does not show the webcam

- Open `http://localhost:8000`, not a remote IP address.
- Allow camera permission in the browser.
- Close applications that exclusively use the webcam.
- Reload the page and select **Start Camera** again.

### Port 8000 is already in use

Change the host side of the port mapping:

```yaml
ports:
  - "8080:8000"
```

Then open `http://localhost:8080`.

### Container fails to start

```powershell
docker compose -f docker-compose.laptop-demo.yml logs
docker compose -f docker-compose.laptop-demo.yml ps
```

This evidence supports the expected result that the planned restricted action
interface behaves logically. Final FYP2 claims must use the physical Raspberry
Pi 4 robot and measured robot results.
