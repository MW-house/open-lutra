"""CLI entry point: `uv run data-collection-management`."""

from __future__ import annotations

import argparse
import os
import sys

import uvicorn

from .config import CONFIG_PATH_ENV, ConfigError, load_app_config, resolve_config_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Data collection management web app")
    parser.add_argument("--config", help="Path to config.yaml (default: ./config.yaml)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--reload", action="store_true", help="Reload on code changes")
    args = parser.parse_args()

    if args.config:
        os.environ[CONFIG_PATH_ENV] = args.config

    # Fail fast with a readable message instead of erroring on the first request.
    try:
        config = load_app_config(resolve_config_path())
    except ConfigError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"output_dir:            {config.output_dir}")
    print(f"recording_config_path: {config.recording_config_path}")
    print(f"listening on           http://{args.host}:{args.port}")
    uvicorn.run(
        "data_collection_management.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
