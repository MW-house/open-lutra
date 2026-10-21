from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from data_collection_management.app import create_app
from data_collection_management.config import CONFIG_PATH_ENV, AppConfig

from .conftest import write_recording


@pytest.fixture
def client(output_dir: Path, recording_config_path: Path) -> TestClient:
    return TestClient(
        create_app(AppConfig(output_dir=output_dir, recording_config_path=recording_config_path))
    )


def test_config_endpoint_reports_paths(
    client: TestClient, output_dir: Path, recording_config_path: Path
) -> None:
    payload = client.get("/api/config").json()

    assert payload == {
        "output_dir": str(output_dir),
        "recording_config_path": str(recording_config_path),
    }


def test_summary_endpoint_aggregates(client: TestClient) -> None:
    payload = client.post("/api/summary", json={"filters": {}}).json()

    assert payload["total_count"] == 3
    assert payload["total_duration_text"] == "1時間03分02秒"
    assert [field["key"] for field in payload["fields"]] == [
        "object",
        "operator_id",
        "task_evaluation",
    ]
    assert payload["field_summaries"][0]["groups"][0]["display"] == "A000_フェイスタオル"


def test_summary_endpoint_applies_a_date_range(client: TestClient, output_dir: Path) -> None:
    write_recording(output_dir / "20260725_100000", {"object": "A001"}, 10.0)

    payload = client.post(
        "/api/summary", json={"date_from": "2026-08-01", "date_to": "2026-08-01"}
    ).json()

    assert payload["total_count"] == 3
    assert payload["date_from"] == "2026-08-01"


def test_summary_endpoint_rejects_a_malformed_date(client: TestClient) -> None:
    response = client.post("/api/summary", json={"date_from": "yesterday"})

    assert response.status_code == 422


def test_summary_endpoint_reports_evaluation_totals(client: TestClient) -> None:
    payload = client.post("/api/summary", json={}).json()

    assert [(item["value"], item["count"]) for item in payload["evaluation_totals"]] == [
        ("success", 2),
        ("failure", 1),
    ]


def test_summary_endpoint_applies_filters(client: TestClient) -> None:
    payload = client.post("/api/summary", json={"filters": {"object": "A001"}}).json()

    assert payload["total_count"] == 2
    assert len(payload["recordings"]) == 2


def test_summary_endpoint_reports_broken_recording_config(output_dir: Path, tmp_path: Path) -> None:
    client = TestClient(
        create_app(AppConfig(output_dir=output_dir, recording_config_path=tmp_path / "absent.yaml"))
    )

    response = client.post("/api/summary", json={"filters": {}})

    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_daily_summary_endpoint_downloads_the_requested_date(
    client: TestClient, output_dir: Path
) -> None:
    write_recording(
        output_dir / "20260725_100000", {"operator_id": "007", "task_evaluation": "success"}, 10.0
    )

    response = client.get("/api/daily-summary.csv", params={"date": "2026-07-25"})

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="summary_20260725.csv"'
    # The BOM keeps Excel from rendering the Japanese headers as mojibake.
    assert response.content.startswith(b"\xef\xbb\xbf")
    rows = response.content.decode("utf-8-sig").strip().split("\r\n")
    # One column per field the master declares, headed by its key and in declaration
    # order; task_evaluation feeds the metric pairs instead of becoming a column.
    assert rows[0] == "日付,object,operator_id,成功件数,成功時間,失敗件数,失敗時間"
    assert rows[1] == "2026/7/25,未設定,007,1,0:00:10,0,0:00:00"


def test_daily_summary_endpoint_defaults_to_today(client: TestClient, output_dir: Path) -> None:
    today = date.today()
    write_recording(
        output_dir / today.strftime("%Y%m%d_%H%M%S"),
        {"operator_id": "007", "task_evaluation": "failure"},
        20.0,
    )

    response = client.get("/api/daily-summary.csv")

    rows = response.content.decode("utf-8-sig").strip().split("\r\n")
    assert response.headers["content-disposition"].endswith(f'summary_{today:%Y%m%d}.csv"')
    expected_date = f"{today.year}/{today.month}/{today.day}"
    assert rows[1] == f"{expected_date},未設定,007,0,0:00:00,1,0:00:20"


def test_daily_summary_endpoint_rejects_a_malformed_date(client: TestClient) -> None:
    response = client.get("/api/daily-summary.csv", params={"date": "yesterday"})

    assert response.status_code == 422


def test_index_is_served(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "収録データ集計" in response.text


def test_missing_app_config_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CONFIG_PATH_ENV, str(tmp_path / "absent.yaml"))
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/api/config")

    assert response.status_code == 500
