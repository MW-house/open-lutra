"""Registry and discovery for custom validators.

Builtin validators are instantiated in `active_set.py`. This module owns
the registration and lookup of user-defined validators placed under the
`custom/` package.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.features.validation.base import RecordingValidator

logger = logging.getLogger(__name__)

# Registered custom validator classes, in the order @register_validator was
# applied. Instantiation happens when the runner executes them.
_custom_validator_classes: list[type[RecordingValidator]] = []

DEFAULT_CUSTOM_PACKAGE = "app.features.validation.custom"


def register_validator(cls: type[RecordingValidator]) -> type[RecordingValidator]:
    """Decorator that registers a custom validator class.

    Raises ValueError if the class does not declare a `name` attribute.
    Duplicate names are allowed (with a warning log); the UI can still
    distinguish them via source_module.
    """
    name = getattr(cls, "name", None)
    if not name:
        raise ValueError(f"{cls.__name__} must declare a 'name' class variable")

    if any(existing.name == name for existing in _custom_validator_classes):
        logger.warning(
            "A custom validator with the same name is already registered (name=%s): %s",
            name,
            cls.__module__,
        )

    _custom_validator_classes.append(cls)
    return cls


def get_custom_validators() -> list[RecordingValidator]:
    """Return fresh instances of every registered custom validator."""
    return [cls() for cls in _custom_validator_classes]


def clear_registry() -> None:
    """Empty the registry (intended for tests)."""
    _custom_validator_classes.clear()


def load_custom_validators(package: str = DEFAULT_CUSTOM_PACKAGE) -> None:
    """Import every `.py` module under the given package so decorators run.

    An import error in any single module is logged at WARNING and skipped;
    other modules continue to load. Call this once at application startup.

    Args:
        package: Python package to walk. Tests may pass a different package.
    """
    try:
        pkg = importlib.import_module(package)
    except Exception as e:
        logger.warning("Failed to load custom validator package: %s - %s", package, e)
        return

    pkg_path = getattr(pkg, "__path__", None)
    if pkg_path is None:
        logger.warning("Custom validator package has no __path__: %s", package)
        return

    for _, module_name, _ in pkgutil.iter_modules(pkg_path):
        full_name = f"{package}.{module_name}"
        try:
            importlib.import_module(full_name)
            logger.info("Loaded custom validator module: %s", full_name)
        except Exception as e:
            logger.warning("Failed to load custom validator module: %s - %s", full_name, e)
