"""Protect collection of role suites with duplicate test module names."""

from pathlib import Path
import shlex
import tomllib


def test_role_suites_use_importlib_collection() -> None:
    root = Path(__file__).resolve().parents[2]
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    options = config["tool"]["pytest"]["ini_options"]
    assert "--import-mode=importlib" in shlex.split(options["addopts"])
    assert options["testpaths"] == [
        "tests/lead", "tests/plugin", "tests/controller", "tests/verifier", "tests/eval",
    ]
