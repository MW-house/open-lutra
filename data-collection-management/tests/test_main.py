from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from data_collection_management import __main__


@pytest.fixture
def app_config_path(tmp_path: Path, recording_config_path: Path, output_dir: Path) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "output_dir": str(output_dir),
                "recording_config_path": str(recording_config_path),
            }
        ),
        encoding="utf-8",
    )
    return path


def test_main_starts_the_server(
    app_config_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    started: dict[str, object] = {}
    monkeypatch.setattr(__main__.uvicorn, "run", lambda target, **kwargs: started.update(kwargs))
    monkeypatch.setattr("sys.argv", ["dcm", "--config", str(app_config_path), "--port", "9999"])

    assert __main__.main() == 0
    assert started["port"] == 9999
    assert "listening on" in capsys.readouterr().out


def test_main_reports_a_missing_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["dcm", "--config", str(tmp_path / "absent.yaml")])

    assert __main__.main() == 1
    assert "error:" in capsys.readouterr().err
