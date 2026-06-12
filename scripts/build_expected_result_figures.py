from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "figures" / "chapter_4"

WIDTH = 1800
HEIGHT = 1050
MARGIN_LEFT = 180
MARGIN_RIGHT = 100
MARGIN_TOP = 150
MARGIN_BOTTOM = 160


def font_path(bold: bool = False) -> Path:
    names = ["arialbd.ttf", "calibrib.ttf"] if bold else ["arial.ttf", "calibri.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return path
    raise FileNotFoundError("A supported Windows font was not found")


TITLE = ImageFont.truetype(str(font_path(True)), 42)
LABEL = ImageFont.truetype(str(font_path()), 26)
LABEL_BOLD = ImageFont.truetype(str(font_path(True)), 27)
NOTE = ImageFont.truetype(str(font_path()), 23)


def base_canvas(title: str, x_label: str, y_label: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 40), title, font=TITLE, fill="#193858")
    x0, y0 = MARGIN_LEFT, HEIGHT - MARGIN_BOTTOM
    x1, y1 = WIDTH - MARGIN_RIGHT, MARGIN_TOP
    draw.line((x0, y0, x1, y0), fill="#303030", width=4)
    draw.line((x0, y0, x0, y1), fill="#303030", width=4)
    draw.text((WIDTH // 2 - 150, HEIGHT - 85), x_label, font=LABEL_BOLD, fill="#303030")
    draw.text((35, HEIGHT // 2), y_label, font=LABEL_BOLD, fill="#303030")
    return image, draw


def build_obstacle_response() -> None:
    image, draw = base_canvas(
        "Expected Obstacle-Stop Response at the Planned 25 cm Threshold",
        "Minimum front ultrasonic distance (cm)",
        "Expected response",
    )
    x0, y0 = MARGIN_LEFT, HEIGHT - MARGIN_BOTTOM
    x1, y1 = WIDTH - MARGIN_RIGHT, MARGIN_TOP
    plot_width = x1 - x0
    stop_y = y0 - int((y0 - y1) * 0.25)
    move_y = y0 - int((y0 - y1) * 0.75)

    def sx(distance: float) -> int:
        return x0 + int(plot_width * distance / 60)

    draw.line((x0, stop_y, sx(25), stop_y), fill="#c00000", width=12)
    draw.line((sx(25), stop_y, sx(25), move_y), fill="#6b6b6b", width=5)
    draw.line((sx(25), move_y, x1, move_y), fill="#2e7d32", width=12)
    draw.line((sx(25), y0, sx(25), y1), fill="#d79b00", width=4)

    for distance in range(0, 61, 10):
        x = sx(distance)
        draw.line((x, y0 - 8, x, y0 + 8), fill="#303030", width=3)
        draw.text((x - 14, y0 + 20), str(distance), font=LABEL, fill="#303030")

    draw.text((x0 + 20, stop_y - 55), "STOP", font=LABEL_BOLD, fill="#c00000")
    draw.text((sx(25) + 30, move_y - 55), "MOVEMENT MAY BE PERMITTED", font=LABEL_BOLD, fill="#2e7d32")
    draw.text((sx(25) - 85, y1 - 10), "25 cm planned threshold", font=NOTE, fill="#8a5b00")
    image.save(OUT_DIR / "figure_4_1_expected_obstacle_stop_response.png", quality=95)


def build_timeout_response() -> None:
    image, draw = base_canvas(
        "Expected Motor Response When No New Command Arrives",
        "Elapsed time since last valid command (ms)",
        "Expected motor state",
    )
    x0, y0 = MARGIN_LEFT, HEIGHT - MARGIN_BOTTOM
    x1, y1 = WIDTH - MARGIN_RIGHT, MARGIN_TOP
    plot_width = x1 - x0
    stop_y = y0 - int((y0 - y1) * 0.25)
    active_y = y0 - int((y0 - y1) * 0.75)

    def sx(milliseconds: float) -> int:
        return x0 + int(plot_width * milliseconds / 1600)

    draw.line((x0, active_y, sx(1000), active_y), fill="#2e7d32", width=12)
    draw.line((sx(1000), active_y, sx(1000), stop_y), fill="#6b6b6b", width=5)
    draw.line((sx(1000), stop_y, x1, stop_y), fill="#c00000", width=12)
    draw.line((sx(1000), y0, sx(1000), y1), fill="#d79b00", width=4)

    for milliseconds in range(0, 1601, 200):
        x = sx(milliseconds)
        draw.line((x, y0 - 8, x, y0 + 8), fill="#303030", width=3)
        draw.text((x - 25, y0 + 20), str(milliseconds), font=LABEL, fill="#303030")

    draw.text((x0 + 20, active_y - 55), "COMMANDED MOTION AVAILABLE", font=LABEL_BOLD, fill="#2e7d32")
    draw.text((sx(1000) + 30, stop_y - 55), "STOP", font=LABEL_BOLD, fill="#c00000")
    draw.text((sx(1000) - 100, y1 - 10), "1,000 ms timeout", font=NOTE, fill="#8a5b00")
    image.save(OUT_DIR / "figure_4_2_expected_command_timeout_response.png", quality=95)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_obstacle_response()
    build_timeout_response()
    print(f"Built expected-result figures in {OUT_DIR}")


if __name__ == "__main__":
    main()
