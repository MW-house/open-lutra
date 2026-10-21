"""App settings: where the recordings live and which recording config describes them."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_FILENAME = "config.yaml"
CONFIG_PATH_ENV = "DCM_CONFIG"


class ConfigError(Exception):
    """Raised when the app config is missing or malformed."""


@dataclass(frozen=True)
class AppConfig:
    output_dir: Path
    recording_config_path: Path


def resolve_config_path() -> Path:
    """Config path from $DCM_CONFIG, else config.yaml in the current directory."""
    env_path = os.environ.get(CONFIG_PATH_ENV)
    if env_path:
        return Path(env_path).expanduser()
    return Path.cwd() / DEFAULT_CONFIG_FILENAME


def load_app_config(path: Path) -> AppConfig:
    """Load the app config, resolving relative paths against the config file's directory."""
    if not path.is_file():
        raise ConfigError(
            f"Config file not found: {path}. Copy config.example.yaml to config.yaml, "
            f"or point {CONFIG_PATH_ENV} at your config file."
        )

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError(f"Config file must contain a YAML mapping: {path}")

    base = path.parent.resolve()
    return AppConfig(
        output_dir=_resolve_required_path(raw, "output_dir", base, path),
        recording_config_path=_resolve_required_path(raw, "recording_config_path", base, path),
    )


def _resolve_required_path(raw: dict, key: str, base: Path, config_path: Path) -> Path:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{key}' must be a non-empty string in {config_path}")

    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve()
