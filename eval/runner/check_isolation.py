"""Historical preflight probe, superseded by the user's access-audit decision.

This diagnostic reads a private grader file but never prints its contents.
Exit 1 means STOP-E4: the built-in workspace sandbox can read the grader.
Exit 2 means the probe could not establish isolation. The original fixture has
since moved outside the repository, so this script is retained as historical
source only. Use eval.runner.audit for current evaluation validity checks.
"""

from pathlib import Path
import subprocess
import sys


def main() -> int:
    """Probe the installed diagnostic CLI's built-in workspace profile."""
    task = Path(__file__).resolve().parents[1] / "tasks/bug-chunk-tail"
    hidden = task / "hidden_tests/test_chunking.py"
    command = [
        "codex", "sandbox", "-P", ":workspace",
        "-C", str(task / "workspace"), sys.executable, "-I", "-c",
        "import pathlib, sys; data = pathlib.Path(sys.argv[1]).read_bytes(); "
        "print('HIDDEN_GRADER_READABLE' if data else 'EMPTY_GRADER')",
        str(hidden),
    ]
    try:
        version = subprocess.run(
            ["codex", "--version"], capture_output=True, text=True, timeout=10, check=True,
        )
        print(version.stdout.strip())
        print("Diagnostic profile: :workspace (exec --sandbox workspace-write not invoked)")
        print(f"Workspace: {task / 'workspace'}")
        print(f"Private grader outside workspace: {hidden}")
        result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Probe error: {exc}", file=sys.stderr)
        return 2
    print(f"Sandbox process exit: {result.returncode}")
    print(result.stdout.strip())
    if result.returncode == 0 and result.stdout.strip() == "HIDDEN_GRADER_READABLE":
        print("STOP-E4: :workspace permits reading the private grader by absolute path.")
        return 1
    print(result.stderr.strip(), file=sys.stderr)
    print("Isolation unproven; a failed process alone does not establish a read-deny boundary.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
