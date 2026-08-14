"""HTTP endpoints for uploaded-dataset text and voice analysis."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from config import settings
from models.schemas import (
    DataAnalysisResponse,
    DatasetUploadResponse,
    TextAnalysisRequest,
)
from services.data_analysis_service import DataAnalysisService
from services.database_service import (
    DatabaseService,
    DatasetNotFoundError,
)
from services.file_processor import (
    DatasetFileError,
    load_dataset,
)
from services.speech_to_text import (
    SpeechToTextError,
    speech_to_text_service,
)
from services.sql_generator import SQLValidationError


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/data",
    tags=["Voice Data Analysis"],
)


# ============================================================
# SERVICES
# ============================================================

database = DatabaseService()

analysis_service = DataAnalysisService(
    database=database
)


# ============================================================
# ERROR HANDLER
# ============================================================

def _client_error(exc: Exception) -> HTTPException:
    """
    Convert expected application errors into HTTP errors.
    """

    status_code = (
        404
        if isinstance(exc, DatasetNotFoundError)
        else 400
    )

    return HTTPException(
        status_code=status_code,
        detail=str(exc),
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "OK"
    }


# ============================================================
# UPLOAD DATASET
# ============================================================

@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
)
async def upload_dataset(
    file: UploadFile = File(...)
) -> DatasetUploadResponse:

    content = await file.read()

    # Check file size
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                "Dataset exceeds the configured "
                "upload size limit."
            ),
        )

    # Get safe filename
    filename = Path(
        file.filename or "dataset"
    ).name

    try:

        # Load CSV / Excel
        frame, table_name = load_dataset(
            filename,
            content,
        )

        # Store dataset
        dataset_id = database.create_dataset(
            frame,
            table_name,
        )

        return DatasetUploadResponse(
            dataset_id=dataset_id,
            filename=filename,
            table_name=table_name,
            rows=len(frame),
            columns=list(frame.columns),
        )

    except DatasetFileError as exc:
        raise _client_error(exc) from exc


# ============================================================
# ANALYZE TEXT
# ============================================================

@router.post(
    "/analyze/text",
    response_model=DataAnalysisResponse,
)
def analyze_text(
    request: TextAnalysisRequest
) -> DataAnalysisResponse:

    try:

        result = analysis_service.analyze_text(
            request.dataset_id,
            request.query,
        )

        return DataAnalysisResponse(
            **result
        )

    except (
        DatasetNotFoundError,
        SQLValidationError,
        ValueError,
    ) as exc:

        raise _client_error(exc) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Data analysis could not be completed."
            ),
        ) from exc


# ============================================================
# ANALYZE VOICE
# ============================================================

@router.post(
    "/analyze/voice",
    response_model=DataAnalysisResponse,
)
async def analyze_voice(

    # Comes from multipart/form-data
    dataset_id: str = Form(...),

    # Recorded/uploaded audio
    audio: UploadFile = File(...),

) -> DataAnalysisResponse:

    # --------------------------------------------------------
    # GET AUDIO FILE EXTENSION
    # --------------------------------------------------------

    suffix = Path(
        audio.filename or ""
    ).suffix.lower()

    # Default if the browser does not provide an extension
    if not suffix:
        suffix = ".wav"

    # --------------------------------------------------------
    # VALIDATE AUDIO TYPE
    # --------------------------------------------------------

    allowed_extensions = {
        ".wav",
        ".mp3",
        ".m4a",
        ".mp4",
        ".ogg",
        ".flac",
        ".webm",
    }

    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {suffix}",
        )

    # --------------------------------------------------------
    # READ AUDIO
    # --------------------------------------------------------

    content = await audio.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The audio file is empty.",
        )

    # --------------------------------------------------------
    # CREATE TEMP AUDIO DIRECTORY
    # --------------------------------------------------------

    settings.AUDIO_STORAGE_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Create unique temporary filename
    path = (
        settings.AUDIO_STORAGE_PATH
        / f"{uuid.uuid4().hex}{suffix}"
    )

    try:

        # ----------------------------------------------------
        # SAVE AUDIO TEMPORARILY
        # ----------------------------------------------------

        path.write_bytes(content)

        # ----------------------------------------------------
        # SPEECH -> TEXT
        # ----------------------------------------------------

        transcription = (
            speech_to_text_service.transcribe(path)
        )

        # ----------------------------------------------------
        # ANALYZE TRANSCRIBED QUESTION
        # ----------------------------------------------------

        response = analysis_service.analyze_text(
            dataset_id,
            transcription,
        )

        # Add transcription to the response
        response["transcription"] = transcription

        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return DataAnalysisResponse(
            **response
        )

    except (
        DatasetNotFoundError,
        SpeechToTextError,
        SQLValidationError,
        ValueError,
    ) as exc:

        raise _client_error(exc) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Voice data analysis could not "
                "be completed."
            ),
        ) from exc

    finally:

        # ----------------------------------------------------
        # DELETE TEMPORARY AUDIO FILE
        # ----------------------------------------------------

        path.unlink(
            missing_ok=True
        )