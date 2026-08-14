"""Compact, bounded summaries of SQL query results."""

from __future__ import annotations

from typing import Any

import pandas as pd

from services.generator import CodeGenerator


class ResultAnalysisService:
    def __init__(self, generator: CodeGenerator | None = None) -> None:
        self.generator = generator or CodeGenerator()

    def analyze(self, query: str, result: dict[str, Any]) -> str:
        rows = result["rows"]
        if not rows:
            return "The query returned no matching rows. Try broadening or rephrasing the question."
        frame = pd.DataFrame(rows)
        facts = [f"The query returned {result['row_count']} row(s)."]
        for column in frame.select_dtypes(include="number").columns:
            series = frame[column].dropna()
            if not series.empty:
                facts.append(f"{column}: min {series.min():g}, max {series.max():g}, mean {series.mean():.2f}, median {series.median():.2f}.")
        for column in frame.select_dtypes(include=["object", "string", "category"]).columns[:3]:
            values = frame[column].dropna()
            if not values.empty:
                top, count = values.value_counts().index[0], int(values.value_counts().iloc[0])
                facts.append(f"Most common {column}: {top} ({count}).")
        summary = " ".join(facts)
        if not self.generator.api_key:
            return summary
        prompt = f"Question: {query}\nResult summary: {summary}\nSample: {frame.head(5).to_dict(orient='records')}\nGive a concise factual analysis, using only these facts."
        generated = self.generator.complete("You are a careful data analyst. Do not invent facts.", prompt)
        return generated if not generated.startswith("Code generation failed:") else summary
