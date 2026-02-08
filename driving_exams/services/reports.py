from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QFont, QImage, QPainter, QPdfWriter, QPen


# Convierte el dict de filtros en líneas legibles para el reporte.
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


# Genera un PDF con resumen, tabla y/o gráfica según la selección.
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
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    page_w = writer.width()
    page_h = writer.height()
    margin = int(page_w * 0.06)
    x0 = margin
    y = margin
    content_w = page_w - (2 * margin)

    title_font = QFont("Helvetica", 25, QFont.Weight.Bold)
    body_font = QFont("Helvetica", 11)
    small_font = QFont("Helvetica", 9)

    align_top_left = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    align_vcenter_left = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    # Dibuja un bloque de texto ajustando altura, wrap y salto de página.
    def draw_text_block(text: str, font: QFont, *, wrap: bool = False, spacing_after: int = 0) -> None:
        nonlocal y
        painter.setFont(font)
        flags = align_top_left
        if wrap:
            flags |= int(Qt.TextFlag.TextWordWrap)

        required_h = painter.boundingRect(QRect(0, 0, content_w, 10_000), flags, text).height()
        if y + required_h > page_h - margin:
            writer.newPage()
            y = margin
        painter.drawText(QRect(x0, y, content_w, required_h), flags, text)
        y += required_h + spacing_after

    draw_text_block("Driving Exams Report", title_font, spacing_after=10)
    draw_text_block(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_font, spacing_after=6)
    for line in _filters_to_lines(filters):
        draw_text_block(line, body_font, wrap=True, spacing_after=4)

    passed = int(totals.get("passed", 0) or 0)
    failed = int(totals.get("failed", 0) or 0)
    attempted = passed + failed
    pass_rate = (passed / attempted * 100.0) if attempted else 0.0
    draw_text_block(
        f"Totals: Passed={passed} | Failed={failed} | Pass rate={pass_rate:.1f}%",
        body_font,
        wrap=True,
        spacing_after=14,
    )

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
        col_w = max(25, content_w // col_count)
        remainder = content_w - (col_w * col_count)
        col_widths = [col_w + (1 if col < remainder else 0) for col in range(col_count)]
        col_x_positions = [x0]
        for w in col_widths[:-1]:
            col_x_positions.append(col_x_positions[-1] + w)

        cell_pad_x = max(8, int(page_w * 0.003))
        cell_pad_y = max(6, int(page_w * 0.002))

        painter.setFont(small_font)
        row_h = max(30, painter.fontMetrics().lineSpacing() + (cell_pad_y * 2))

        painter.setFont(body_font)
        header_flags = align_vcenter_left | int(Qt.TextFlag.TextWordWrap)
        header_max_text_h = 0
        for col, text in enumerate(table_headers):
            available_w = max(0, col_widths[col] - (cell_pad_x * 2))
            header_max_text_h = max(
                header_max_text_h,
                painter.boundingRect(QRect(0, 0, available_w, 10_000), header_flags, str(text)).height(),
            )
        header_h = max(row_h, header_max_text_h + (cell_pad_y * 2))

        # Dibuja una fila de la tabla (cabecera o datos) con padding.
        def draw_row(values: list[str], y_pos: int, row_height: int, is_header: bool = False) -> None:
            painter.setFont(body_font if is_header else small_font)
            metrics = painter.fontMetrics()
            for col, text in enumerate(values):
                rect = QRect(col_x_positions[col], y_pos, col_widths[col], row_height)
                painter.drawRect(rect)
                text_rect = rect.adjusted(cell_pad_x, cell_pad_y, -cell_pad_x, -cell_pad_y)
                if is_header:
                    painter.drawText(text_rect, header_flags, str(text))
                    continue

                elided = metrics.elidedText(str(text), Qt.TextElideMode.ElideRight, text_rect.width())
                painter.drawText(text_rect, align_vcenter_left, elided)

        if y + header_h > page_h - margin:
            writer.newPage()
            y = margin

        draw_row(table_headers, y, header_h, is_header=True)
        y += header_h

        for row in table_rows:
            if y + row_h > page_h - margin:
                writer.newPage()
                y = margin
                draw_row(table_headers, y, header_h, is_header=True)
                y += header_h
            draw_row(row, y, row_h, is_header=False)
            y += row_h

    painter.end()
