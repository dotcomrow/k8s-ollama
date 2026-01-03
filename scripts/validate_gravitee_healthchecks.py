#!/usr/bin/env python3
"""
Validate Gravitee service annotations for required health checks.

Default behavior:
- Inspect YAML manifests under the provided paths (default: manifests/).
- For Service resources with gravitee.io/expose == "true", require a valid
  gravitee.io/definition-endpoint-groups annotation that includes a health check
  with enabled=true and configuration.schedule + configuration.target.
- Allow opt-out per Service via gravitee.io/healthcheck-required == "false".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:
    print("Missing dependency: pyyaml. Install with `pip install pyyaml`.", file=sys.stderr)
    raise SystemExit(2) from exc


def iter_yaml_files(paths: Iterable[Path]) -> Iterable[Path]:
    for base in paths:
        if base.is_file() and base.suffix in {".yml", ".yaml"}:
            yield base
            continue
        if base.is_dir():
            for path in base.rglob("*.yml"):
                yield path
            for path in base.rglob("*.yaml"):
                yield path


def is_true(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def load_yaml_docs(path: Path) -> Iterable[dict]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"{path}: failed to read file: {exc}") from exc
    try:
        for doc in yaml.safe_load_all(content):
            if isinstance(doc, dict):
                yield doc
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: invalid YAML: {exc}") from exc


def parse_endpoint_groups(raw: str, path: Path) -> list[dict]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: gravitee.io/definition-endpoint-groups is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{path}: gravitee.io/definition-endpoint-groups must be a JSON array")
    return data


def validate_service(doc: dict, path: Path, errors: list[str]) -> None:
    if doc.get("kind") != "Service":
        return
    metadata = doc.get("metadata") or {}
    annotations = metadata.get("annotations") or {}
    if not is_true(annotations.get("gravitee.io/expose", "false")):
        return
    if is_true(annotations.get("gravitee.io/healthcheck-required", "true")) is False:
        return

    raw_groups = annotations.get("gravitee.io/definition-endpoint-groups")
    if not raw_groups:
        errors.append(f"{path}: missing gravitee.io/definition-endpoint-groups for exposed service")
        return

    groups = parse_endpoint_groups(raw_groups, path)
    if not groups:
        errors.append(f"{path}: gravitee.io/definition-endpoint-groups is empty")
        return

    for index, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            errors.append(f"{path}: endpoint group #{index} is not an object")
            continue
        services = group.get("services") or {}
        health = services.get("healthCheck") or services.get("health-check")
        if not isinstance(health, dict):
            errors.append(f"{path}: endpoint group #{index} missing services.healthCheck")
            continue
        if not is_true(health.get("enabled", "false")):
            errors.append(f"{path}: endpoint group #{index} healthCheck.enabled is not true")
            continue
        config = health.get("configuration") or {}
        if not isinstance(config, dict):
            errors.append(f"{path}: endpoint group #{index} healthCheck.configuration is not an object")
            continue
        if not config.get("schedule"):
            errors.append(f"{path}: endpoint group #{index} healthCheck.configuration.schedule is missing")
        if not config.get("target"):
            errors.append(f"{path}: endpoint group #{index} healthCheck.configuration.target is missing")


def main() -> int:
    args = [Path(p) for p in sys.argv[1:]] or [Path("manifests")]
    yaml_files = list(iter_yaml_files(args))
    if not yaml_files:
        print("No YAML files found to validate.", file=sys.stderr)
        return 0

    errors: list[str] = []
    for path in sorted(set(yaml_files)):
        for doc in load_yaml_docs(path):
            validate_service(doc, path, errors)

    if errors:
        print("Gravitee health check validation failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print("Gravitee health check validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
