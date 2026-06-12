from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "drawio"
SOURCE_FILES = [
    ROOT / "chapter_1_introduction.md",
    ROOT / "literature_review.md",
    ROOT / "chapter_3_methodology.md",
    ROOT / "chapter_4_results_and_discussion.md",
]

FIGURE_RE = re.compile(r"\*\*Figure\s+(\d+\.\d+):\s*(.+?)\*\*")
TABLE_RE = re.compile(r"\*\*Table\s+(\d+\.\d+):\s*(.+?)\*\*")

VERTEX_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    "fontSize=14;"
)
DECISION_STYLE = (
    "rhombus;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
    "fontSize=14;"
)
NOTE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
    "fontSize=13;"
)
EDGE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
    "html=1;endArrow=block;endFill=1;strokeWidth=2;"
)
FEEDBACK_EDGE_STYLE = EDGE_STYLE + "dashed=1;strokeColor=#d79b00;"
TABLE_TITLE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"
    "fontStyle=1;fontSize=16;"
)
TABLE_HEADER_STYLE = (
    "shape=rectangle;whiteSpace=wrap;html=1;align=center;verticalAlign=middle;"
    "spacing=8;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=12;"
)
TABLE_BODY_STYLE = (
    "shape=rectangle;whiteSpace=wrap;html=1;align=left;verticalAlign=middle;"
    "spacing=8;strokeColor=#666666;fontSize=11;"
)


class DrawioBuilder:
    def __init__(self, name: str, page_width: int, page_height: int) -> None:
        self.mxfile = ET.Element(
            "mxfile",
            {
                "host": "app.diagrams.net",
                "modified": "2026-05-09T00:00:00.000Z",
                "agent": "Codex",
                "version": "24.7.17",
            },
        )
        diagram = ET.SubElement(
            self.mxfile,
            "diagram",
            {
                "id": slugify(name),
                "name": name,
            },
        )
        model = ET.SubElement(
            diagram,
            "mxGraphModel",
            {
                "dx": "1600",
                "dy": "1200",
                "grid": "1",
                "gridSize": "10",
                "guides": "1",
                "tooltips": "1",
                "connect": "1",
                "arrows": "1",
                "fold": "1",
                "page": "1",
                "pageScale": "1",
                "pageWidth": str(page_width),
                "pageHeight": str(page_height),
                "math": "0",
                "shadow": "0",
            },
        )
        self.root = ET.SubElement(model, "root")
        ET.SubElement(self.root, "mxCell", {"id": "0"})
        ET.SubElement(self.root, "mxCell", {"id": "1", "parent": "0"})
        self.next_id = 2

    def _id(self) -> str:
        current = str(self.next_id)
        self.next_id += 1
        return current

    def add_vertex(
        self,
        value: str,
        style: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> str:
        cell_id = self._id()
        cell = ET.SubElement(
            self.root,
            "mxCell",
            {
                "id": cell_id,
                "value": value,
                "style": style,
                "vertex": "1",
                "parent": "1",
            },
        )
        ET.SubElement(
            cell,
            "mxGeometry",
            {
                "x": str(x),
                "y": str(y),
                "width": str(width),
                "height": str(height),
                "as": "geometry",
            },
        )
        return cell_id

    def add_edge(
        self,
        source: str,
        target: str,
        value: str = "",
        style: str = EDGE_STYLE,
    ) -> str:
        cell_id = self._id()
        attrib = {
            "id": cell_id,
            "style": style,
            "edge": "1",
            "parent": "1",
            "source": source,
            "target": target,
        }
        if value:
            attrib["value"] = value
        cell = ET.SubElement(self.root, "mxCell", attrib)
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        return cell_id

    def write(self, path: Path) -> None:
        ET.indent(self.mxfile, space="  ")
        tree = ET.ElementTree(self.mxfile)
        tree.write(path, encoding="UTF-8", xml_declaration=True)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", cleaned).strip("_")


def estimate_height(text: str, width: int, font_size: int = 11, minimum: int = 38) -> int:
    chars_per_line = max(12, int(width / max(7, font_size * 0.65)))
    line_count = 0
    for line in text.splitlines() or [""]:
        line_count += max(1, math.ceil(len(line) / chars_per_line))
    return max(minimum, int(line_count * (font_size * 1.7) + 16))


def parse_markdown_table(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    header = split_table_row(lines[0])
    rows = [split_table_row(line) for line in lines[2:]]
    return header, rows


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_vertical_flow(name: str, steps: list[str], out_path: Path) -> None:
    width = 980
    x = 340
    box_width = 300
    y = 40
    positions: list[tuple[str, int, int]] = []
    builder = DrawioBuilder(name, page_width=1169, page_height=1654)
    previous = None
    for step in steps:
        height = estimate_height(step, box_width, font_size=14, minimum=58)
        node = builder.add_vertex(step, VERTEX_STYLE, x, y, box_width, height)
        positions.append((node, y, height))
        if previous is not None:
            builder.add_edge(previous, node)
        previous = node
        y += height + 36
    builder.write(out_path)


def render_figure_2_3(name: str, out_path: Path) -> None:
    builder = DrawioBuilder(name, page_width=1700, page_height=1200)
    top = builder.add_vertex(
        "Advanced VLM/VLA Navigation\nNaVid, Uni-NaVid, NaVILA",
        VERTEX_STYLE,
        560,
        60,
        420,
        90,
    )
    left = builder.add_vertex(
        "Spatial Grounding Improvements\nVLMaps, HOV-SG",
        VERTEX_STYLE,
        80,
        300,
        360,
        90,
    )
    center = builder.add_vertex(
        "LM-Nav Baseline Architecture\nLanguage -> Visual Grounding -> Execution",
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;fontSize=15;",
        560,
        300,
        420,
        100,
    )
    right = builder.add_vertex(
        "Navigation Execution Improvements\nViNT, NoMaD",
        VERTEX_STYLE,
        1110,
        300,
        360,
        90,
    )
    prompt = builder.add_vertex(
        "Prompt-Based Action Selection\nVLMnav",
        NOTE_STYLE,
        560,
        520,
        420,
        90,
    )
    prototype = builder.add_vertex(
        "Low-Cost Physical FYP Prototype\nCoral Dev Board onboard compute\nESP32 sensor, safety, and motor control",
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=15;",
        560,
        710,
        420,
        140,
    )
    action = builder.add_vertex(
        "Simple Indoor Action Set\nmove_forward, turn_left, turn_right, stop, search",
        NOTE_STYLE,
        560,
        950,
        420,
        90,
    )
    builder.add_edge(left, center)
    builder.add_edge(center, right)
    builder.add_edge(top, center)
    builder.add_edge(center, prompt)
    builder.add_edge(prompt, prototype)
    builder.add_edge(prototype, action)
    builder.write(out_path)


def render_figure_3_1(name: str, out_path: Path) -> None:
    builder = DrawioBuilder(name, page_width=1500, page_height=1900)
    schema = builder.add_vertex(
        "Define Prompt Schema,\nActions, Scenarios, and Metrics",
        VERTEX_STYLE,
        360,
        40,
        330,
        90,
    )
    hardware = builder.add_vertex(
        "Complete Coral, ESP32,\nSensor, and Motor Wiring",
        VERTEX_STYLE,
        360,
        170,
        330,
        70,
    )
    low_level = builder.add_vertex(
        "Validate ESP32 Sensors,\nSafety, and Motor Control",
        VERTEX_STYLE,
        360,
        280,
        330,
        80,
    )
    coral = builder.add_vertex(
        "Install Mendel Linux and Verify\nCoral Edge TPU Inference",
        VERTEX_STYLE,
        360,
        410,
        330,
        80,
    )
    integrate = builder.add_vertex(
        "Integrate Webcam, Prompt Parser,\nDetector, UART, and Logging",
        VERTEX_STYLE,
        360,
        540,
        330,
        80,
    )
    scenarios = builder.add_vertex(
        "Run Equivalent Controlled\nIndoor Scenarios",
        VERTEX_STYLE,
        360,
        670,
        330,
        70,
    )
    valid = builder.add_vertex(
        "Is Output Valid,\nResponsive, and Safe?",
        DECISION_STYLE,
        410,
        790,
        230,
        110,
    )
    evaluate = builder.add_vertex(
        "Measure Prompt Quality, Detection,\nLatency, Safety, and Movement",
        VERTEX_STYLE,
        360,
        950,
        330,
        90,
    )
    analysis = builder.add_vertex(
        "Analyse Failures and\nReport Results",
        VERTEX_STYLE,
        360,
        1090,
        330,
        70,
    )
    stop = builder.add_vertex(
        "Stop, Log Failure, and Adjust\nPrompt, Model, Safety, or Hardware",
        NOTE_STYLE,
        810,
        800,
        330,
        100,
    )

    for source, target in [
        (schema, hardware),
        (hardware, low_level),
        (low_level, coral),
        (coral, integrate),
        (integrate, scenarios),
        (scenarios, valid),
        (evaluate, analysis),
    ]:
        builder.add_edge(source, target)

    builder.add_edge(valid, evaluate, value="Yes")
    builder.add_edge(valid, stop, value="No", style=FEEDBACK_EDGE_STYLE)
    builder.add_edge(stop, schema, style=FEEDBACK_EDGE_STYLE)
    builder.write(out_path)


def render_placeholder_figure(name: str, out_path: Path, message: str) -> None:
    builder = DrawioBuilder(name, page_width=1169, page_height=900)
    builder.add_vertex(
        name,
        TABLE_TITLE_STYLE,
        80,
        60,
        1000,
        70,
    )
    builder.add_vertex(
        message,
        (
            "rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;"
            "fillColor=#f8f9fa;strokeColor=#666666;fontSize=18;"
        ),
        120,
        180,
        920,
        560,
    )
    builder.write(out_path)


def render_figure_3_7(name: str, out_path: Path) -> None:
    builder = DrawioBuilder(name, page_width=1700, page_height=1200)
    battery = builder.add_vertex("3S 18650\nBattery Pack", VERTEX_STYLE, 680, 40, 300, 80)
    switch = builder.add_vertex("Main Power\nSwitch and Fuse", VERTEX_STYLE, 680, 170, 300, 80)
    motor_buck = builder.add_vertex("Adjustable Motor\nBuck Converter", NOTE_STYLE, 140, 340, 300, 80)
    power_module = builder.add_vertex("3S-Compatible Power-Bank\nCharging / Output Module", NOTE_STYLE, 680, 340, 300, 90)
    drivers = builder.add_vertex("Two MX1508 Motor Drivers\nPower from motor buck\nControl from ESP32", VERTEX_STYLE, 140, 520, 300, 110)
    motors = builder.add_vertex("Four DC Gear Motors\nand Wheels", VERTEX_STYLE, 140, 730, 300, 90)
    compute = builder.add_vertex("Coral Dev Board\nOnboard Compute", VERTEX_STYLE, 680, 520, 300, 90)
    webcam = builder.add_vertex("USB Webcam", VERTEX_STYLE, 520, 730, 260, 80)
    esp32 = builder.add_vertex("ESP32\nSensor + Motor Control", VERTEX_STYLE, 1060, 520, 300, 90)
    sensors = builder.add_vertex("Two HC-SR04 Sensors\nFront Left + Front Right", VERTEX_STYLE, 1000, 730, 300, 90)
    imu = builder.add_vertex("GY-291 / ADXL345\nAcceleration, Roll/Pitch,\nMotion + Vibration", VERTEX_STYLE, 1340, 730, 260, 110)
    ground = builder.add_vertex(
        "Common Ground Between Battery, Power Modules, Compute Board, ESP32, Sensors, and Both MX1508 Drivers",
        (
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;"
            "strokeColor=#666666;fontStyle=1;fontSize=14;"
        ),
        390,
        930,
        900,
        80,
    )

    for source, target in [
        (battery, switch),
        (switch, motor_buck),
        (switch, power_module),
        (motor_buck, drivers),
        (drivers, motors),
        (power_module, compute),
        (power_module, esp32),
        (compute, webcam),
        (esp32, sensors),
        (esp32, imu),
    ]:
        builder.add_edge(source, target)

    builder.add_edge(compute, esp32, value="UART3 to UART2")
    builder.add_edge(drivers, ground, style=FEEDBACK_EDGE_STYLE)
    builder.add_edge(compute, ground, style=FEEDBACK_EDGE_STYLE)
    builder.add_edge(esp32, ground, style=FEEDBACK_EDGE_STYLE)
    builder.write(out_path)


def render_figure_3_8(name: str, out_path: Path) -> None:
    builder = DrawioBuilder(name, page_width=1700, page_height=1200)
    coral = builder.add_vertex(
        "Coral Dev Board UART3\nPin 7 TX, Pin 11 RX, Pin 9 GND",
        VERTEX_STYLE,
        650,
        100,
        400,
        100,
    )
    esp32 = builder.add_vertex(
        "ESP32\nSensor, Safety, UART, and Motor Controller",
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;fontSize=15;",
        650,
        430,
        400,
        120,
    )
    left_sensor = builder.add_vertex("Front-Left HC-SR04\nTRIG 5, ECHO 34", VERTEX_STYLE, 100, 130, 320, 90)
    right_sensor = builder.add_vertex("Front-Right HC-SR04\nTRIG 18, ECHO 35", VERTEX_STYLE, 100, 330, 320, 90)
    imu = builder.add_vertex("GY-291 / ADXL345\nSDA 21, SCL 22", VERTEX_STYLE, 100, 530, 320, 90)
    driver1 = builder.add_vertex("MX1508 Driver 1\nFront-Left 25/26\nRear-Left 32/33", VERTEX_STYLE, 1250, 180, 320, 120)
    driver2 = builder.add_vertex("MX1508 Driver 2\nFront-Right 27/14\nRear-Right 19/23", VERTEX_STYLE, 1250, 430, 320, 120)
    safety = builder.add_vertex(
        "Local Safety\nObstacle, Timeout, Unknown Command -> STOP",
        NOTE_STYLE,
        650,
        720,
        400,
        110,
    )
    builder.add_edge(coral, esp32, value="UART3 <-> UART2\nESP32 RX16 / TX17")
    builder.add_edge(left_sensor, esp32, value="level-shift Echo")
    builder.add_edge(right_sensor, esp32, value="level-shift Echo")
    builder.add_edge(imu, esp32, value="I2C")
    builder.add_edge(esp32, driver1, value="PWM/DIR inputs")
    builder.add_edge(esp32, driver2, value="PWM/DIR inputs")
    builder.add_edge(esp32, safety)
    builder.write(out_path)


def render_table(name: str, header: list[str], rows: list[list[str]], out_path: Path) -> None:
    all_rows = [header] + rows
    col_count = len(header)
    max_lengths = []
    for col_idx in range(col_count):
        lengths = [len(row[col_idx]) if col_idx < len(row) else 0 for row in all_rows]
        max_lengths.append(max(12, min(90, max(lengths))))

    total_width = min(3200, max(1000, 180 * col_count + int(sum(max_lengths) * 5.5)))
    available_width = total_width - 80
    weight_sum = sum(max_lengths)
    widths = []
    consumed = 0
    for idx, weight in enumerate(max_lengths):
        if idx == col_count - 1:
            width = available_width - consumed
        else:
            width = int(available_width * weight / weight_sum)
            width = max(140, min(760, width))
            consumed += width
        widths.append(width)

    title_height = estimate_height(name, available_width, font_size=16, minimum=58)
    header_height = max(
        estimate_height(text, widths[idx], font_size=12, minimum=46)
        for idx, text in enumerate(header)
    )
    row_heights = []
    for row in rows:
        row_heights.append(
            max(
                estimate_height(row[idx], widths[idx], font_size=11, minimum=40)
                for idx in range(col_count)
            )
        )

    page_height = max(800, 120 + title_height + header_height + sum(row_heights) + 40)
    builder = DrawioBuilder(name, page_width=max(1169, total_width), page_height=page_height)

    x0 = 40
    y = 40
    builder.add_vertex(name, TABLE_TITLE_STYLE, x0, y, available_width, title_height)
    y += title_height + 18

    x = x0
    for idx, text in enumerate(header):
        builder.add_vertex(text, TABLE_HEADER_STYLE, x, y, widths[idx], header_height)
        x += widths[idx]
    y += header_height

    for row_index, row in enumerate(rows):
        x = x0
        fill = "#ffffff" if row_index % 2 == 0 else "#f8f9fa"
        style = TABLE_BODY_STYLE + f"fillColor={fill};"
        for col_idx, text in enumerate(row):
            builder.add_vertex(text, style, x, y, widths[col_idx], row_heights[row_index])
            x += widths[col_idx]
        y += row_heights[row_index]

    builder.write(out_path)


def extract_items(path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    items: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        figure_match = FIGURE_RE.match(line)
        table_match = TABLE_RE.match(line)
        if figure_match:
            number, title = figure_match.groups()
            cursor = index + 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
            block: list[str] = []
            if cursor < len(lines) and lines[cursor].startswith("```"):
                cursor += 1
                while cursor < len(lines) and not lines[cursor].startswith("```"):
                    block.append(lines[cursor].rstrip())
                    cursor += 1
            items.append(
                {
                    "kind": "figure",
                    "number": number,
                    "title": title,
                    "block": block,
                }
            )
            index = cursor
        elif table_match:
            number, title = table_match.groups()
            cursor = index + 1
            while cursor < len(lines) and not lines[cursor].startswith("|"):
                cursor += 1
            block: list[str] = []
            while cursor < len(lines) and lines[cursor].startswith("|"):
                block.append(lines[cursor].rstrip())
                cursor += 1
            header, rows = parse_markdown_table(block)
            items.append(
                {
                    "kind": "table",
                    "number": number,
                    "title": title,
                    "header": header,
                    "rows": rows,
                }
            )
            index = cursor
        else:
            index += 1
    return items


def clean_drawio_dir(paths_to_keep: Iterable[Path]) -> None:
    keep = {path.resolve() for path in paths_to_keep}
    for existing in OUT_DIR.rglob("*.drawio"):
        if existing.resolve() not in keep:
            existing.unlink()


def main() -> None:
    source_items: list[dict[str, object]] = []
    for source in SOURCE_FILES:
        source_items.extend(extract_items(source))

    generated: list[Path] = []
    for item in source_items:
        number = str(item["number"])
        chapter_folder = f"chapter_{number.split('.')[0]}"
        kind = str(item["kind"])
        title = str(item["title"])
        if kind == "table":
            continue
        output_dir = OUT_DIR / chapter_folder
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{kind}_{number.replace('.', '_')}_{slugify(title)}.drawio"
        output_path = output_dir / filename
        generated.append(output_path)

        figure_name = f"Figure {number}: {title}"
        if number == "2.3":
            render_figure_2_3(figure_name, output_path)
        elif number == "3.1":
            render_figure_3_1(figure_name, output_path)
        elif number == "3.3":
            render_placeholder_figure(
                figure_name,
                output_path,
                "Static finalized component collage is embedded from figures/chapter_3/figure_3_3_main_hardware_components.png.\n\nThis Draw.io placeholder is kept only so the generated asset list remains complete.",
            )
        elif number == "3.4":
            render_placeholder_figure(
                figure_name,
                output_path,
                "The finalized Fusion 360 robot overview is embedded from figures/chapter_3.\n\nThis Draw.io placeholder is kept only so the generated asset list remains complete.",
            )
        elif number == "3.5":
            render_placeholder_figure(
                figure_name,
                output_path,
                "The finalized Fusion 360 multi-view layout is embedded from figures/chapter_3.\n\nThis Draw.io placeholder is kept only so the generated asset list remains complete.",
            )
        elif number == "3.6":
            render_placeholder_figure(
                figure_name,
                output_path,
                "The finalized dimensioned mechanical sketch is embedded from figures/chapter_3.\n\nThis Draw.io placeholder is kept only so the generated asset list remains complete.",
            )
        elif number == "3.7":
            render_figure_3_7(figure_name, output_path)
        elif number == "3.8":
            render_figure_3_8(figure_name, output_path)
        elif number in {"4.1", "4.2"}:
            render_placeholder_figure(
                figure_name,
                output_path,
                "The expected-result safety simulation is embedded from figures/chapter_4.\n\nThis Draw.io placeholder is kept only so the generated asset list remains complete.",
            )
        else:
            steps = [
                line.strip()
                for line in list(item["block"])
                if line.strip() and line.strip() not in {"|", "v"}
            ]
            render_vertical_flow(figure_name, steps, output_path)

    clean_drawio_dir(generated)


if __name__ == "__main__":
    main()
