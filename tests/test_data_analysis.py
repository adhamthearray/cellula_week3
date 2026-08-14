from pathlib import Path

import pandas as pd
import pytest

from services.data_analysis_service import DataAnalysisService
from services.database_service import DatabaseService
from services.file_processor import DatasetFileError, load_dataset
from services.speech_to_text import SpeechToTextService
from services.sql_generator import SQLValidationError, validate_sql


def test_csv_loading_normalizes_columns() -> None:
    frame, table = load_dataset("Students List.csv", b"Name,GPA Score\nSara,3.9\n")
    assert table == "students_list"
    assert list(frame.columns) == ["name", "gpa_score"]
    assert len(frame) == 1


def test_excel_loading() -> None:
    from io import BytesIO
    source = BytesIO()
    pd.DataFrame({"Name": ["Sara"]}).to_excel(source, index=False)
    frame, _ = load_dataset("students.xlsx", source.getvalue())
    assert frame.to_dict(orient="records") == [{"name": "Sara"}]


def test_empty_dataset_rejected() -> None:
    with pytest.raises(DatasetFileError):
        load_dataset("empty.csv", b"name,gpa\n")


def test_schema_and_readonly_execution(tmp_path: Path) -> None:
    database = DatabaseService(tmp_path)
    dataset_id = database.create_dataset(pd.DataFrame({"name": ["Sara", "Ahmed"], "gpa": [3.9, 3.2]}), "students")
    assert "Table: students" in database.get_schema(dataset_id)
    result = database.execute_readonly(dataset_id, "SELECT name, gpa FROM students ORDER BY gpa DESC")
    assert result["columns"] == ["name", "gpa"]
    assert result["rows"][0]["name"] == "Sara"


@pytest.mark.parametrize("sql", ["DELETE FROM students", "UPDATE students SET gpa = 4", "INSERT INTO students VALUES ('A')", "DROP TABLE students"])
def test_unsafe_sql_is_rejected(sql: str) -> None:
    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_select_sql_is_accepted() -> None:
    assert validate_sql("SELECT * FROM students;") == "SELECT * FROM students"


def test_text_analysis_pipeline_with_mocked_llm(tmp_path: Path) -> None:
    database = DatabaseService(tmp_path)
    dataset_id = database.create_dataset(pd.DataFrame({"department": ["Engineering", "Medicine"], "gpa": [3.9, 3.2]}), "students")

    class FakeSQL:
        def generate(self, query: str, schema: str) -> str:
            assert "students" in schema
            return "SELECT * FROM students ORDER BY gpa DESC"

    class FakeAnalysis:
        def analyze(self, query: str, result: dict) -> str:
            return f"Found {result['row_count']} students."

    service = DataAnalysisService(database=database, sql_generator=FakeSQL(), result_analyzer=FakeAnalysis())
    response = service.analyze_text(dataset_id, "Show top GPAs")
    assert response["generated_sql"].startswith("SELECT")
    assert response["rows"][0]["gpa"] == 3.9
    assert response["analysis"] == "Found 2 students."


def test_speech_service_reuses_mocked_model(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Segment:
        text = " average GPA "

    class Model:
        def transcribe(self, path: str, beam_size: int):
            return [Segment()], None

    SpeechToTextService._model = Model()
    audio = tmp_path / "question.wav"
    audio.write_bytes(b"not-a-real-audio-file")
    assert SpeechToTextService().transcribe(audio) == "average GPA"
