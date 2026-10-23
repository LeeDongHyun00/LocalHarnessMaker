"""Preflight human-authored baseline C guidance without model calls."""

from pathlib import Path
from typing import Any
from eval.runner.publication import safe_source

PLACEHOLDER = "__HUMAN_FILL__"


def load_templates(config: dict[str, Any], repository: Path) -> dict[str, bytes]:
    """Read every selected template before execution; retain these exact bytes."""
    if "static_template_dir" not in config:
        return {}
    directory = Path(config["static_template_dir"])
    if not directory.is_absolute():
        directory = repository / directory
    templates = {}
    for task in config["tasks"]:
        path = directory / f"{task}.md"
        if not safe_source(path, directory) or not path.is_file():
            raise ValueError(f"Missing or linked static template for {task}")
        content = path.read_bytes()
        if not content.strip() or PLACEHOLDER in content.decode("utf-8"):
            raise ValueError(f"Unfilled static template for {task}")
        templates[task] = content
    return templates
