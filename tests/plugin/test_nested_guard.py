"""The exact nested guard precedes all hook imports, I/O, and logging."""

from __future__ import annotations

import builtins
import io
import os
from pathlib import Path
import subprocess
import sys

import pytest


DIRECTORY = Path(__file__).resolve().parents[2] / "plugin/hooks"
HOOKS = sorted(p for p in DIRECTORY.glob("*.py") if not p.name.startswith("_"))


@pytest.mark.parametrize("hook", HOOKS, ids=lambda p: p.stem)
@pytest.mark.parametrize("stub", ["0", "1"])
def test_nested_guard_exits_with_open_stdin(hook: Path, stub: str, tmp_path: Path) -> None:
    evidence = tmp_path / "not-created"
    child = subprocess.Popen(
        [sys.executable, str(hook)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, cwd=tmp_path,
        env={**os.environ, "HARNESS_NESTED": "1", "HARNESS_STUB": stub,
             "HARNESS_EVENT_LOG": str(evidence), "HARNESS_PROBE_DIR": str(evidence)},
    )
    try:
        # Do not close stdin: any attempt to read input would block.
        assert child.wait(timeout=2) == 0
        stdout, stderr = child.communicate()
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate()
    assert stdout == stderr == b""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("hook", HOOKS, ids=lambda p: p.stem)
def test_nested_guard_precedes_poisoned_import_io_and_processes(
    hook: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    compiled = compile(hook.read_text(), str(hook), "exec")
    stdout, stderr = io.StringIO(), io.StringIO()
    original_import = builtins.__import__
    calls: list[str] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append("forbidden I/O or subprocess")
        raise AssertionError("nested hook performed work")

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name != "os":
            calls.append("import " + name)
            raise AssertionError("nested hook imported runtime code")
        return original_import(name, *args, **kwargs)

    class Unreadable:
        def read(self, *args: object, **kwargs: object) -> None:
            forbidden()

    with monkeypatch.context() as patch:
        patch.setenv("HARNESS_NESTED", "1")
        patch.setenv("HARNESS_STUB", "1")
        patch.setattr(sys, "stdin", Unreadable())
        patch.setattr(sys, "stdout", stdout)
        patch.setattr(sys, "stderr", stderr)
        patch.setattr(builtins, "open", forbidden)
        patch.setattr(Path, "open", forbidden)
        patch.setattr(Path, "mkdir", forbidden)
        patch.setattr(subprocess, "run", forbidden)
        patch.setattr(subprocess, "Popen", forbidden)
        patch.setattr(builtins, "__import__", guarded_import)
        try:
            exec(compiled, {"__name__": "__main__", "__file__": str(hook)})
        except SystemExit as exc:
            code = exc.code
        else:
            code = None
    assert code == 0
    assert calls == []
    assert stdout.getvalue() == stderr.getvalue() == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("hook", HOOKS, ids=lambda p: p.stem)
@pytest.mark.parametrize("value", [None, "", "0", "true", "01"])
def test_other_guard_values_preserve_normal_path(hook: Path, value: str | None, tmp_path: Path) -> None:
    env = {**os.environ, "HARNESS_PROBE_DIR": str(tmp_path)}
    env.pop("HARNESS_NESTED", None)
    if value is not None:
        env["HARNESS_NESTED"] = value
    result = subprocess.run([sys.executable, str(hook)], input="malformed JSON", text=True,
                            capture_output=True, env=env, timeout=5, check=False)
    assert result.returncode == 0
    assert result.stdout == ""
    assert "warning:" in result.stderr
    assert "elapsed_seconds=" in result.stderr
