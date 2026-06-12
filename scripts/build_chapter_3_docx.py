from __future__ import annotations

import html
import math
import mimetypes
import re
import shutil
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_PATH = ROOT / "chapter_3_methodology.md"
DRAWIO_DIR = ROOT / "drawio" / "chapter_3"
EXPORT_DIR = DRAWIO_DIR / "exported"
DOCX_PATH = ROOT / "chapter_3_methodology.docx"
STATIC_FIGURE_IMAGES = {
    "figure 3.3: main hardware components for the finalized coral dev board robot": ROOT
    / "figures"
    / "chapter_3"
    / "figure_3_3_main_hardware_components.png",
    "figure 3.4: finalized fusion 360 physical robot model": ROOT
    / "figures"
    / "chapter_3"
    / "figure_3_4_finalized_fusion_360_robot_model.png",
    "figure 3.5: finalized fusion 360 robot multi-view layout": ROOT
    / "figures"
    / "chapter_3"
    / "figure_3_5_fusion_360_robot_multi_view.png",
    "figure 3.6: finalized mechanical design sketch and dimensions": ROOT
    / "figures"
    / "chapter_3"
    / "figure_3_6_mechanical_design_sketch_and_dimensions.png",
    "figure 4.1: expected obstacle-stop response at the planned 25 cm threshold": ROOT
    / "figures"
    / "chapter_4"
    / "figure_4_1_expected_obstacle_stop_response.png",
    "figure 4.2: expected motor response when the command timeout exceeds 1,000 ms": ROOT
    / "figures"
    / "chapter_4"
    / "figure_4_2_expected_command_timeout_response.png",
}

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

NS = {
    "w": W_NS,
    "r": R_NS,
    "wp": WP_NS,
    "a": A_NS,
    "pic": PIC_NS,
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def qn(prefix: str, tag: str) -> str:
    return f"{{{NS[prefix]}}}{tag}"


def attr(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", cleaned).strip("_")


def parse_style(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in style.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            result[key] = value
        elif part:
            result[part] = "1"
    return result


def parse_color(value: str | None, default: str) -> tuple[int, int, int]:
    value = value or default
    if value == "none":
        value = default
    value = value.lstrip("#")
    if len(value) != 6:
        value = default.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def clean_drawio_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("`", "")
    return value.strip()


def font_path(name: str) -> Path:
    candidates = {
        "regular": [Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/calibri.ttf")],
        "bold": [Path("C:/Windows/Fonts/arialbd.ttf"), Path("C:/Windows/Fonts/calibrib.ttf")],
        "mono": [Path("C:/Windows/Fonts/consola.ttf"), Path("C:/Windows/Fonts/cour.ttf")],
    }
    for candidate in candidates[name]:
        if candidate.exists():
            return candidate
    return candidates["regular"][0]


def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        path = font_path("mono")
    else:
        path = font_path("bold" if bold else "regular")
    return ImageFont.truetype(str(path), size)


@dataclass
class Vertex:
    cell_id: str
    value: str
    style: dict[str, str]
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def cx(self) -> float:
        return self.x + self.width / 2

    @property
    def cy(self) -> float:
        return self.y + self.height / 2


@dataclass
class Edge:
    source: str
    target: str
    value: str
    style: dict[str, str]


def wrap_text_to_width(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.ImageDraw,
) -> list[str]:
    wrapped: list[str] = []
    for raw_line in text.splitlines() or [""]:
        words = raw_line.split()
        if not words:
            wrapped.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                current = trial
            else:
                wrapped.append(current)
                current = word
        wrapped.append(current)
    return wrapped


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    align: str = "center",
    valign: str = "middle",
    padding: int = 10,
) -> None:
    x1, y1, x2, y2 = box
    max_width = max(10, x2 - x1 - padding * 2)
    lines = wrap_text_to_width(text, font, max_width, draw)
    line_heights = [
        max(1, draw.textbbox((0, 0), line or "Ag", font=font)[3] - draw.textbbox((0, 0), line or "Ag", font=font)[1])
        for line in lines
    ]
    line_gap = max(3, int(font.size * 0.25))
    total_height = sum(line_heights) + line_gap * max(0, len(lines) - 1)
    if valign == "top":
        y = y1 + padding
    else:
        y = y1 + max(padding, (y2 - y1 - total_height) // 2)
    for line, line_height in zip(lines, line_heights):
        width = draw.textbbox((0, 0), line, font=font)[2]
        if align == "left":
            x = x1 + padding
        elif align == "right":
            x = x2 - padding - width
        else:
            x = x1 + (x2 - x1 - width) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height + line_gap


def scaled_point(point: tuple[float, float], scale: int, offset: tuple[float, float]) -> tuple[int, int]:
    return (round((point[0] - offset[0]) * scale), round((point[1] - offset[1]) * scale))


def draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    fill: tuple[int, int, int],
    width: int,
    dash_length: int = 14,
    gap_length: int = 10,
) -> None:
    for start, end in zip(points, points[1:]):
        x1, y1 = start
        x2, y2 = end
        distance = math.hypot(x2 - x1, y2 - y1)
        if distance == 0:
            continue
        dx = (x2 - x1) / distance
        dy = (y2 - y1) / distance
        travelled = 0.0
        while travelled < distance:
            dash_end = min(distance, travelled + dash_length)
            p1 = (round(x1 + dx * travelled), round(y1 + dy * travelled))
            p2 = (round(x1 + dx * dash_end), round(y1 + dy * dash_end))
            draw.line([p1, p2], fill=fill, width=width)
            travelled += dash_length + gap_length


def draw_arrow_head(
    draw: ImageDraw.ImageDraw,
    previous: tuple[int, int],
    end: tuple[int, int],
    fill: tuple[int, int, int],
    size: int,
) -> None:
    px, py = previous
    ex, ey = end
    angle = math.atan2(ey - py, ex - px)
    left = (ex - size * math.cos(angle - math.pi / 6), ey - size * math.sin(angle - math.pi / 6))
    right = (ex - size * math.cos(angle + math.pi / 6), ey - size * math.sin(angle + math.pi / 6))
    draw.polygon([(ex, ey), left, right], fill=fill)


def polyline_label_anchor(points: list[tuple[int, int]], text_width: int, text_height: int, scale: int) -> tuple[int, int]:
    if len(points) < 2:
        return points[0] if points else (0, 0)
    lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]
    total = sum(lengths)
    target = total / 2
    travelled = 0.0
    for (a, b), length in zip(zip(points, points[1:]), lengths):
        if travelled + length >= target and length:
            ratio = (target - travelled) / length
            x = round(a[0] + (b[0] - a[0]) * ratio)
            y = round(a[1] + (b[1] - a[1]) * ratio)
            is_vertical = abs(b[1] - a[1]) >= abs(b[0] - a[0])
            if is_vertical:
                return x + 10 * scale, y - text_height // 2
            return x - text_width // 2, y - text_height - 8 * scale
        travelled += length
    end = points[-1]
    return end[0] + 10 * scale, end[1] - text_height // 2


def connection_points(source: Vertex, target: Vertex) -> tuple[tuple[float, float], tuple[float, float]]:
    dx = target.cx - source.cx
    dy = target.cy - source.cy
    if abs(dx) > abs(dy):
        if dx > 0:
            return (source.right, source.cy), (target.left, target.cy)
        return (source.left, source.cy), (target.right, target.cy)
    if dy > 0:
        return (source.cx, source.bottom), (target.cx, target.top)
    return (source.cx, source.top), (target.cx, target.bottom)


def route_edge(start: tuple[float, float], end: tuple[float, float]) -> list[tuple[float, float]]:
    sx, sy = start
    ex, ey = end
    if abs(sx - ex) < 4 or abs(sy - ey) < 4:
        return [start, end]
    if abs(ey - sy) >= abs(ex - sx):
        mid_y = sy + (ey - sy) / 2
        return [start, (sx, mid_y), (ex, mid_y), end]
    mid_x = sx + (ex - sx) / 2
    return [start, (mid_x, sy), (mid_x, ey), end]


def render_drawio(path: Path, out_path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    diagram = root.find("diagram")
    name = diagram.attrib.get("name", path.stem) if diagram is not None else path.stem
    model = root.find(".//mxGraphModel")
    if model is None:
        raise ValueError(f"No mxGraphModel found in {path}")

    vertices: dict[str, Vertex] = {}
    edges: list[Edge] = []
    is_table = path.name.startswith("table_")

    for cell in model.findall(".//mxCell"):
        geom = cell.find("mxGeometry")
        if cell.attrib.get("vertex") == "1" and geom is not None:
            value = clean_drawio_text(cell.attrib.get("value", ""))
            if is_table and value == name:
                continue
            vertices[cell.attrib["id"]] = Vertex(
                cell_id=cell.attrib["id"],
                value=value,
                style=parse_style(cell.attrib.get("style", "")),
                x=float(geom.attrib.get("x", 0)),
                y=float(geom.attrib.get("y", 0)),
                width=float(geom.attrib.get("width", 0)),
                height=float(geom.attrib.get("height", 0)),
            )
        elif cell.attrib.get("edge") == "1":
            edges.append(
                Edge(
                    source=cell.attrib.get("source", ""),
                    target=cell.attrib.get("target", ""),
                    value=clean_drawio_text(cell.attrib.get("value", "")),
                    style=parse_style(cell.attrib.get("style", "")),
                )
            )

    if not vertices:
        raise ValueError(f"No vertices found in {path}")

    margin = 36
    min_x = min(v.left for v in vertices.values()) - margin
    min_y = min(v.top for v in vertices.values()) - margin
    max_x = max(v.right for v in vertices.values()) + margin
    max_y = max(v.bottom for v in vertices.values()) + margin
    offset = (min_x, min_y)
    scale = 2

    image = Image.new("RGB", (round((max_x - min_x) * scale), round((max_y - min_y) * scale)), "white")
    draw = ImageDraw.Draw(image)

    for edge in edges:
        if edge.source not in vertices or edge.target not in vertices:
            continue
        source = vertices[edge.source]
        target = vertices[edge.target]
        start, end = connection_points(source, target)
        points = [scaled_point(point, scale, offset) for point in route_edge(start, end)]
        stroke = parse_color(edge.style.get("strokeColor"), "#333333")
        width = max(2, int(float(edge.style.get("strokeWidth", "2")) * scale))
        if edge.style.get("dashed") == "1":
            draw_dashed_line(draw, points, fill=stroke, width=width)
        else:
            draw.line(points, fill=stroke, width=width, joint="curve")
        if len(points) >= 2:
            draw_arrow_head(draw, points[-2], points[-1], stroke, size=10 * scale)
        if edge.value:
            label_font = get_font(12 * scale)
            bbox = draw.textbbox((0, 0), edge.value, font=label_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            label_x, label_y = polyline_label_anchor(points, text_width, text_height, scale)
            pad = 4 * scale
            label_box = (label_x - pad, label_y - pad, label_x + text_width + pad, label_y + text_height + pad)
            draw.rectangle(label_box, fill="white")
            draw.text((label_x, label_y), edge.value, font=label_font, fill=stroke)

    for vertex in sorted(vertices.values(), key=lambda item: (item.y, item.x)):
        style = vertex.style
        x1, y1 = scaled_point((vertex.x, vertex.y), scale, offset)
        x2, y2 = scaled_point((vertex.right, vertex.bottom), scale, offset)
        fill = parse_color(style.get("fillColor"), "#ffffff")
        stroke = parse_color(style.get("strokeColor"), "#666666")
        width = max(1, int(scale))
        if "rhombus" in style:
            polygon = [
                ((x1 + x2) // 2, y1),
                (x2, (y1 + y2) // 2),
                ((x1 + x2) // 2, y2),
                (x1, (y1 + y2) // 2),
            ]
            draw.polygon(polygon, fill=fill, outline=stroke)
        elif style.get("rounded") == "1":
            draw.rounded_rectangle((x1, y1, x2, y2), radius=12 * scale, fill=fill, outline=stroke, width=width)
        else:
            draw.rectangle((x1, y1, x2, y2), fill=fill, outline=stroke, width=width)

        font_size = int(float(style.get("fontSize", "11"))) * scale
        bold = style.get("fontStyle") == "1"
        font = get_font(font_size, bold=bold)
        align = style.get("align", "center" if ("rhombus" in style or style.get("rounded") == "1") else "left")
        draw_wrapped_text(
            draw,
            (x1, y1, x2, y2),
            vertex.value,
            font,
            fill=(30, 30, 30),
            align=align,
            padding=max(8, int(float(style.get("spacing", "8")) * scale)),
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, quality=95)


def render_all_drawio() -> dict[str, Path]:
    if EXPORT_DIR.exists():
        shutil.rmtree(EXPORT_DIR)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    caption_to_image: dict[str, Path] = {}
    for drawio in sorted(DRAWIO_DIR.glob("*.drawio")):
        tree = ET.parse(drawio)
        diagram = tree.getroot().find("diagram")
        caption = diagram.attrib.get("name", drawio.stem) if diagram is not None else drawio.stem
        out_path = EXPORT_DIR / f"{drawio.stem}.png"
        caption_key = caption.lower()
        static_path = STATIC_FIGURE_IMAGES.get(caption_key)
        if static_path and static_path.exists():
            shutil.copy2(static_path, out_path)
        else:
            render_drawio(drawio, out_path)
        caption_to_image[caption_key] = out_path
    markdown_text = MARKDOWN_PATH.read_text(encoding="utf-8").lower()
    for caption, image_path in STATIC_FIGURE_IMAGES.items():
        if image_path.exists() and caption in markdown_text and caption not in caption_to_image:
            caption_to_image[caption] = image_path
    return caption_to_image


class DocxBuilder:
    def __init__(self, page_number_start: int = 1) -> None:
        self.relationships: list[tuple[str, str, str]] = []
        self.media: list[tuple[Path, str]] = []
        self.image_counter = 1
        self.elements: list[ET.Element] = []
        self.page_number_start = page_number_start
        self.footer_rel_id = self.add_relationship(
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer",
            "footer1.xml",
        )

    def add_relationship(self, rel_type: str, target: str) -> str:
        rel_id = f"rId{len(self.relationships) + 1}"
        self.relationships.append((rel_id, rel_type, target))
        return rel_id

    def add_text_paragraph(
        self,
        text: str,
        style: str | None = None,
        *,
        alignment: str | None = None,
        bold: bool = False,
        italic: bool = False,
        mono: bool = False,
        keep_backticks: bool = False,
        spacing_after: int = 160,
        indent_left: int | None = None,
    ) -> None:
        paragraph = ET.Element(qn("w", "p"))
        ppr = ET.SubElement(paragraph, qn("w", "pPr"))
        if style:
            ET.SubElement(ppr, qn("w", "pStyle"), {attr("w", "val"): style})
        if alignment:
            ET.SubElement(ppr, qn("w", "jc"), {attr("w", "val"): alignment})
        if indent_left is not None:
            ET.SubElement(ppr, qn("w", "ind"), {attr("w", "left"): str(indent_left)})
        ET.SubElement(ppr, qn("w", "spacing"), {attr("w", "after"): str(spacing_after), attr("w", "line"): "360", attr("w", "lineRule"): "auto"})

        parts = [text] if keep_backticks else split_inline_code(text)
        if isinstance(parts[0], tuple):
            for chunk, is_code in parts:  # type: ignore[misc]
                self._add_run(paragraph, chunk, bold=bold, italic=italic, mono=mono or is_code)
        else:
            self._add_run(paragraph, text, bold=bold, italic=italic, mono=mono)
        self.elements.append(paragraph)

    def _add_run(self, paragraph: ET.Element, text: str, *, bold: bool = False, italic: bool = False, mono: bool = False) -> None:
        run = ET.SubElement(paragraph, qn("w", "r"))
        rpr = ET.SubElement(run, qn("w", "rPr"))
        if bold:
            ET.SubElement(rpr, qn("w", "b"))
        if italic:
            ET.SubElement(rpr, qn("w", "i"))
        if mono:
            ET.SubElement(rpr, qn("w", "rFonts"), {attr("w", "ascii"): "Courier New", attr("w", "hAnsi"): "Courier New"})
        for index, line in enumerate(text.split("\n")):
            if index:
                ET.SubElement(run, qn("w", "br"))
            t = ET.SubElement(run, qn("w", "t"))
            if line.startswith(" ") or line.endswith(" "):
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            t.text = line

    def add_code_block(self, text: str) -> None:
        paragraph = ET.Element(qn("w", "p"))
        ppr = ET.SubElement(paragraph, qn("w", "pPr"))
        ET.SubElement(ppr, qn("w", "pStyle"), {attr("w", "val"): "CodeBlock"})
        ET.SubElement(ppr, qn("w", "spacing"), {attr("w", "before"): "80", attr("w", "after"): "160"})
        ET.SubElement(ppr, qn("w", "shd"), {attr("w", "val"): "clear", attr("w", "color"): "auto", attr("w", "fill"): "F7F7F7"})
        borders = ET.SubElement(ppr, qn("w", "pBdr"))
        for side in ("top", "left", "bottom", "right"):
            ET.SubElement(borders, qn("w", side), {attr("w", "val"): "single", attr("w", "sz"): "4", attr("w", "space"): "4", attr("w", "color"): "D9D9D9"})
        run = ET.SubElement(paragraph, qn("w", "r"))
        rpr = ET.SubElement(run, qn("w", "rPr"))
        ET.SubElement(rpr, qn("w", "rFonts"), {attr("w", "ascii"): "Courier New", attr("w", "hAnsi"): "Courier New"})
        ET.SubElement(rpr, qn("w", "sz"), {attr("w", "val"): "19"})
        for index, line in enumerate(text.rstrip("\n").split("\n")):
            if index:
                ET.SubElement(run, qn("w", "br"))
            t = ET.SubElement(run, qn("w", "t"))
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            t.text = line
        self.elements.append(paragraph)

    def add_page_break(self) -> None:
        paragraph = ET.Element(qn("w", "p"))
        run = ET.SubElement(paragraph, qn("w", "r"))
        ET.SubElement(run, qn("w", "br"), {attr("w", "type"): "page"})
        self.elements.append(paragraph)

    def add_image(self, image_path: Path, max_width_inches: float = 6.27) -> None:
        media_name = f"image{self.image_counter}{image_path.suffix.lower()}"
        self.image_counter += 1
        target = f"media/{media_name}"
        rel_id = self.add_relationship(
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
            target,
        )
        self.media.append((image_path, media_name))

        with Image.open(image_path) as img:
            width_px, height_px = img.size
        aspect = height_px / width_px
        width_inches = max_width_inches
        height_inches = width_inches * aspect
        if height_inches > 8.9:
            height_inches = 8.9
            width_inches = height_inches / aspect
        cx = int(width_inches * 914400)
        cy = int(height_inches * 914400)

        paragraph = ET.Element(qn("w", "p"))
        ppr = ET.SubElement(paragraph, qn("w", "pPr"))
        ET.SubElement(ppr, qn("w", "jc"), {attr("w", "val"): "center"})
        ET.SubElement(ppr, qn("w", "spacing"), {attr("w", "after"): "220"})
        run = ET.SubElement(paragraph, qn("w", "r"))
        drawing = ET.SubElement(run, qn("w", "drawing"))
        inline = ET.SubElement(
            drawing,
            qn("wp", "inline"),
            {"distT": "0", "distB": "0", "distL": "0", "distR": "0"},
        )
        ET.SubElement(inline, qn("wp", "extent"), {"cx": str(cx), "cy": str(cy)})
        ET.SubElement(inline, qn("wp", "effectExtent"), {"l": "0", "t": "0", "r": "0", "b": "0"})
        ET.SubElement(inline, qn("wp", "docPr"), {"id": str(self.image_counter + 100), "name": image_path.stem})
        ET.SubElement(inline, qn("wp", "cNvGraphicFramePr"))
        graphic = ET.SubElement(inline, qn("a", "graphic"))
        graphic_data = ET.SubElement(
            graphic,
            qn("a", "graphicData"),
            {"uri": "http://schemas.openxmlformats.org/drawingml/2006/picture"},
        )
        pic = ET.SubElement(graphic_data, qn("pic", "pic"))
        nv_pic_pr = ET.SubElement(pic, qn("pic", "nvPicPr"))
        ET.SubElement(nv_pic_pr, qn("pic", "cNvPr"), {"id": "0", "name": media_name})
        ET.SubElement(nv_pic_pr, qn("pic", "cNvPicPr"))
        blip_fill = ET.SubElement(pic, qn("pic", "blipFill"))
        ET.SubElement(blip_fill, qn("a", "blip"), {attr("r", "embed"): rel_id})
        stretch = ET.SubElement(blip_fill, qn("a", "stretch"))
        ET.SubElement(stretch, qn("a", "fillRect"))
        sp_pr = ET.SubElement(pic, qn("pic", "spPr"))
        xfrm = ET.SubElement(sp_pr, qn("a", "xfrm"))
        ET.SubElement(xfrm, qn("a", "off"), {"x": "0", "y": "0"})
        ET.SubElement(xfrm, qn("a", "ext"), {"cx": str(cx), "cy": str(cy)})
        prst_geom = ET.SubElement(sp_pr, qn("a", "prstGeom"), {"prst": "rect"})
        ET.SubElement(prst_geom, qn("a", "avLst"))
        self.elements.append(paragraph)

    def build_document_xml(self) -> bytes:
        document = ET.Element(qn("w", "document"))
        body = ET.SubElement(document, qn("w", "body"))
        for element in self.elements:
            body.append(element)
        sect_pr = ET.SubElement(body, qn("w", "sectPr"))
        ET.SubElement(
            sect_pr,
            qn("w", "footerReference"),
            {attr("w", "type"): "default", attr("r", "id"): self.footer_rel_id},
        )
        ET.SubElement(sect_pr, qn("w", "pgNumType"), {attr("w", "start"): str(self.page_number_start)})
        ET.SubElement(sect_pr, qn("w", "pgSz"), {attr("w", "w"): "11906", attr("w", "h"): "16838"})
        ET.SubElement(
            sect_pr,
            qn("w", "pgMar"),
            {
                attr("w", "top"): "1440",
                attr("w", "right"): "1440",
                attr("w", "bottom"): "1440",
                attr("w", "left"): "1440",
                attr("w", "header"): "720",
                attr("w", "footer"): "720",
                attr("w", "gutter"): "0",
            },
        )
        return xml_bytes(document)

    def write(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as docx:
            docx.writestr("[Content_Types].xml", content_types_xml(self.media))
            docx.writestr("_rels/.rels", root_relationships_xml())
            docx.writestr("word/document.xml", self.build_document_xml())
            docx.writestr("word/styles.xml", styles_xml())
            docx.writestr("word/settings.xml", settings_xml())
            docx.writestr("word/footer1.xml", footer_xml())
            docx.writestr("word/_rels/document.xml.rels", document_relationships_xml(self.relationships))
            for image_path, media_name in self.media:
                docx.write(image_path, f"word/media/{media_name}")


def split_inline_code(text: str) -> list[tuple[str, bool]]:
    parts: list[tuple[str, bool]] = []
    chunks = text.split("`")
    for index, chunk in enumerate(chunks):
        if chunk:
            parts.append((chunk, index % 2 == 1))
    return parts or [("", False)]


def strip_markdown_emphasis(text: str) -> str:
    text = text.strip()
    if text.startswith("**") and text.endswith("**"):
        text = text[2:-2]
    return text


CAPTION_RE = re.compile(r"^\*\*((?:Figure|Table)\s+\d+\.\d+:\s+.+?)\*\*$")


def append_markdown(
    builder: DocxBuilder,
    markdown_path: Path,
    caption_to_image: dict[str, Path],
    *,
    start_heading: str | None = None,
    stop_heading: str | None = None,
) -> set[Path]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    if start_heading and start_heading in lines:
        lines = lines[lines.index(start_heading) :]
    if stop_heading and stop_heading in lines:
        lines = lines[: lines.index(stop_heading)]
    used_images: set[Path] = set()
    i = 0
    pending_skip: str | None = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if pending_skip and stripped == "":
            i += 1
            continue
        if pending_skip == "table" and stripped.startswith("|"):
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
            pending_skip = None
            continue
        if pending_skip == "figure" and stripped.startswith("```"):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                i += 1
            if i < len(lines):
                i += 1
            pending_skip = None
            continue
        if pending_skip == "figure" and stripped.startswith("!["):
            i += 1
            pending_skip = None
            continue
        pending_skip = None

        if stripped == "":
            i += 1
            continue

        caption_match = CAPTION_RE.match(stripped)
        if caption_match:
            caption = caption_match.group(1)
            builder.add_text_paragraph(caption, style="Caption", alignment="center", bold=True, spacing_after=120)
            image_path = caption_to_image.get(caption.lower())
            if image_path:
                builder.add_image(image_path)
                used_images.add(image_path)
            pending_skip = "table" if caption.startswith("Table") else "figure"
            i += 1
            continue

        if stripped.startswith("```"):
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            builder.add_code_block("\n".join(code_lines))
            continue

        if stripped.startswith("# "):
            text = stripped[2:].strip()
            style = "ChapterTitle" if text.startswith("CHAPTER") else "ChapterSubtitle"
            builder.add_text_paragraph(text, style=style, alignment="center", bold=True, spacing_after=220)
            i += 1
            continue

        if stripped.startswith("## "):
            builder.add_text_paragraph(stripped[3:].strip(), style="Heading1", bold=True, spacing_after=180)
            i += 1
            continue

        if stripped.startswith("### "):
            builder.add_text_paragraph(stripped[4:].strip(), style="Heading2", bold=True, spacing_after=160)
            i += 1
            continue

        if stripped.startswith("- ") or re.match(r"^\d+\.\s+", stripped):
            item_lines = [stripped]
            i += 1
            while i < len(lines):
                continuation = lines[i].strip()
                if (
                    not continuation
                    or continuation.startswith(("#", "- ", "|", "```", "!["))
                    or CAPTION_RE.match(continuation)
                    or re.match(r"^\d+\.\s+", continuation)
                ):
                    break
                item_lines.append(continuation)
                i += 1
            builder.add_text_paragraph(
                " ".join(item_lines),
                style="Normal",
                indent_left=360,
                spacing_after=80,
            )
            continue

        if stripped.startswith("|"):
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
            continue

        paragraph_lines = [strip_markdown_emphasis(stripped)]
        i += 1
        while i < len(lines):
            continuation = lines[i].strip()
            if (
                not continuation
                or continuation.startswith(("#", "- ", "|", "```", "!["))
                or CAPTION_RE.match(continuation)
                or re.match(r"^\d+\.\s+", continuation)
            ):
                break
            paragraph_lines.append(strip_markdown_emphasis(continuation))
            i += 1
        builder.add_text_paragraph(" ".join(paragraph_lines), style="Normal")

    return used_images


def build_docx(caption_to_image: dict[str, Path], page_number_start: int = 1) -> int:
    builder = DocxBuilder(page_number_start=page_number_start)
    used_images = append_markdown(builder, MARKDOWN_PATH, caption_to_image)
    unused = [path for path in caption_to_image.values() if path not in used_images]
    if unused:
        builder.add_text_paragraph("Additional Draw.io Assets", style="Heading1", bold=True)
        for image_path in unused:
            caption = image_path.stem.replace("_", " ").title()
            builder.add_text_paragraph(caption, style="Caption", alignment="center", bold=True, spacing_after=120)
            builder.add_image(image_path)

    builder.write(DOCX_PATH)
    return len(used_images) + len(unused)


def xml_bytes(element: ET.Element) -> bytes:
    ET.indent(element, space="  ")
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def content_types_xml(media: list[tuple[Path, str]]) -> bytes:
    root = ET.Element(f"{{{CT_NS}}}Types")
    ET.SubElement(root, f"{{{CT_NS}}}Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    ET.SubElement(root, f"{{{CT_NS}}}Default", {"Extension": "xml", "ContentType": "application/xml"})
    for ext in sorted({media_name.rsplit(".", 1)[-1].lower() for _, media_name in media}):
        mime = mimetypes.types_map.get(f".{ext}", "image/png")
        ET.SubElement(root, f"{{{CT_NS}}}Default", {"Extension": ext, "ContentType": mime})
    ET.SubElement(
        root,
        f"{{{CT_NS}}}Override",
        {"PartName": "/word/document.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"},
    )
    ET.SubElement(root, f"{{{CT_NS}}}Override", {"PartName": "/word/styles.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"})
    ET.SubElement(root, f"{{{CT_NS}}}Override", {"PartName": "/word/settings.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"})
    ET.SubElement(root, f"{{{CT_NS}}}Override", {"PartName": "/word/footer1.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"})
    return xml_bytes(root)


def root_relationships_xml() -> bytes:
    root = ET.Element(f"{{{REL_NS}}}Relationships")
    ET.SubElement(
        root,
        f"{{{REL_NS}}}Relationship",
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "Target": "word/document.xml",
        },
    )
    return xml_bytes(root)


def document_relationships_xml(relationships: list[tuple[str, str, str]]) -> bytes:
    root = ET.Element(f"{{{REL_NS}}}Relationships")
    ET.SubElement(
        root,
        f"{{{REL_NS}}}Relationship",
        {
            "Id": "rIdStyles",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
            "Target": "styles.xml",
        },
    )
    ET.SubElement(
        root,
        f"{{{REL_NS}}}Relationship",
        {
            "Id": "rIdSettings",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings",
            "Target": "settings.xml",
        },
    )
    for rel_id, rel_type, target in relationships:
        ET.SubElement(root, f"{{{REL_NS}}}Relationship", {"Id": rel_id, "Type": rel_type, "Target": target})
    return xml_bytes(root)


def footer_xml() -> bytes:
    footer = ET.Element(qn("w", "ftr"))
    paragraph = ET.SubElement(footer, qn("w", "p"))
    ppr = ET.SubElement(paragraph, qn("w", "pPr"))
    ET.SubElement(ppr, qn("w", "jc"), {attr("w", "val"): "center"})

    begin_run = ET.SubElement(paragraph, qn("w", "r"))
    ET.SubElement(begin_run, qn("w", "fldChar"), {attr("w", "fldCharType"): "begin"})

    instruction_run = ET.SubElement(paragraph, qn("w", "r"))
    instruction = ET.SubElement(instruction_run, qn("w", "instrText"))
    instruction.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instruction.text = " PAGE "

    separate_run = ET.SubElement(paragraph, qn("w", "r"))
    ET.SubElement(separate_run, qn("w", "fldChar"), {attr("w", "fldCharType"): "separate"})
    number_run = ET.SubElement(paragraph, qn("w", "r"))
    ET.SubElement(number_run, qn("w", "t")).text = "1"
    end_run = ET.SubElement(paragraph, qn("w", "r"))
    ET.SubElement(end_run, qn("w", "fldChar"), {attr("w", "fldCharType"): "end"})
    return xml_bytes(footer)


def styles_xml() -> bytes:
    styles = ET.Element(qn("w", "styles"))

    def style(style_id: str, name: str, type_: str = "paragraph", based_on: str | None = None) -> ET.Element:
        element = ET.SubElement(styles, qn("w", "style"), {attr("w", "type"): type_, attr("w", "styleId"): style_id})
        ET.SubElement(element, qn("w", "name"), {attr("w", "val"): name})
        if based_on:
            ET.SubElement(element, qn("w", "basedOn"), {attr("w", "val"): based_on})
        return element

    normal = style("Normal", "Normal")
    ppr = ET.SubElement(normal, qn("w", "pPr"))
    ET.SubElement(ppr, qn("w", "spacing"), {attr("w", "after"): "160", attr("w", "line"): "360", attr("w", "lineRule"): "auto"})
    rpr = ET.SubElement(normal, qn("w", "rPr"))
    ET.SubElement(rpr, qn("w", "rFonts"), {attr("w", "ascii"): "Times New Roman", attr("w", "hAnsi"): "Times New Roman"})
    ET.SubElement(rpr, qn("w", "sz"), {attr("w", "val"): "24"})

    for style_id, name, size in [
        ("ChapterTitle", "Chapter Title", "32"),
        ("ChapterSubtitle", "Chapter Subtitle", "30"),
        ("Heading1", "Heading 1", "28"),
        ("Heading2", "Heading 2", "26"),
    ]:
        element = style(style_id, name, based_on="Normal")
        ppr = ET.SubElement(element, qn("w", "pPr"))
        ET.SubElement(ppr, qn("w", "keepNext"))
        ET.SubElement(ppr, qn("w", "spacing"), {attr("w", "before"): "180", attr("w", "after"): "160"})
        rpr = ET.SubElement(element, qn("w", "rPr"))
        ET.SubElement(rpr, qn("w", "b"))
        ET.SubElement(rpr, qn("w", "rFonts"), {attr("w", "ascii"): "Times New Roman", attr("w", "hAnsi"): "Times New Roman"})
        ET.SubElement(rpr, qn("w", "sz"), {attr("w", "val"): size})

    caption = style("Caption", "Caption", based_on="Normal")
    ppr = ET.SubElement(caption, qn("w", "pPr"))
    ET.SubElement(ppr, qn("w", "spacing"), {attr("w", "before"): "80", attr("w", "after"): "120"})
    rpr = ET.SubElement(caption, qn("w", "rPr"))
    ET.SubElement(rpr, qn("w", "b"))
    ET.SubElement(rpr, qn("w", "sz"), {attr("w", "val"): "22"})

    code = style("CodeBlock", "Code Block", based_on="Normal")
    rpr = ET.SubElement(code, qn("w", "rPr"))
    ET.SubElement(rpr, qn("w", "rFonts"), {attr("w", "ascii"): "Courier New", attr("w", "hAnsi"): "Courier New"})
    ET.SubElement(rpr, qn("w", "sz"), {attr("w", "val"): "19"})

    return xml_bytes(styles)


def settings_xml() -> bytes:
    settings = ET.Element(qn("w", "settings"))
    ET.SubElement(settings, qn("w", "zoom"), {attr("w", "percent"): "100"})
    return xml_bytes(settings)


def main() -> None:
    caption_to_image = render_all_drawio()
    embedded_count = build_docx(caption_to_image)
    print(f"Rendered {len(caption_to_image)} drawio files to {EXPORT_DIR}")
    print(f"Embedded {embedded_count} images in {DOCX_PATH}")


if __name__ == "__main__":
    main()
