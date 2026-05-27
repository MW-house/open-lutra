"""Application-wide exception handlers."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.features.recording import AlreadyRecordingError, NotRecordingError, RecorderError


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(AlreadyRecordingError)
    async def _already_recording(_request: Request, exc: AlreadyRecordingError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(NotRecordingError)
    async def _not_recording(_request: Request, exc: NotRecordingError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(RecorderError)
    async def _recorder_error(_request: Request, exc: RecorderError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": str(exc)})
