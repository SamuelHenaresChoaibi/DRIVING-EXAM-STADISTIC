from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QFont, QImage, QPainter, QPdfWriter, QPen


def _filters_to_lines(filters: dict[str, Any]) -> list[str]:
    if not filters:
        return ["Filters: (none)"]
    parts: list[str] = []
    for key, label in [
        ("year", "Year"),
        ("month", "Month"),
        ("province", "Province"),
        ("exam_center", "Exam center"),
        ("exam_type", "Exam type"),
        ("permit", "Permit"),
        ("school_code", "School code"),
        ("school_name_contains", "School name contains"),
    ]:
        value = filters.get(key)
        if value is not None and value != "":
            parts.append(f"{label}: {value}")
    return ["Filters: " + " | ".join(parts)] if parts else ["Filters: (none)"]


def export_pdf_report(
    pdf_path: Path,
    filters: dict[str, Any],
    totals: dict[str, int],
    table_headers: list[str],
    table_rows: list[list[str]],
    chart_image: QImage | None,
    include_table: bool,
    include_chart: bool,
) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    writer = QPdfWriter(str(pdf_path))
    writer.setResolution(300)

    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    page_w = writer.width()
    page_h = writer.height()
    margin = int(page_w * 0.06)
    x0 = margin
    y = margin
    content_w = page_w - (2 * margin)

    title_font = QFont("Helvetica", 16)
    body_font = QFont("Helvetica", 9)
    small_font = QFont("Helvetica", 7)

    painter.setFont(title_font)
    painter.drawText(QRect(x0, y, content_w, 60), Qt.AlignmentFlag.AlignLeft, "Driving Exams Report")
    y += 45

    painter.setFont(body_font)
    painter.drawText(
        QRect(x0, y, content_w, 20),
        Qt.AlignmentFlag.AlignLeft,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    )
    y += 18

    for line in _filters_to_lines(filters):
        painter.drawText(QRect(x0, y, content_w, 20), Qt.AlignmentFlag.AlignLeft, line)
        y += 16

    passed = int(totals.get("passed", 0) or 0)
    failed = int(totals.get("failed", 0) or 0)
    attempted = passed + failed
    pass_rate = (passed / attempted * 100.0) if attempted else 0.0
    painter.drawText(
        QRect(x0, y, content_w, 20),
        Qt.AlignmentFlag.AlignLeft,
        f"Totals: Passed={passed} | Failed={failed} | Pass rate={pass_rate:.1f}%",
    )
    y += 24

    if include_chart and chart_image is not None and not chart_image.isNull():
        max_h = int(page_h * 0.35)
        scaled = chart_image.scaled(
            content_w,
            max_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if y + scaled.height() > page_h - margin:
            writer.newPage()
            y = margin
        painter.drawImage(QRect(x0, y, scaled.width(), scaled.height()), scaled)
        y += scaled.height() + 20

    if include_table and table_headers and table_rows:
        painter.setFont(small_font)
        pen = QPen()
        painter.setPen(pen)

        col_count = len(table_headers)
        col_w = max(1, content_w // col_count)
        row_h = 18

        def draw_row(values: list[str], y_pos: int, is_header: bool = False) -> None:
            painter.setFont(body_font if is_header else small_font)
            for col, text in enumerate(values):
                rect = QRect(x0 + col * col_w, y_pos, col_w, row_h)
                painter.drawRect(rect)
                painter.drawText(
                    rect.adjusted(3, 0, -3, 0),
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                    str(text),
                )

        if y + row_h > page_h - margin:
            writer.newPage()
            y = margin

        draw_row(table_headers, y, is_header=True)
        y += row_h

        for row in table_rows:
            if y + row_h > page_h - margin:
                writer.newPage()
                y = margin
                draw_row(table_headers, y, is_header=True)
                y += row_h
            draw_row(row, y, is_header=False)
            y += row_h

    painter.end()

