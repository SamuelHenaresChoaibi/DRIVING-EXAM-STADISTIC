from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from PyQt6 import QtCore, QtWidgets

from services.charts import ExamsChartCanvas
from services.csv_importer import read_exam_file
from services.database import Database, DatabaseError
from services.reports import export_pdf_report
from ui.main_window_ui import Ui_MainWindow


# Modelo Qt para mostrar los resultados en un QTableView.
class ResultsTableModel(QtCore.QAbstractTableModel):
    # Inicializa el modelo y define las columnas visibles.
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self._rows: list[dict[str, Any]] = rows or []
        self._columns: list[tuple[str, str]] = [
            ("Year", "year"),
            ("Month", "month"),
            ("Province", "province"),
            ("Exam center", "exam_center"),
            ("School code", "school_code"),
            ("School name", "school_name"),
            ("Section", "section_code"),
            ("Exam type", "exam_type"),
            ("Permit", "permit"),
            ("Passed", "num_passed"),
            ("Failed", "num_failed"),
            ("Passed 1st", "num_passed_1st"),
            ("Passed 2nd", "num_passed_2nd"),
            ("Passed 3rd/4th", "num_passed_3rd_or_4th"),
            ("Passed 5+", "num_passed_5plus"),
        ]

    # Sustituye las filas del modelo y notifica a la vista.
    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    # Devuelve el número de filas del modelo.
    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    # Devuelve el número de columnas del modelo.
    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._columns)

    # Devuelve el texto de los encabezados (columnas/filas) de la tabla.
    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self._columns[section][0]
        return section + 1

    # Devuelve el texto/alineación a mostrar para una celda concreta.
    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: N802
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        _, key = self._columns[index.column()]
        value = row.get(key)

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return "" if value is None else str(value)

        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, int):
                return int(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            return int(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)

        return None

    # Exporta la tabla como cabeceras + filas (texto) para reportes.
    def export_table(self) -> tuple[list[str], list[list[str]]]:
        headers = [title for title, _ in self._columns]
        rows: list[list[str]] = []
        for row in self._rows:
            rows.append([str(row.get(key, "")) for _, key in self._columns])
        return headers, rows


# Ventana principal: filtros, tabla, gráfica y exportación.
class MainWindow(QtWidgets.QMainWindow):
    # Construye la UI, inicializa modelos y carga datos iniciales.
    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._chart = ExamsChartCanvas(self.ui.chartContainer)
        self.ui.chartContainerLayout.addWidget(self._chart)

        self._table_model = ResultsTableModel([])
        self._table_proxy = QtCore.QSortFilterProxyModel(self)
        self._table_proxy.setSourceModel(self._table_model)
        self._table_proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.ui.tableView.setModel(self._table_proxy)
        self.ui.tableView.sortByColumn(0, QtCore.Qt.SortOrder.DescendingOrder)

        self._current_rows: list[dict[str, Any]] = []
        self._last_totals: dict[str, int] = {"passed": 0, "failed": 0}

        self._wire_signals()
        self.refresh_filters()
        self.apply_filters()

    # Cierra la base de datos al cerrar la ventana.
    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self._db.close()
        finally:
            super().closeEvent(event)

    # Conecta señales/acciones de la UI con sus handlers.
    def _wire_signals(self) -> None:
        self.ui.actionImportCsv.triggered.connect(self.import_csv)
        self.ui.actionExit.triggered.connect(self.close)

        self.ui.applyButton.clicked.connect(self.apply_filters)
        self.ui.clearButton.clicked.connect(self.clear_filters)
        self.ui.yearCombo.currentIndexChanged.connect(self._on_year_changed)

        self.ui.exportPdfTableAction.triggered.connect(lambda: self.export_pdf("table"))
        self.ui.exportPdfChartAction.triggered.connect(lambda: self.export_pdf("chart"))
        self.ui.exportPdfBothAction.triggered.connect(lambda: self.export_pdf("both"))

    # Devuelve el valor (data) actual seleccionado en un combo.
    def _combo_value(self, combo: QtWidgets.QComboBox) -> Any:
        return combo.currentData()

    # Devuelve el valor seleccionado o el texto si el combo es editable.
    def _combo_selected_value(self, combo: QtWidgets.QComboBox) -> Any:
        data = combo.currentData()
        if data is not None:
            return data
        if combo.currentIndex() == 0:
            return None
        text = combo.currentText().strip()
        return text if text else None

    # Rellena un combo con valores y mantiene la selección si es posible.
    def _set_combo_items(self, combo: QtWidgets.QComboBox, values: list[Any], formatter=str) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("All", None)
        for value in values:
            combo.addItem(formatter(value), value)
        if current is not None:
            idx = combo.findData(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    # Recarga los valores de filtros desde la base de datos.
    def refresh_filters(self) -> None:
        years = self._db.distinct_years()
        self._set_combo_items(self.ui.yearCombo, years, formatter=str)
        self._refresh_months()

        self._set_combo_items(self.ui.provinceCombo, self._db.distinct_values("province"))
        self._set_combo_items(self.ui.centerCombo, self._db.distinct_values("exam_center"))
        self._set_combo_items(self.ui.examTypeCombo, self._db.distinct_values("exam_type"))
        self._set_combo_items(self.ui.permitCombo, self._db.distinct_values("permit"))

    # Handler: actualiza meses cuando cambia el año.
    def _on_year_changed(self) -> None:
        self._refresh_months()

    # Rellena el combo de meses para el año seleccionado.
    def _refresh_months(self) -> None:
        year = self._combo_value(self.ui.yearCombo)
        months = self._db.distinct_months(year=year)
        self._set_combo_items(self.ui.monthCombo, months, formatter=lambda m: f"{m:02d}")

    # Construye el diccionario de filtros a partir del estado de la UI.
    def current_filters(self) -> dict[str, Any]:
        filters: dict[str, Any] = {}

        year = self._combo_value(self.ui.yearCombo)
        if year is not None:
            filters["year"] = int(year)
        month = self._combo_value(self.ui.monthCombo)
        if month is not None:
            filters["month"] = int(month)

        for key, combo in [
            ("province", self.ui.provinceCombo),
            ("exam_center", self.ui.centerCombo),
            ("exam_type", self.ui.examTypeCombo),
            ("permit", self.ui.permitCombo),
        ]:
            value = self._combo_selected_value(combo)
            if value:
                filters[key] = str(value)

        school_code = self.ui.schoolCodeLineEdit.text().strip()
        if school_code:
            filters["school_code"] = school_code

        school_name = self.ui.schoolNameLineEdit.text().strip()
        if school_name:
            filters["school_name_contains"] = school_name

        return filters

    # Aplica filtros: consulta DB, actualiza tabla, gráfica y barra de estado.
    def apply_filters(self) -> None:
        filters = self.current_filters()
        self._current_rows = self._db.fetch_rows(filters)
        self._table_model.set_rows(self._current_rows)

        totals = self._db.fetch_totals(filters)
        self._last_totals = totals

        chart_rows = self._db.fetch_totals_by_exam_type(filters)
        self._chart.plot_exam_type_totals(chart_rows)

        total_rows = len(self._current_rows)
        passed = totals.get("passed", 0)
        failed = totals.get("failed", 0)
        attempted = passed + failed
        pass_rate = (passed / attempted * 100.0) if attempted else 0.0
        self.statusBar().showMessage(
            f"Rows: {total_rows} | Passed: {passed} | Failed: {failed} | Pass rate: {pass_rate:.1f}%"
        )

    # Resetea filtros/inputs a su estado inicial y recarga resultados.
    def clear_filters(self) -> None:
        for combo in [
            self.ui.yearCombo,
            self.ui.monthCombo,
            self.ui.provinceCombo,
            self.ui.centerCombo,
            self.ui.examTypeCombo,
            self.ui.permitCombo,
        ]:
            combo.setCurrentIndex(0)
        self.ui.schoolCodeLineEdit.clear()
        self.ui.schoolNameLineEdit.clear()
        self.apply_filters()

    # Importa un CSV/TXT, lo inserta en la DB y refresca la vista.
    def import_csv(self) -> None:
        path_str, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import DGT exam results",
            str(Path.home()),
            "CSV/TXT files (*.csv *.txt);;All files (*.*)",
        )
        if not path_str:
            return

        try:
            import_result = read_exam_file(path_str)
            inserted = self._db.import_exam_rows(import_result.rows, source_file=path_str)
        except (ValueError, DatabaseError) as exc:
            QtWidgets.QMessageBox.critical(self, "Import failed", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Import failed", f"Unexpected error: {exc!r}")
            return

        periods_str = ", ".join(f"{y}-{m:02d}" for (y, m) in sorted(import_result.periods))
        QtWidgets.QMessageBox.information(
            self,
            "Import completed",
            f"Imported period(s): {periods_str}\nInserted rows: {inserted}",
        )
        self.refresh_filters()
        self.apply_filters()

    # Exporta un reporte PDF (tabla, gráfica o ambos).
    def export_pdf(self, mode: str) -> None:
        include_table = mode in ("table", "both")
        include_chart = mode in ("chart", "both")

        default_name = "driving_exams_report.pdf"
        year = self._combo_value(self.ui.yearCombo)
        month = self._combo_value(self.ui.monthCombo)
        if year and month:
            default_name = f"driving_exams_report_{int(year)}_{int(month):02d}.pdf"

        path_str, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export PDF report",
            str(Path.home() / default_name),
            "PDF files (*.pdf)",
        )
        if not path_str:
            return

        filters = self.current_filters()
        chart_image = self._chart.grab().toImage() if include_chart else None
        headers, rows = self._table_model.export_table()

        try:
            export_pdf_report(
                pdf_path=Path(path_str),
                filters=filters,
                totals=self._last_totals,
                table_headers=headers,
                table_rows=rows if include_table else [],
                chart_image=chart_image,
                include_table=include_table,
                include_chart=include_chart,
            )
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Export failed", f"Unexpected error: {exc!r}")
            return

        QtWidgets.QMessageBox.information(self, "Export completed", f"Saved: {path_str}")


# Punto de entrada: crea la app Qt, la DB y muestra la ventana principal.
def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Driving Exams Statistics")

    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "data" / "driving_exams.db"
    db = Database(db_path)

    window = MainWindow(db)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
