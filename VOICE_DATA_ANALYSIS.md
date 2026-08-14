# Voice Data Analysis

The existing Code Assistant remains available in the first Streamlit tab. The second tab adds isolated dataset analysis for CSV, XLSX, and XLS files.

## Run

Install dependencies and start the existing services:

```bash
pip install -r requirements.txt
uvicorn app:app --reload
streamlit run frontend/streamlit_app.py
```

Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`. Voice analysis additionally uses `WHISPER_MODEL` (default `base`), `WHISPER_DEVICE` (default `cpu`), and `WHISPER_COMPUTE_TYPE` (default `int8`). Dataset and temporary-audio locations, result limit, and upload limit are configurable through the remaining data settings in `.env.example`.

## API

- `GET /data/health`
- `POST /data/upload` — multipart field `file`
- `POST /data/analyze/text` — JSON `{"dataset_id": "...", "query": "..."}`
- `POST /data/analyze/voice` — multipart fields `dataset_id` and `audio`

Uploads are placed into a unique SQLite database. Each text question gets the actual schema, generates SQLite SQL with the existing OpenRouter client, validates a single read-only `SELECT`/`WITH` statement, and runs it using SQLite read-only mode. Results are capped at `MAX_QUERY_ROWS` and summarized using bounded statistics plus the shared LLM client. Voice uploads are transcribed once by a lazy, reused Faster-Whisper model before entering the exact same text-analysis pipeline.

## Test

```bash
python -m pytest -q
```

The new tests mock LLM and speech-model behavior, so they do not require an OpenRouter call or model download.
