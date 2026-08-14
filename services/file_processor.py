"""Dataset file validation and DataFrame loading."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


class DatasetFileError(ValueError):
    """Raised when an uploaded dataset cannot be safely used."""


def normalize_identifier(value: object, fallback: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]", "_", str(value).strip().lower())
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = fallback
    if name[0].isdigit():
        name = f"_{name}"
    return name


def _normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    columns: list[str] = []
    used: set[str] = set()
    for index, column in enumerate(frame.columns, start=1):
        base = normalize_identifier(column, f"column_{index}")
        name = base
        suffix = 2
        while name in used:
            name = f"{base}_{suffix}"
            suffix += 1
        used.add(name)
        columns.append(name)
    frame.columns = columns
    return frame


def load_dataset(filename: str, content: bytes) -> tuple[pd.DataFrame, str]:
    """Load one supported upload and return its DataFrame and normalized table name."""
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DatasetFileError("Unsupported file type. Upload a CSV, XLSX, or XLS file.")
    if not content:
        raise DatasetFileError("The uploaded file is empty.")

    try:
        source = BytesIO(content)
        if suffix == ".csv":
            frame = pd.read_csv(source)
        else:
            frame = pd.read_excel(source)
    except Exception as exc:
        raise DatasetFileError("The uploaded dataset could not be read.") from exc

    if frame.empty:
        raise DatasetFileError("The dataset has no rows.")
    if len(frame.columns) == 0:
        raise DatasetFileError("The dataset has no usable columns.")
    frame = _normalise_columns(frame)
    table_name = normalize_identifier(Path(filename).stem, "dataset")
    return frame, table_name
