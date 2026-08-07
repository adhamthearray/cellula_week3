import logging
from pathlib import Path

from config import settings


settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("ai_code_assistant")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_handler = logging.FileHandler(settings.LOG_DIR / "app.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(stream_handler)
