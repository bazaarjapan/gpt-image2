from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "manga_config.json"
DEFAULT_FONT_PATHS = [
    Path("C:/Windows/Fonts/BIZ-UDMinchoM.ttc"),
    Path("C:/Windows/Fonts/NotoSerifJP-VF.ttf"),
    Path("C:/Windows/Fonts/yumin.ttf"),
    Path("C:/Windows/Fonts/msgothic.ttc"),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_font() -> Path:
    for path in DEFAULT_FONT_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError("No Japanese font found in C:/Windows/Fonts")


def parse_page_selection(value: str | None, all_pages: list[int]) -> list[int]:
    if not value:
        return all_pages
    pages: set[int] = set()
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start, end = chunk.split("-", 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(chunk))
    return sorted(pages)


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^「|」$", "", text)
    return text


def vertical_columns(text: str, max_rows: int) -> list[str]:
    chars = list(clean_text(text))
    if not chars:
        return []
    return ["".join(chars[index : index + max_rows]) for index in range(0, len(chars), max_rows)]


def normalize_char(char: str) -> str:
    table = {
        "ー": "｜",
        "―": "｜",
        "…": "…",
        "、": "、",
        "。": "。",
        "！": "！",
        "？": "？",
        "(": "（",
        ")": "）",
    }
    return table.get(char, char)


def draw_vertical_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    line_gap: int,
    column_gap: int,
) -> tuple[int, int]:
    columns = vertical_columns(text, max_rows=13)
    if not columns:
        return (0, 0)

    char_w = max(font.getbbox("あ")[2], 20)
    char_h = max(font.getbbox("あ")[3] - font.getbbox("あ")[1], 24)
    x, y = xy
    for column_index, column in enumerate(columns):
        cx = x - column_index * (char_w + column_gap)
        cy = y
        for char in column:
            draw.text((cx, cy), normalize_char(char), font=font, fill=fill, anchor="mm")
            cy += char_h + line_gap

    width = len(columns) * char_w + max(0, len(columns) - 1) * column_gap
    height = max(len(column) for column in columns) * (char_h + line_gap)
    return (width, height)


def measure_vertical_text(text: str, font: ImageFont.FreeTypeFont, line_gap: int, column_gap: int) -> tuple[int, int]:
    columns = vertical_columns(text, max_rows=13)
    if not columns:
        return (0, 0)
    bbox = font.getbbox("あ")
    char_w = max(bbox[2], 20)
    char_h = max(bbox[3] - bbox[1], 24)
    width = len(columns) * char_w + max(0, len(columns) - 1) * column_gap
    height = max(len(column) for column in columns) * (char_h + line_gap)
    return (width, height)


def panel_count(items: list[dict]) -> int:
    if not items:
        return 1
    return max(int(item.get("panel", 1)) for item in items)


def bubble_position(
    image_size: tuple[int, int],
    item: dict,
    item_index: int,
    count_for_panel: int,
    index_in_panel: int,
    bubble_size: tuple[int, int],
    total_panels: int,
) -> tuple[int, int, int, int]:
    width, height = image_size
    margin = 34
    panel = int(item.get("panel", 1))
    panel_band = height / max(total_panels, 1)
    y_center = int((panel - 0.5) * panel_band)
    y_center += int((index_in_panel - (count_for_panel - 1) / 2) * 74)
    y_center = max(margin + bubble_size[1] // 2, min(height - margin - bubble_size[1] // 2, y_center))

    side_cycle = item_index % 4
    if side_cycle in {0, 3}:
        x_center = width - margin - bubble_size[0] // 2
    else:
        x_center = margin + bubble_size[0] // 2

    left = max(margin, min(width - margin - bubble_size[0], x_center - bubble_size[0] // 2))
    top = max(margin, min(height - margin - bubble_size[1], y_center - bubble_size[1] // 2))
    return (left, top, left + bubble_size[0], top + bubble_size[1])


def letter_page(input_path: Path, output_path: Path, items: list[dict], font_path: Path) -> None:
    image = Image.open(input_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    font = ImageFont.truetype(str(font_path), size=max(25, width // 39))
    small_font = ImageFont.truetype(str(font_path), size=max(16, width // 58))
    line_gap = 2
    column_gap = 8
    padding_x = 26
    padding_y = 24

    panel_totals: dict[int, int] = {}
    panel_seen: dict[int, int] = {}
    for item in items:
        panel = int(item.get("panel", 1))
        panel_totals[panel] = panel_totals.get(panel, 0) + 1

    total_panels = panel_count(items)
    for item_index, item in enumerate(items):
        text = clean_text(item.get("text", ""))
        if not text:
            continue
        panel = int(item.get("panel", 1))
        index_in_panel = panel_seen.get(panel, 0)
        panel_seen[panel] = index_in_panel + 1

        text_w, text_h = measure_vertical_text(text, font, line_gap, column_gap)
        bubble_w = max(96, text_w + padding_x * 2)
        bubble_h = max(96, text_h + padding_y * 2)
        bubble_w = min(bubble_w, int(width * 0.44))
        bubble_h = min(bubble_h, int(height * 0.28))
        box = bubble_position(
            image.size,
            item,
            item_index,
            panel_totals.get(panel, 1),
            index_in_panel,
            (bubble_w, bubble_h),
            total_panels,
        )

        draw.rounded_rectangle(box, radius=28, fill=(255, 255, 255), outline=(10, 10, 10), width=4)
        speaker = item.get("speaker", "")
        if speaker and speaker not in {"効果音", "テロップ", "タイトル", "警告表示"}:
            draw.text((box[0] + 12, box[1] + 10), speaker, font=small_font, fill=(0, 0, 0))

        text_x = box[2] - padding_x - max(font.getbbox("あ")[2], 20) // 2
        text_y = box[1] + padding_y + 12
        draw_vertical_text(draw, (text_x, text_y), text, font, (0, 0, 0), line_gap, column_gap)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    print(f"Wrote {output_path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Typeset Japanese dialogue onto generated manga pages.")
    parser.add_argument("--pages", help="Page numbers to letter, for example: 1,3,5-8. Defaults to all pages.")
    parser.add_argument("--font", help="Path to a Japanese font file.")
    args = parser.parse_args()

    config = load_json(CONFIG_PATH)
    manifest = load_json(ROOT / config["production_dir"] / "manifest.json")
    lettering = load_json(ROOT / manifest["assets"]["lettering"])
    font_path = Path(args.font) if args.font else find_font()

    items_by_page = {page["page"]: page.get("items", []) for page in lettering["pages"]}
    all_page_numbers = [page["page"] for page in manifest["pages"]]
    selected = set(parse_page_selection(args.pages, all_page_numbers))

    for page in manifest["pages"]:
        page_number = page["page"]
        if page_number not in selected:
            continue
        input_path = ROOT / page["output_file"]
        if not input_path.exists():
            print(f"Skip missing page image: {input_path.relative_to(ROOT)}", file=sys.stderr)
            continue
        output_path = ROOT / page["lettered_file"]
        letter_page(input_path, output_path, items_by_page.get(page_number, []), font_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

