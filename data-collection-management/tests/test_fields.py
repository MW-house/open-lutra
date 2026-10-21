from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from data_collection_management.config import ConfigError
from data_collection_management.fields import load_metadata_fields, option_display


def test_loads_fields_with_options(recording_config_path: Path) -> None:
    fields = load_metadata_fields(recording_config_path)

    assert [field.key for field in fields] == ["object", "operator_id", "task_evaluation"]
    assert fields[0].label == "対象物"
    assert fields[0].options[0].display == "A000_フェイスタオル"
    assert fields[1].type == "number"
    assert fields[1].options == ()


def test_display_for_falls_back_to_raw_value(recording_config_path: Path) -> None:
    field = load_metadata_fields(recording_config_path)[0]

    assert field.display_for("A001") == "A001_バスタオル"
    assert field.display_for("A999") == "A999"


@pytest.mark.parametrize(
    ("value", "label", "expected"),
    [
        ("A000", "A000_フェイスタオル", "A000_フェイスタオル"),
        ("A000", "フェイスタオル", "A000_フェイスタオル"),
        ("success", "成功", "success_成功"),
        ("A000", "A000", "A000"),
        ("A000", None, "A000"),
    ],
)
def test_option_display(value: str, label: str | None, expected: str) -> None:
    assert option_display(value, label) == expected


def test_config_without_metadata_fields_is_empty(tmp_path: Path) -> None:
    path = tmp_path / "no_fields.yaml"
    path.write_text(yaml.safe_dump({"topics": []}), encoding="utf-8")

    assert load_metadata_fields(path) == []


def test_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_metadata_fields(tmp_path / "absent.yaml")


def test_non_mapping_config_raises(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text(yaml.safe_dump(["not", "a", "mapping"]), encoding="utf-8")

    with pytest.raises(ConfigError, match="YAML mapping"):
        load_metadata_fields(path)


def test_invalid_metadata_fields_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump({"metadata_fields": "nope"}), encoding="utf-8")

    with pytest.raises(ConfigError):
        load_metadata_fields(path)
