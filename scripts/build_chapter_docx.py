from __future__ import annotations

from pathlib import Path

import build_chapter_3_docx as docx_builder
import build_table_workbook


ROOT = Path(__file__).resolve().parents[1]


def build(markdown_path: Path, drawio_dir: Path, docx_path: Path) -> dict[str, Path]:
    docx_builder.MARKDOWN_PATH = markdown_path
    docx_builder.DRAWIO_DIR = drawio_dir
    docx_builder.EXPORT_DIR = drawio_dir / "exported"
    docx_builder.DOCX_PATH = docx_path
    caption_to_image = docx_builder.render_all_drawio()
    embedded_count = docx_builder.build_docx(caption_to_image)
    print(f"Built {docx_path.name}: embedded {embedded_count} images")
    return caption_to_image


def build_combined(
    chapters: list[tuple[Path, dict[str, Path]]],
    docx_path: Path,
) -> None:
    builder = docx_builder.DocxBuilder(page_number_start=1)
    embedded_count = 0
    for index, (markdown_path, caption_to_image) in enumerate(chapters):
        if index:
            builder.add_page_break()
        stop_heading = "## REFERENCE" if markdown_path.name == "literature_review.md" else None
        used = docx_builder.append_markdown(
            builder,
            markdown_path,
            caption_to_image,
            stop_heading=stop_heading,
        )
        embedded_count += len(used)
    literature_path = ROOT / "literature_review.md"
    builder.add_page_break()
    docx_builder.append_markdown(
        builder,
        literature_path,
        {},
        start_heading="## REFERENCE",
    )
    builder.write(docx_path)
    print(
        f"Built {docx_path.name}: embedded {embedded_count} images with "
        "continuous page numbering and references after Chapter 4"
    )


def main() -> None:
    build_table_workbook.main()
    specifications = [
        (
            ROOT / "chapter_1_introduction.md",
            ROOT / "drawio" / "chapter_1",
            ROOT / "chapter_1_introduction.docx",
        ),
        (
            ROOT / "literature_review.md",
            ROOT / "drawio" / "chapter_2",
            ROOT / "chapter_2_literature_review.docx",
        ),
        (
            ROOT / "chapter_3_methodology.md",
            ROOT / "drawio" / "chapter_3",
            ROOT / "chapter_3_methodology.docx",
        ),
        (
            ROOT / "chapter_4_results_and_discussion.md",
            ROOT / "drawio" / "chapter_4",
            ROOT / "chapter_4_results_and_discussion.docx",
        ),
    ]
    chapters: list[tuple[Path, dict[str, Path]]] = []
    for markdown_path, drawio_dir, docx_path in specifications:
        chapters.append((markdown_path, build(markdown_path, drawio_dir, docx_path)))
    build_combined(chapters, ROOT / "thesis_chapters_1_to_4.docx")


if __name__ == "__main__":
    main()
