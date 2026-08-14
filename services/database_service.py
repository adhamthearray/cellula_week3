"""Per-dataset SQLite storage with read-only query execution."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from config import settings


class DatasetNotFoundError(ValueError):
    pass


class DatabaseService:
    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or settings.SQLITE_STORAGE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_dataset(self, frame: pd.DataFrame, table_name: str) -> str:
        dataset_id = f"dataset_{uuid.uuid4().hex}"
        database_path = self.get_database_path(dataset_id)
        with sqlite3.connect(database_path) as connection:
            frame.to_sql(table_name, connection, if_exists="replace", index=False)
        return dataset_id

    def get_database_path(self, dataset_id: str) -> Path:
        if not dataset_id.startswith("dataset_") or not dataset_id.replace("_", "").isalnum():
            raise DatasetNotFoundError("Invalid dataset ID.")
        return self.storage_path / f"{dataset_id}.sqlite"

    def _existing_path(self, dataset_id: str) -> Path:
        path = self.get_database_path(dataset_id)
        if not path.is_file():
            raise DatasetNotFoundError("Dataset was not found. Upload it again and use its dataset_id.")
        return path

    def get_table_names(self, dataset_id: str) -> list[str]:
        path = self._existing_path(dataset_id)
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as connection:
            return [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]

    def get_schema(self, dataset_id: str) -> str:
        path = self._existing_path(dataset_id)
        lines: list[str] = []
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as connection:
            for table in self.get_table_names(dataset_id):
                lines.append(f"Table: {table}")
                columns = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
                lines.extend(f"- {column[1]} {column[2] or 'TEXT'}" for column in columns)
        return "\n".join(lines)

    def execute_readonly(self, dataset_id: str, sql: str, max_rows: int | None = None) -> dict[str, Any]:
        path = self._existing_path(dataset_id)
        limit = max_rows or settings.MAX_QUERY_ROWS
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(sql)
            records = [dict(row) for row in cursor.fetchmany(limit + 1)]
        truncated = len(records) > limit
        records = records[:limit]
        # JSON round-trip changes SQLite/Pandas scalar values into API-safe primitives.
        records = json.loads(json.dumps(records, default=str))
        return {"columns": list(records[0].keys()) if records else [item[0] for item in cursor.description or []], "rows": records, "row_count": len(records), "truncated": truncated}
