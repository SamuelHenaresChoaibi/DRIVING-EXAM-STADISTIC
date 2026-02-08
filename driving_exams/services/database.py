from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.csv_importer import ExamRow


# Error específico de la capa de base de datos.
class DatabaseError(RuntimeError):
    pass


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS imported_periods (
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  imported_at TEXT NOT NULL,
  source_file TEXT,
  row_count INTEGER NOT NULL,
  PRIMARY KEY (year, month)
);

CREATE TABLE IF NOT EXISTS exam_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  province TEXT NOT NULL,
  exam_center TEXT NOT NULL,
  school_code TEXT NOT NULL,
  school_name TEXT NOT NULL,
  section_code TEXT NOT NULL,
  month INTEGER NOT NULL,
  year INTEGER NOT NULL,
  exam_type TEXT NOT NULL,
  permit TEXT NOT NULL,
  num_passed INTEGER NOT NULL,
  num_passed_1st INTEGER NOT NULL,
  num_passed_2nd INTEGER NOT NULL,
  num_passed_3rd_or_4th INTEGER NOT NULL,
  num_passed_5plus INTEGER NOT NULL,
  num_failed INTEGER NOT NULL,
  UNIQUE (province, exam_center, school_code, section_code, month, year, exam_type, permit)
    ON CONFLICT IGNORE
);

CREATE INDEX IF NOT EXISTS idx_exam_results_period ON exam_results (year, month);
CREATE INDEX IF NOT EXISTS idx_exam_results_filters ON exam_results (
  year, month, province, exam_center, exam_type, permit, school_code
);
"""


ALLOWED_DISTINCT_FIELDS = {
    "province": "province",
    "exam_center": "exam_center",
    "school_code": "school_code",
    "school_name": "school_name",
    "section_code": "section_code",
    "exam_type": "exam_type",
    "permit": "permit",
}


# Devuelve la fecha/hora actual en UTC en formato ISO-8601 (con sufijo Z).
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# Construye la cláusula WHERE y parámetros SQL a partir de filtros de la UI.
def _build_where(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if year := filters.get("year"):
        clauses.append("year = ?")
        params.append(int(year))
    if month := filters.get("month"):
        clauses.append("month = ?")
        params.append(int(month))

    for key in ("province", "exam_center", "school_code", "exam_type", "permit"):
        value = filters.get(key)
        if value:
            clauses.append(f"{key} = ?")
            params.append(str(value))

    if contains := filters.get("school_name_contains"):
        clauses.append("school_name LIKE ?")
        params.append(f"%{contains}%")

    where = " AND ".join(clauses)
    return where, params


# Encapsula el acceso a SQLite y operaciones de importación/consulta.
class Database:
    # Abre la conexión, prepara el directorio y asegura el esquema.
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self.initialize_schema()

    # Cierra la conexión con la base de datos.
    def close(self) -> None:
        self._conn.close()

    # Crea tablas/índices si no existen.
    def initialize_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    # Comprueba si un periodo (año/mes) ya fue importado.
    def is_period_imported(self, year: int, month: int) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM imported_periods WHERE year = ? AND month = ? LIMIT 1",
            (int(year), int(month)),
        )
        return cur.fetchone() is not None

    # Devuelve los años disponibles en el dataset.
    def distinct_years(self) -> list[int]:
        cur = self._conn.execute("SELECT DISTINCT year FROM exam_results ORDER BY year DESC")
        return [int(r[0]) for r in cur.fetchall()]

    # Devuelve los meses disponibles (filtrando por año opcionalmente).
    def distinct_months(self, year: int | None = None) -> list[int]:
        if year is None:
            cur = self._conn.execute("SELECT DISTINCT month FROM exam_results ORDER BY month ASC")
        else:
            cur = self._conn.execute(
                "SELECT DISTINCT month FROM exam_results WHERE year = ? ORDER BY month ASC",
                (int(year),),
            )
        return [int(r[0]) for r in cur.fetchall()]

    # Devuelve valores distintos para un campo permitido (para combos de filtros).
    def distinct_values(self, field: str) -> list[str]:
        if field not in ALLOWED_DISTINCT_FIELDS:
            raise DatabaseError(f"Unsupported distinct field: {field}")
        column = ALLOWED_DISTINCT_FIELDS[field]
        cur = self._conn.execute(f"SELECT DISTINCT {column} FROM exam_results ORDER BY {column} ASC")  # noqa: S608
        return [str(r[0]) for r in cur.fetchall() if r[0] is not None]

    # Importa filas, evita duplicados y registra los periodos importados.
    def import_exam_rows(self, rows: list[ExamRow], source_file: str | None = None) -> int:
        if not rows:
            raise DatabaseError("No data rows found in the selected file.")

        periods = {(r.year, r.month) for r in rows}
        already = [(y, m) for (y, m) in periods if self.is_period_imported(y, m)]
        if already:
            period_str = ", ".join(f"{y}-{m:02d}" for (y, m) in sorted(already))
            raise DatabaseError(f"Period(s) already imported: {period_str}")

        before = self._conn.total_changes
        with self._conn:
            self._conn.executemany(
                """
                INSERT OR IGNORE INTO exam_results (
                  province, exam_center, school_code, school_name, section_code,
                  month, year, exam_type, permit,
                  num_passed, num_passed_1st, num_passed_2nd, num_passed_3rd_or_4th, num_passed_5plus,
                  num_failed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [r.as_db_tuple() for r in rows],
            )

            inserted = self._conn.total_changes - before
            imported_at = _utc_now_iso()
            for year, month in periods:
                period_rows = sum(1 for r in rows if r.year == year and r.month == month)
                self._conn.execute(
                    """
                    INSERT INTO imported_periods (year, month, imported_at, source_file, row_count)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (int(year), int(month), imported_at, source_file, int(period_rows)),
                )

        return int(inserted)

    # Devuelve las filas detalladas para pintar la tabla principal.
    def fetch_rows(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where, params = _build_where(filters)
        sql = """
        SELECT
          year, month, province, exam_center, school_code, school_name, section_code,
          exam_type, permit,
          num_passed, num_failed,
          num_passed_1st, num_passed_2nd, num_passed_3rd_or_4th, num_passed_5plus
        FROM exam_results
        """
        if where:
            sql += f" WHERE {where}"
        sql += " ORDER BY year DESC, month DESC, province ASC, exam_center ASC, school_name ASC, exam_type ASC, permit ASC"

        cur = self._conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    # Devuelve totales agregados de aprobados/suspensos para los filtros.
    def fetch_totals(self, filters: dict[str, Any]) -> dict[str, int]:
        where, params = _build_where(filters)
        sql = "SELECT SUM(num_passed) AS passed, SUM(num_failed) AS failed FROM exam_results"
        if where:
            sql += f" WHERE {where}"
        cur = self._conn.execute(sql, params)
        row = cur.fetchone()
        if not row:
            return {"passed": 0, "failed": 0}
        return {"passed": int(row["passed"] or 0), "failed": int(row["failed"] or 0)}

    # Devuelve totales agrupados por tipo de examen para la gráfica.
    def fetch_totals_by_exam_type(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where, params = _build_where(filters)
        sql = """
        SELECT
          exam_type,
          SUM(num_passed) AS passed,
          SUM(num_failed) AS failed
        FROM exam_results
        """
        if where:
            sql += f" WHERE {where}"
        sql += " GROUP BY exam_type ORDER BY exam_type ASC"

        cur = self._conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
