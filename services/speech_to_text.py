"""Lazy Faster-Whisper transcription service."""

from __future__ import annotations

from pathlib import Path

from config import settings


class SpeechToTextError(ValueError):
    """Raised when speech transcription fails."""


class SpeechToTextService:
    _model = None

    def _get_model(self):
        """
        Load the Whisper model only when it is first needed.
        """

        if self.__class__._model is None:
            try:
                from faster_whisper import WhisperModel

                self.__class__._model = WhisperModel(
                    settings.WHISPER_MODEL,
                    device=settings.WHISPER_DEVICE,
                    compute_type=settings.WHISPER_COMPUTE_TYPE,
                )

            except Exception as exc:
                raise SpeechToTextError(
                    "Speech transcription is unavailable. "
                    f"Check Faster-Whisper installation and model settings. "
                    f"Original error: {exc}"
                ) from exc

        return self.__class__._model

    def transcribe(self, audio_path: Path) -> str:
        """
        Convert an audio file into text.
        """

        if not audio_path.exists():
            raise SpeechToTextError(
                f"Audio file not found: {audio_path}"
            )

        try:
            segments, _ = self._get_model().transcribe(
                str(audio_path),
                beam_size=5,
                vad_filter=True,
            )

            text = " ".join(
                segment.text.strip()
                for segment in segments
            ).strip()

        except SpeechToTextError:
            raise

        except Exception as exc:
            raise SpeechToTextError(
                f"Audio transcription failed: {exc}"
            ) from exc

        if not text:
            raise SpeechToTextError(
                "No speech was detected in the audio."
            )

        return text


# Shared service instance
speech_to_text_service = SpeechToTextService()