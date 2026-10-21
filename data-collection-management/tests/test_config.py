from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from data_collection_management.config import (
    CONFIG_PATH_ENV,
    ConfigError,
    load_app_config,
    resolve_config_path,
)


def write_config(path: Path, raw: object) -> Path:
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return path


def test_resolves_relative_paths_against_config_dir(tmp_path: Path) -> None:
    (tmp_path / "output").mkdir()
    (tmp_path / "simulator.yaml").write_text("metadata_fields: []", encoding="utf-8")
    path = write_config(
        tmp_path / "config.yaml",
        {"output_dir": "output", "recording_config_path": "simulator.yaml"},
    )

    config = load_app_config(path)

    assert config.output_dir == (tmp_path / "output").resolve()
    assert config.recording_config_path == (tmp_path / "simulator.yaml").resolve()


def test_keeps_absolute_paths(tmp_path: Path) -> None:
    path = write_config(
        tmp_path / "config.yaml",
        {"output_dir": "/data/output", "recording_config_path": "/data/simulator.yaml"},
    )

    config = load_app_config(path)

    assert config.output_dir == Path("/data/output")


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_app_config(tmp_path / "absent.yaml")


@pytest.mark.parametrize(
    "raw",
    [
        ["not", "a", "mapping"],
        {"recording_config_path": "simulator.yaml"},
        {"output_dir": "", "recording_config_path": "simulator.yaml"},
        {"output_dir": 5, "recording_config_path": "simulator.yaml"},
    ],
)
def test_invalid_config_raises(tmp_path: Path, raw: object) -> None:
    path = write_config(tmp_path / "config.yaml", raw)

    with pytest.raises(ConfigError):
        load_app_config(path)


def test_config_path_prefers_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CONFIG_PATH_ENV, str(tmp_path / "custom.yaml"))
    assert resolve_config_path() == tmp_path / "custom.yaml"

    monkeypatch.delenv(CONFIG_PATH_ENV)
    monkeypatch.chdir(tmp_path)
    assert resolve_config_path() == tmp_path / "config.yaml"
