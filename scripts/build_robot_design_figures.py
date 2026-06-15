from __future__ import annotations

from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIR = ROOT / "cad" / "design_sources"
OUT_DIR = ROOT / "figures" / "chapter_3"

OVERVIEW_SOURCE = PHOTO_DIR / "FYP_2_2026-Jun-10_09-44-41PM-000_CustomizedView7494680794.png"
VIEW_SOURCES = [
    ("Front view", "FYP_2_2026-Jun-10_09-45-14PM-000_CustomizedView45560590010.png"),
    ("Left-side view", "FYP_2_2026-Jun-10_09-46-30PM-000_CustomizedView18189701881.png"),
    ("Rear three-quarter view", "FYP_2_2026-Jun-10_09-47-04PM-000_CustomizedView4164938549.png"),
    ("Top view", "FYP_2_2026-Jun-10_09-50-40PM-000_CustomizedView38847452573.png"),
]
SKETCH_SOURCE = PHOTO_DIR / "Diagram sketch VLM Robot.pdf"

OVERVIEW_OUT = OUT_DIR / "figure_3_4_finalized_fusion_360_robot_model.png"
MULTI_VIEW_OUT = OUT_DIR / "figure_3_5_fusion_360_robot_multi_view.png"
SKETCH_OUT = OUT_DIR / "figure_3_6_mechanical_design_sketch_and_dimensions.png"


def font_path(bold: bool = False) -> Path:
    names = ["arialbd.ttf", "calibrib.ttf"] if bold else ["arial.ttf", "calibri.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return path
    raise FileNotFoundError("A supported Windows font was not found")


TITLE_FONT = ImageFont.truetype(str(font_path(True)), 42)
LABEL_FONT = ImageFont.truetype(str(font_path(True)), 24)


def crop_fraction(image: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    width, height = image.size
    pixels = (
        round(width * box[0]),
        round(height * box[1]),
        round(width * box[2]),
        round(height * box[3]),
    )
    return image.crop(pixels)


def fitted_panel(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image.convert("RGB"), size, Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def build_overview() -> None:
    with Image.open(OVERVIEW_SOURCE) as source:
        cropped = crop_fraction(source, (0.18, 0.20, 0.84, 0.76))
        overview = fitted_panel(cropped, (1800, 1080))
    overview.save(OVERVIEW_OUT, quality=95)


def build_multi_view() -> None:
    canvas = Image.new("RGB", (1800, 1420), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((55, 35), "Finalized Fusion 360 Robot Multi-View Layout", font=TITLE_FONT, fill="#193858")

    panel_width = 830
    panel_height = 560
    positions = [(55, 125), (915, 125), (55, 815), (915, 815)]
    crops = [
        (0.18, 0.20, 0.82, 0.74),
        (0.18, 0.20, 0.84, 0.75),
        (0.16, 0.19, 0.85, 0.77),
        (0.18, 0.12, 0.83, 0.88),
    ]

    for (label, filename), position, crop in zip(VIEW_SOURCES, positions, crops):
        x, y = position
        with Image.open(PHOTO_DIR / filename) as source:
            panel = fitted_panel(crop_fraction(source, crop), (panel_width, panel_height))
        canvas.paste(panel, (x, y))
        draw.rectangle((x, y, x + panel_width, y + panel_height), outline="#8495a8", width=3)
        label_box = (x, y + panel_height, x + panel_width, y + panel_height + 62)
        draw.rectangle(label_box, fill="#eef3f8", outline="#8495a8", width=2)
        text_box = draw.textbbox((0, 0), label, font=LABEL_FONT)
        text_width = text_box[2] - text_box[0]
        draw.text(
            (x + (panel_width - text_width) / 2, y + panel_height + 17),
            label,
            font=LABEL_FONT,
            fill="#263b50",
        )

    canvas.save(MULTI_VIEW_OUT, quality=95)


def build_sketch() -> None:
    document = fitz.open(SKETCH_SOURCE)
    try:
        page = document[0]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        pixmap.save(SKETCH_OUT)
    finally:
        document.close()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_overview()
    build_multi_view()
    build_sketch()
    print(f"Built {OVERVIEW_OUT}")
    print(f"Built {MULTI_VIEW_OUT}")
    print(f"Built {SKETCH_OUT}")


if __name__ == "__main__":
    main()
