"""Natural-language to SQLite SELECT generation and defensive validation."""

from __future__ import annotations

import re

from services.generator import CodeGenerator


class SQLValidationError(ValueError):
    pass


FORBIDDEN_SQL = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|REPLACE)\b", re.IGNORECASE)


class SQLGenerator:
    def __init__(self, generator: CodeGenerator | None = None) -> None:
        self.generator = generator or CodeGenerator()

    def generate(self, query: str, schema: str) -> str:
        system = """You are a SQLite SQL generation engine. Return only one valid SQLite SELECT query, without markdown or explanation. Never write data or change schema. Use only tables and columns present in the provided schema."""
        prompt = f"DATABASE SCHEMA:\n{schema}\n\nUSER REQUEST:\n{query}\n\nReturn a single SQLite SELECT query only."
        sql = self.generator.complete(system, prompt).strip()
        return validate_sql(sql)


def validate_sql(sql: str) -> str:
    """Return normalized safe SQL or reject it before it reaches SQLite."""
    cleaned = sql.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE).strip()
    if not cleaned:
        raise SQLValidationError("The model did not generate SQL.")
    if "--" in cleaned or "/*" in cleaned:
        raise SQLValidationError("SQL comments are not allowed.")
    statements = [part.strip() for part in cleaned.split(";") if part.strip()]
    if len(statements) != 1:
        raise SQLValidationError("Only one SQL statement is allowed.")
    cleaned = statements[0]
    if not re.match(r"^(SELECT|WITH)\b", cleaned, re.IGNORECASE):
        raise SQLValidationError("Only SELECT queries are allowed.")
    if FORBIDDEN_SQL.search(cleaned):
        raise SQLValidationError("Unsafe SQL was rejected.")
    return cleaned
