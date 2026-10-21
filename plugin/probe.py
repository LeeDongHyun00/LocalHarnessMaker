"""Prepare an isolated, reproducible Codex hook compatibility experiment."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable


PROMPT = (
    "This is a hook compatibility experiment. Reply with the two exact markers "
    "supplied in extra context, then FIRST_REPLY. Do not use tools or change files. "
    "If later asked to print one more line, reply only SECOND_REPLY."
)


def prepare(output_dir: Path, run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> dict[str, object]:
    """Create fresh config/workspace outside the repository, without copying secrets."""
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise ValueError("use a new evidence directory for each run")
    output_dir.mkdir(parents=True)
    version = run(["codex", "--version"], text=True, capture_output=True, check=True).stdout.strip()
    pin = Path(__file__).with_name("CODEX_VERSION").read_text().strip()
    if version != pin:
        raise ValueError(f"Codex version mismatch: expected {pin}; found {version}")
    sandbox_dir = Path(tempfile.mkdtemp(prefix="harness-hook-probe-"))
    config_home = sandbox_dir / "codex-home"
    workspace = sandbox_dir / "workspace"
    config_home.mkdir()
    workspace.mkdir()
    # Reuse existing local login via a symlink outside the repo; never read credentials.
    auth_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth_path = auth_home / "auth.json"
    if auth_path.is_file():
        (config_home / "auth.json").symlink_to(auth_path)
    config = (
        'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "low"\n'
        'approval_policy = "never"\nsandbox_mode = "read-only"\n'
        '[features]\nhooks = true\nmulti_agent = false\n'
        'skip_host_skill_discovery = true\n'
        f'[projects.{json.dumps(str(workspace))}]\ntrust_level = "trusted"\n'
    )
    (config_home / "config.toml").write_text(config, encoding="utf-8")
    script = Path(__file__).with_name("hooks") / "probe.py"
    command = shlex.join([sys.executable, str(script.resolve())])
    hooks = {"hooks": {event: [{"hooks": [{
        "type": "command", "command": command, "timeout": 5,
    }]}] for event in ("SessionStart", "UserPromptSubmit", "Stop")}}
    (config_home / "hooks.json").write_text(json.dumps(hooks, indent=2) + "\n")
    (output_dir / "hooks.json").write_text(json.dumps(hooks, indent=2) + "\n")
    metadata: dict[str, object] = {
        "version": version, "codex_home": str(config_home), "workspace": str(workspace),
        "evidence_dir": str(output_dir), "prompt": PROMPT,
        "auth": "existing auth.json symlink outside repository" if auth_path.is_file() else "environment/default",
    }
    (output_dir / "experiment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main() -> int:
    """Prepare a probe and print a shell-quoted launch command for the chosen mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("exec", "tui"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    metadata = prepare(args.out)
    base = [shutil.which("codex") or "codex", "--no-daemon", "--dangerously-bypass-hook-trust"]
    if args.mode == "exec":
        base += ["exec", "--skip-git-repo-check", "--json", "--color", "never"]
    else:
        base += ["--no-alt-screen"]
    base += ["-C", str(metadata["workspace"]), PROMPT]
    env = ["env", f"CODEX_HOME={metadata['codex_home']}",
           f"HARNESS_PROBE_DIR={Path(str(metadata['evidence_dir'])) / 'hooks'}"]
    print(shlex.join(env + base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
