"""Export merged or validated configs to various output formats."""

import json
import os
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


class ExportError(Exception):
    """Raised when an export operation fails."""


SUPPORTED_FORMATS = ("json", "yaml", "env")


def export_as_json(data: dict, indent: int = 2) -> str:
    """Serialize *data* to a JSON string."""
    try:
        return json.dumps(data, indent=indent, default=str)
    except (TypeError, ValueError) as exc:
        raise ExportError(f"JSON serialization failed: {exc}") from exc


def export_as_yaml(data: dict) -> str:
    """Serialize *data* to a YAML string."""
    if yaml is None:  # pragma: no cover
        raise ExportError("PyYAML is not installed")
    try:
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    except yaml.YAMLError as exc:
        raise ExportError(f"YAML serialization failed: {exc}") from exc


def _flatten(data: dict, prefix: str = "") -> dict:
    """Recursively flatten *data* into dot-separated key=value pairs."""
    items: dict = {}
    for key, value in data.items():
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            items.update(_flatten(value, prefix=full_key))
        else:
            items[full_key] = value
    return items


def export_as_env(data: dict) -> str:
    """Serialize *data* to a shell-compatible KEY=VALUE string."""
    flat = _flatten(data)
    lines = []
    for key, value in sorted(flat.items()):
        env_key = key.upper().replace(".", "_").replace("-", "_")
        lines.append(f"{env_key}={value}")
    return "\n".join(lines)


def export_config(data: dict, fmt: str) -> str:
    """Dispatch export to the correct serializer based on *fmt*."""
    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
    if fmt == "json":
        return export_as_json(data)
    if fmt == "yaml":
        return export_as_yaml(data)
    return export_as_env(data)


def write_export(content: str, output_path: str) -> None:
    """Write *content* to *output_path*, creating parent directories as needed."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(content)
        if not content.endswith("\n"):
            fh.write("\n")
