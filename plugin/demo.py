"""Run the D-2 fixture loop in an isolated Codex session, preserving real logs."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from plugin.versions import validate_version

from plugin.hooks._runtime import run_group, seconds
from plugin.hooks._config import validate_settings
from plugin.install import configuration, resolve_codex


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"
Runner = Callable[..., subprocess.CompletedProcess[str]]
REAL_PROMPT = ("Create result.txt containing exactly ok followed by a newline. "
               "Verify its exact contents with Python. This is the whole task. "
               "Display the injected contract and wait for approval before writing.")
PROMPT = (
    "This is an isolated HARNESS_STUB demonstration of contract approval and hook routing. "
    "The injected FastAPI contract and verifier verdicts are unchanged synthetic fixtures. "
    "Do not implement the endpoint or edit application files. First display the contract's "
    "goal, checklist, assumptions, effort and cost, then wait for approve. This empty "
    "workspace has no application or test dependencies, meeting the fixture's stop "
    "condition. This is a routing-only simulation: do not use tools or run fixture "
    "commands against the nonexistent app. After approval, report all real criteria as "
    "not done and label fixture evidence SYNTHETIC. When Stop supplies its one "
    "re-instruction, report only unmet criteria as not done; do not edit files or pretend "
    "the task succeeded. Task being simulated: Add and test GET /health in an existing FastAPI app."
)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")



def workspace_files(workspace: Path) -> dict[str, dict[str, str]]:
    """Inventory task entries without following symlinks or counting harness metadata."""
    entries: dict[str, dict[str, str]] = {}
    metadata = {"state.json", "session.json", "request.txt", "contract.json", "verdict.json", "handoff.json"}
    for directory, subdirs, files in os.walk(workspace, followlinks=False):
        parent = Path(directory)
        directory_names = list(subdirs)
        if parent == workspace:
            # Walk .harness to detect unexpected task files, but omit its managed
            # directory entry. Symlink replacements remain visible to the audit.
            directory_names = [name for name in directory_names
                               if name != ".harness" or (parent / name).is_symlink()]
            files = [name for name in files if name != ".local-harness-maker"]
        if parent == workspace / ".harness":
            files = [name for name in files if name not in metadata
                     and not name.startswith(("session.bad.", "handoff.pending.", "handoff.stale."))
                     and not (name.startswith(".") and name.endswith(".tmp"))]
        for name in [*directory_names, *files]:
            path = parent / name
            relative = str(path.relative_to(workspace))
            if path.is_symlink():
                entries[relative] = {"type": "symlink", "target": os.readlink(path)}
            elif path.is_dir():
                entries[relative] = {"type": "directory"}
            else:
                entries[relative] = {"type": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return entries

def prepare(out: Path, run: Runner = run_group, mode: str = "stub",
            executable: str | None = None) -> dict[str, Any]:
    """Register only reviewed harness hooks in a temporary home/workspace."""
    if out.exists():
        raise ValueError("use a new output directory; evidence is never overwritten")
    if mode not in {"real", "stub"}:
        raise ValueError("unsupported demo mode")
    validate_settings()
    executable = executable or resolve_codex()
    if executable is None:
        raise ValueError("Codex CLI not found")
    hooks = configuration(ROOT, executable)
    result = run([executable, "--version"], capture_output=True, text=True, check=False, timeout=5, shell=False,
                  env={**os.environ, "HARNESS_NESTED": "1"})
    if result.returncode != 0:
        raise ValueError("Codex version probe failed")
    version = validate_version(result.stdout.strip())
    out.mkdir(parents=True)
    temporary = Path(tempfile.mkdtemp(prefix="harness-d2-"))
    home, workspace = temporary / "codex-home", temporary / "workspace"
    home.mkdir()
    (temporary / "home").mkdir()
    workspace.mkdir()
    (workspace / ".local-harness-maker").write_text("LocalHarnessMaker project opt-in v1\n")
    write_json(out / "initial-workspace.json", {"files": workspace_files(workspace)})
    existing_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth = existing_home / "auth.json"
    if auth.is_file():
        # Reuse CLI login by reference outside the repo, never read/copy credential content.
        (home / "auth.json").symlink_to(auth)
    (home / "config.toml").write_text(
        'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "low"\n'
        f'approval_policy = "never"\nsandbox_mode = "{"workspace-write" if mode == "real" else "read-only"}"\n'
        '[features]\nhooks = true\nmulti_agent = false\n'
        'skip_host_skill_discovery = true\n'
        f'[projects.{json.dumps(str(workspace))}]\ntrust_level = "trusted"\n',
        encoding="utf-8",
    )
    write_json(home / "hooks.json", hooks)
    write_json(out / "hooks.json", hooks)
    metadata = {"version": version, "workspace": str(workspace), "codex_home": str(home),
                "out": str(out), "codex": executable, "mode": mode, "executor": "gpt-6.1-sol", "prompt": REAL_PROMPT if mode == "real" else PROMPT,
                "approval": "pending", "real_task_verified": False,
                "max_attempts": int(os.environ.get("HARNESS_MAX_ATTEMPTS", "3"))}
    write_json(out / "experiment.json", metadata)
    return metadata


def launch(metadata: dict[str, Any], stage: str, run: Runner = run_group,
           extra_env: dict[str, str] | None = None) -> None:
    """Launch exactly one executor process per stage; hooks own verification."""
    out = Path(metadata["out"])
    child_env = dict(os.environ)
    child_env['HARNESS_INTERFACE_VERSION'] = '2'
    # This is a direct-user hook demo, unlike the independent evaluation runner.
    child_env.pop("HARNESS_NESTED", None)
    child_env.update(CODEX_HOME=metadata["codex_home"],
                     HOME=str(Path(metadata["codex_home"]).parent / "home"), HARNESS_STUB="1",
                     HARNESS_PYTHON=sys.executable, HARNESS_EVENT_LOG=str(out / "hooks.jsonl"),
                     PLUGIN_ROOT=str(PLUGIN))
    if metadata.get("mode") == "real":
        child_env.pop("HARNESS_STUB", None)
        child_env["HARNESS_BACKEND"] = "codex_cli"
    child_env.update(extra_env or {})
    command = [metadata.get("codex", "codex"), "--no-daemon", "--dangerously-bypass-hook-trust", "exec"]
    if stage == "approval":
        command += ["resume", metadata["thread_id"]]
    command += ["--skip-git-repo-check", "--json", "--output-last-message", str(out / f"{stage}-reply.txt"), "-"]
    prompt = metadata.get("prompt", PROMPT) if stage == "request" else "approve"
    attempts = int(os.environ.get("HARNESS_MAX_ATTEMPTS", "3"))
    if attempts < 1:
        raise ValueError("HARNESS_MAX_ATTEMPTS must be at least 1")
    # The demo caller also outlasts every possible Stop cycle, including stubs.
    deadline = max(2400, attempts * seconds("HARNESS_STOP_TIMEOUT", 660)
                   + seconds("HARNESS_USERPROMPTSUBMIT_TIMEOUT", 40)
                   + seconds("HARNESS_SESSIONSTART_TIMEOUT", 10) + 300)
    try:
        result = run(command, input=prompt, cwd=metadata["workspace"], env=child_env,
                     text=True, capture_output=True, timeout=deadline, shell=False, check=False)
    except subprocess.TimeoutExpired as exc:
        # Preserve diagnostic fragments without treating a partial stream as success.
        for name, value in (("events.jsonl", exc.stdout), ("stderr.log", exc.stderr)):
            if value is not None:
                (out / f"{stage}-{name}").write_bytes(value.encode() if isinstance(value, str) else value)
        write_json(out / f"{stage}-result.json", {"command": command, "exit_code": 124})
        raise
    (out / f"{stage}-events.jsonl").write_text(result.stdout, encoding="utf-8")
    (out / f"{stage}-stderr.log").write_text(result.stderr, encoding="utf-8")
    write_json(out / f"{stage}-result.json", {"command": command, "exit_code": result.returncode})
    if result.returncode != 0:
        raise RuntimeError(f"demo {stage} exited {result.returncode}; see retained stderr")
    for line in result.stdout.splitlines():
        record = json.loads(line)
        if record.get("type") == "thread.started":
            metadata["thread_id"] = record["thread_id"]
    if "thread_id" not in metadata:
        raise ValueError("Codex did not report a thread id")
    write_json(out / "experiment.json", metadata)


def collect(metadata: dict[str, Any], stage: str) -> dict[str, Any]:
    """Save actual runtime state/transcript and check the requested demo stage."""
    out, workspace = Path(metadata["out"]), Path(metadata["workspace"])
    events = [json.loads(line) for line in (out / "hooks.jsonl").read_text().splitlines()]
    if any(event["error"] is not None for event in events):
        raise ValueError("a lifecycle hook failed; see hooks.jsonl")
    submitted = [e for e in events if e["event"] == "UserPromptSubmit" and e["output"]]
    real = metadata.get("mode") == "real"
    contract_text = (workspace / ".harness/contract.json").read_text() if real else (ROOT / "schemas/examples/contract.json").read_text()
    context = submitted[0]["output"]["hookSpecificOutput"]["additionalContext"]
    if contract_text not in context:
        raise ValueError("fixture contract was not injected")
    transcript_path = Path(next(e["input"]["transcript_path"] for e in events if e["input"].get("transcript_path")))
    transcript = transcript_path.read_text(encoding="utf-8")
    messages = [json.loads(line) for line in transcript.splitlines()]
    if not any(row.get("type") == "response_item" and row["payload"].get("role") == "developer"
               and any(context == part.get("text") for part in row["payload"].get("content", [])) for row in messages):
        raise ValueError("injected contract is missing from the model transcript")
    shutil.copyfile(transcript_path, out / f"{stage}-transcript.jsonl")
    shutil.copytree(workspace / ".harness", out / f"{stage}-state")
    if not real and workspace_files(workspace):
        raise ValueError("the synthetic demo unexpectedly wrote implementation files")
    state = json.loads((workspace / ".harness/state.json").read_text())
    session = json.loads((workspace / ".harness/session.json").read_text())
    blocks = [e for e in events if e["event"] == "Stop" and e["output"] and e["output"].get("decision") == "block"]
    if stage == "request":
        before_approval = {"files": workspace_files(workspace)}
        write_json(out / "request-workspace.json", before_approval)
        if before_approval != json.loads((out / "initial-workspace.json").read_text()):
            raise ValueError("task files changed before approval")
        if session["phase"] != "awaiting_approval" or state["attempt"] != 0 or blocks:
            raise ValueError("the request did not stop at the approval gate")
        summary = {"contract_visible": True, "approval_pending": True, "verifier_calls": 0}
    else:
        verdict = json.loads((workspace / ".harness/verdict.json").read_text())
        if (session["phase"] != "complete" or verdict["overall"] != "pass"
                or (not real and (state["attempt"] != 2 or len(blocks) != 1))
                or (real and (len(blocks) != state["attempt"] - 1
                              or not 1 <= state["attempt"] <= metadata.get("max_attempts", 3)))):
            raise ValueError("expected exactly one re-instruction followed by fixture pass")
        if real:
            from plugin.hooks._runtime import validate
            validate(workspace / ".harness/handoff.json", "handoff.schema.json")
            if (workspace / "result.txt").read_bytes() != b"ok\n":
                raise ValueError("real task artifact failed exact content check")
            shutil.copyfile(workspace / "result.txt", out / "result.txt")
            metadata["real_task_verified"] = True
            write_json(out / "experiment.json", metadata)
        summary = {"contract_visible": True, "approval_pending": False, "reinstructions": len(blocks),
                   "verifier_calls": state["attempt"], "overall": "pass", "synthetic": not real,
                   "real_task_verified": real}
    write_json(out / f"{stage}-summary.json", summary)
    return summary


def start(out: Path, run: Runner = run_group, mode: str = "stub") -> dict[str, Any]:
    metadata = prepare(out.resolve(), run=run, mode=mode)
    launch(metadata, "request", run=run)
    collect(metadata, "request")
    return metadata


def finish(metadata: dict[str, Any], scripted: bool, run: Runner = run_group) -> dict[str, Any]:
    out = Path(metadata["out"])
    if (out / "approval-result.json").exists():
        raise ValueError("approval was already attempted; use a fresh experiment to preserve evidence")
    print((out / "request-reply.txt").read_text())
    if scripted:
        print(f"SCRIPTED DEMO USER: approve ({metadata.get('mode', 'stub')} demonstration)")
        approval = "approve"
    else:
        approval = input("Review the summary above. Type approve to continue the stub demonstration: ").strip()
    if approval != "approve":
        raise ValueError("approval not supplied; evidence retained at the approval gate")
    before_approval = {"files": workspace_files(Path(metadata["workspace"]))}
    write_json(out / "before-approval-workspace.json", before_approval)
    if before_approval != json.loads((out / "initial-workspace.json").read_text()):
        raise ValueError("task files changed before approval")
    metadata["approval"] = "scripted demo user" if scripted else "interactive user"
    launch(metadata, "approval", run=run)
    summary = collect(metadata, "approval")
    print((out / "approval-reply.txt").read_text())
    print(json.dumps(summary, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--out", type=Path)
    destination.add_argument("--continue", dest="continue_from", type=Path)
    parser.add_argument("--approval-only", action="store_true", help="one codex exec; retain pending approval")
    parser.add_argument("--scripted-approval", action="store_true", help="send a scripted demo approve after saving the summary")
    parser.add_argument("--real", action="store_true", help="host only: real controller/verifier and codex_cli backend")
    args = parser.parse_args()
    if not args.real and not args.continue_from and os.environ.get("HARNESS_STUB") != "1":
        parser.error("choose --real or HARNESS_STUB=1")
    try:
        if args.continue_from:
            metadata = json.loads((args.continue_from.resolve() / "experiment.json").read_text())
        else:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            mode = "real" if args.real else "stub"
            name = datetime.now().strftime("%Y-%m-%d") + "-real" if args.real else f"d2-{stamp}"
            metadata = start(args.out or PLUGIN / "evidence" / name, mode=mode)
        if not args.approval_only:
            finish(metadata, args.scripted_approval)
        print(f"Evidence: {metadata['out']}")
        return 0
    except Exception as exc:
        print(f"demo failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
