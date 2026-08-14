"""Shared text analysis pipeline used by both text and voice endpoints."""

from __future__ import annotations

from typing import Any

from services.database_service import DatabaseService
from services.result_analysis import ResultAnalysisService
from services.sql_generator import SQLGenerator


class DataAnalysisService:
    def __init__(self, database: DatabaseService | None = None, sql_generator: SQLGenerator | None = None, result_analyzer: ResultAnalysisService | None = None) -> None:
        self.database = database or DatabaseService()
        self.sql_generator = sql_generator or SQLGenerator()
        self.result_analyzer = result_analyzer or ResultAnalysisService()

    def analyze_text(self, dataset_id: str, query: str) -> dict[str, Any]:
        query = query.strip()
        if not query:
            raise ValueError("A data question is required.")
        schema = self.database.get_schema(dataset_id)
        sql = self.sql_generator.generate(query, schema)
        result = self.database.execute_readonly(dataset_id, sql)
        analysis = self.result_analyzer.analyze(query, result)
        return {"dataset_id": dataset_id, "query": query, "generated_sql": sql, "columns": result["columns"], "rows": result["rows"], "row_count": result["row_count"], "analysis": analysis}
