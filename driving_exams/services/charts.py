from __future__ import annotations

from typing import Any

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# Canvas de Matplotlib embebido en Qt para mostrar gráficas de resultados.
class ExamsChartCanvas(FigureCanvas):
    # Inicializa la figura y el eje principal de la gráfica.
    def __init__(self, parent=None) -> None:
        self._figure = Figure(figsize=(6, 4), tight_layout=True)
        self._ax = self._figure.add_subplot(111)
        super().__init__(self._figure)
        self.setParent(parent)

    # Dibuja una gráfica apilada (aprobados/suspensos) por tipo de examen.
    def plot_exam_type_totals(self, rows: list[dict[str, Any]]) -> None:
        self._ax.clear()

        if not rows:
            self._ax.text(0.5, 0.5, "No data", ha="center", va="center")
            self._ax.set_xticks([])
            self._ax.set_yticks([])
            self.draw()
            return

        labels = [str(r.get("exam_type", "")) for r in rows]
        passed = [int(r.get("passed", 0) or 0) for r in rows]
        failed = [int(r.get("failed", 0) or 0) for r in rows]

        x = list(range(len(labels)))
        self._ax.bar(x, passed, label="Passed")
        self._ax.bar(x, failed, bottom=passed, label="Failed")

        self._ax.set_title("Totals by exam type")
        self._ax.set_ylabel("Candidates")
        self._ax.set_xticks(x)
        self._ax.set_xticklabels(labels, rotation=30, ha="right")
        self._ax.legend()
        self.draw()
