from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


REQUIRED_COLUMNS = [
    "DESC_PROVINCIA",
    "CENTRO_EXAMEN",
    "CODIGO_AUTOESCUELA",
    "NOMBRE_AUTOESCUELA",
    "CODIGO_SECCION",
    "MES",
    "ANYO",
    "TIPO_EXAMEN",
    "NOMBRE_PERMISO",
    "NUM_APTOS",
    "NUM_APTOS_1conv",
    "NUM_APTOS_2conv",
    "NUM_APTOS_3o4conv",
    "NUM_APTOS_5_o_mas_conv",
    "NUM_NO_APTOS",
]


# Convierte un valor de texto a entero, devolviendo 0 si está vacío.
def _to_int(value: str) -> int:
    value = (value or "").strip()
    if value == "":
        return 0
    return int(value)


@dataclass(frozen=True, slots=True)
# Representa una fila del dataset de exámenes con tipos adecuados.
class ExamRow:
    province: str
    exam_center: str
    school_code: str
    school_name: str
    section_code: str
    month: int
    year: int
    exam_type: str
    permit: str
    num_passed: int
    num_passed_1st: int
    num_passed_2nd: int
    num_passed_3rd_or_4th: int
    num_passed_5plus: int
    num_failed: int

    @staticmethod
    # Construye un ExamRow a partir de una fila CSV y un índice de columnas.
    def from_csv_row(row: list[str], idx: dict[str, int]) -> "ExamRow":
        # Helper: obtiene y limpia el valor de una columna por nombre.
        def g(key: str) -> str:
            i = idx[key]
            return (row[i] if i < len(row) else "").strip()

        return ExamRow(
            province=g("DESC_PROVINCIA"),
            exam_center=g("CENTRO_EXAMEN"),
            school_code=g("CODIGO_AUTOESCUELA"),
            school_name=g("NOMBRE_AUTOESCUELA"),
            section_code=g("CODIGO_SECCION"),
            month=_to_int(g("MES")),
            year=_to_int(g("ANYO")),
            exam_type=g("TIPO_EXAMEN"),
            permit=g("NOMBRE_PERMISO"),
            num_passed=_to_int(g("NUM_APTOS")),
            num_passed_1st=_to_int(g("NUM_APTOS_1conv")),
            num_passed_2nd=_to_int(g("NUM_APTOS_2conv")),
            num_passed_3rd_or_4th=_to_int(g("NUM_APTOS_3o4conv")),
            num_passed_5plus=_to_int(g("NUM_APTOS_5_o_mas_conv")),
            num_failed=_to_int(g("NUM_NO_APTOS")),
        )

    # Devuelve la tupla lista para inserción en la base de datos.
    def as_db_tuple(self) -> tuple[object, ...]:
        return (
            self.province,
            self.exam_center,
            self.school_code,
            self.school_name,
            self.section_code,
            self.month,
            self.year,
            self.exam_type,
            self.permit,
            self.num_passed,
            self.num_passed_1st,
            self.num_passed_2nd,
            self.num_passed_3rd_or_4th,
            self.num_passed_5plus,
            self.num_failed,
        )


@dataclass(frozen=True, slots=True)
# Resultado de importación: filas normalizadas y periodos detectados (año/mes).
class CsvImportResult:
    rows: list[ExamRow]
    periods: set[tuple[int, int]]  # (year, month)


# Lee el archivo con un encoding específico y devuelve filas parseadas.
def _read_with_encoding(path: Path, encoding: str) -> list[ExamRow]:
    with path.open("r", encoding=encoding, newline="") as f:
        reader = csv.reader(f, delimiter=";")
        try:
            header_raw = next(reader)
        except StopIteration:
            return []

        header = [h.strip().lstrip("\ufeff") for h in header_raw]
        idx = {name: i for i, name in enumerate(header)}
        missing = [col for col in REQUIRED_COLUMNS if col not in idx]
        if missing:
            raise ValueError(f"Missing required column(s): {', '.join(missing)}")

        rows: list[ExamRow] = []
        for row in reader:
            if not row or all((cell or "").strip() == "" for cell in row):
                continue
            rows.append(ExamRow.from_csv_row(row, idx))
        return rows


# Lee un fichero CSV/TXT de la DGT probando varios encodings y valida columnas.
def read_exam_file(path: str | Path) -> CsvImportResult:
    file_path = Path(path)
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            rows = _read_with_encoding(file_path, encoding=encoding)
            periods = {(r.year, r.month) for r in rows}
            return CsvImportResult(rows=rows, periods=periods)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue

    raise ValueError(f"Could not decode file: {file_path}. Last error: {last_error!r}")
