"""FastAPI app: serves the aggregation UI and its JSON API."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .aggregate import build_summary
from .config import AppConfig, ConfigError, load_app_config, resolve_config_path
from .csv_report import build_daily_csv
from .fields import MetadataField, load_metadata_fields
from .models import SummaryOut
from .scanner import scan_recordings

STATIC_DIR = Path(__file__).parent / "static"


class SummaryRequest(BaseModel):
    # field key -> selected value ("" or absent means "no filter on this field").
    filters: dict[str, str] = {}
    # Inclusive recording-date range; null on either end leaves that end open.
    date_from: date | None = None
    date_to: date | None = None


def create_app(config: AppConfig | None = None) -> FastAPI:
    """Build the app. `config` is injected by tests; otherwise it is read on first use."""
    app = FastAPI(title="Data Collection Management")
    app.state.config = config

    @app.get("/api/config")
    def read_config() -> dict[str, str]:
        current = _config(app)
        return {
            "output_dir": str(current.output_dir),
            "recording_config_path": str(current.recording_config_path),
        }

    @app.post("/api/summary")
    def read_summary(request: SummaryRequest) -> SummaryOut:
        current = _config(app)
        return build_summary(
            recordings=scan_recordings(current.output_dir),
            fields=_metadata_fields(current),
            filters=request.filters,
            output_dir=str(current.output_dir),
            recording_config_path=str(current.recording_config_path),
            date_from=request.date_from,
            date_to=request.date_to,
        )

    @app.get("/api/daily-summary.csv")
    def download_daily_summary(
        target_date: Annotated[date | None, Query(alias="date")] = None,
    ) -> Response:
        """One day's aggregate as a CSV download; no `date` means today."""
        current = _config(app)
        target = target_date or date.today()
        body = build_daily_csv(
            recordings=scan_recordings(current.output_dir),
            fields=_metadata_fields(current),
            target_date=target,
        )
        return Response(
            # utf-8-sig: without the BOM Excel reads the Japanese headers as mojibake.
            content=body.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="summary_{target:%Y%m%d}.csv"'},
        )

    @app.get("/")
    def read_index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def _metadata_fields(config: AppConfig) -> list[MetadataField]:
    """The field master; a missing or malformed recording config is a client error."""
    try:
        return load_metadata_fields(config.recording_config_path)
    except ConfigError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _config(app: FastAPI) -> AppConfig:
    if app.state.config is None:
        try:
            app.state.config = load_app_config(resolve_config_path())
        except ConfigError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
    return app.state.config


app = create_app()
