from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUT = ROOT / "figures" / "chapter_3" / "figure_3_3_main_hardware_components.png"

WIDTH = 1800
HEIGHT = 1320
CARD_WIDTH = 400
CARD_HEIGHT = 320
IMAGE_HEIGHT = 205
MARGIN_X = 50
GAP_X = 32
START_Y = 170
GAP_Y = 30


def font_path(bold: bool = False) -> Path:
    names = ["arialbd.ttf", "calibrib.ttf"] if bold else ["arial.ttf", "calibri.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return path
    raise FileNotFoundError("A supported Windows font was not found")


TITLE_FONT = ImageFont.truetype(str(font_path(True)), 42)
SUBTITLE_FONT = ImageFont.truetype(str(font_path()), 19)
LABEL_FONT = ImageFont.truetype(str(font_path(True)), 23)
SMALL_FONT = ImageFont.truetype(str(font_path()), 17)


COMPONENTS: list[tuple[str, str | None, str | None]] = [
    ("Raspberry Pi 4", None, "Only onboard high-level compute"),
    ("ESP32 Controller", "esp32.png", "Sensor, safety, USB serial, and motor control"),
    ("USB Webcam", "webcam_camera.png", "Front RGB input"),
    ("2 x HC-SR04", "hc-sr04_ultrasonic_sensor.png", "Front-left and front-right"),
    ("GY-291 / ADXL345", None, "Acceleration, roll/pitch, motion, vibration"),
    ("2 x MX1508 Drivers", "mx1508_motor_driver.png", "Four motor channels"),
    ("4 x Gear Motors + Wheels", "dc_gear_motor_with_wheel.png", "Four-wheel movement"),
    ("3S 18650 Battery Pack", "18650_battery.png", "Three matched cells in series"),
    ("Adjustable Motor Buck", "5v_usb_buck_converter.png", "Regulated motor-driver rail"),
    ("3S-Compatible Power Module", "powerbank_battery.jpg", "Raspberry Pi supply; ESP32 via Pi USB"),
    ("Main Switch + Fuse", None, "Manual isolation and protection"),
]


def rounded_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=18, fill="#f7f9fc", outline="#9aadc2", width=2)


def contain(image: Image.Image, width: int, height: int) -> Image.Image:
    copy = image.convert("RGBA")
    copy.thumbnail((width, height), Image.Resampling.LANCZOS)
    return copy


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    x1, y1, x2, y2 = box
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center", spacing=4)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.multiline_text(
        (x1 + (x2 - x1 - width) / 2, y1 + (y2 - y1 - height) / 2),
        text,
        font=font,
        fill=fill,
        align="center",
        spacing=4,
    )


def build() -> None:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    draw.text((50, 35), "Main Hardware Components for the Finalized Raspberry Pi Robot", font=TITLE_FONT, fill="#193858")
    draw.text(
        (50, 95),
        "The Raspberry Pi 4 is the only high-level physical compute platform.",
        font=SUBTITLE_FONT,
        fill="#555555",
    )
    draw.text(
        (50, 122),
        "The power module must explicitly support a protected 3S lithium-ion pack.",
        font=SUBTITLE_FONT,
        fill="#8a3d24",
    )

    for index, (label, filename, note) in enumerate(COMPONENTS):
        row, col = divmod(index, 4)
        x = MARGIN_X + col * (CARD_WIDTH + GAP_X)
        y = START_Y + row * (CARD_HEIGHT + GAP_Y)
        box = (x, y, x + CARD_WIDTH, y + CARD_HEIGHT)
        rounded_card(draw, box)

        image_box = (x + 25, y + 18, x + CARD_WIDTH - 25, y + IMAGE_HEIGHT)
        if filename:
            with Image.open(SRC / filename) as source:
                component = contain(source, CARD_WIDTH - 70, IMAGE_HEIGHT - 35)
            px = x + (CARD_WIDTH - component.width) // 2
            py = y + 20 + (IMAGE_HEIGHT - 35 - component.height) // 2
            canvas.paste(component, (px, py), component)
        else:
            draw.rounded_rectangle(image_box, radius=14, fill="#e8eef5", outline="#b3c0ce", width=2)
            if "GY-291" in label:
                placeholder = "GY-291\nADXL345"
            elif "Raspberry" in label:
                placeholder = "RASPBERRY\nPI 4"
            else:
                placeholder = "SWITCH\n+\nFUSE"
            draw_centered_text(draw, image_box, placeholder, LABEL_FONT, "#46627c")

        draw_centered_text(
            draw,
            (x + 12, y + 220, x + CARD_WIDTH - 12, y + 266),
            label,
            LABEL_FONT,
            "#222222",
        )
        draw_centered_text(
            draw,
            (x + 18, y + 270, x + CARD_WIDTH - 18, y + CARD_HEIGHT - 10),
            note or "",
            SMALL_FONT,
            "#5a5a5a",
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, quality=95)
    print(f"Built {OUT}")


if __name__ == "__main__":
    build()
