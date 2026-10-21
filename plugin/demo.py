"""Run the D-2 fixture loop in an isolated Codex session, preserving real logs."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"
Runner = Callable[..., subprocess.CompletedProcess[str]]
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


def prepare(out: Path, run: Runner = subprocess.run) -> dict[str, Any]:
    """Register only reviewed harness hooks in a temporary home/workspace."""
    if out.exists():
        raise ValueError("use a new output directory; evidence is never overwritten")
    version = run(["codex", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    expected = (PLUGIN / "CODEX_VERSION").read_text().strip()
    if version != expected:
        raise ValueError(f"STOP-P2: Codex version mismatch: expected {expected}; found {version}")
    out.mkdir(parents=True)
    temporary = Path(tempfile.mkdtemp(prefix="harness-d2-"))
    home, workspace = temporary / "codex-home", temporary / "workspace"
    home.mkdir()
    workspace.mkdir()
    existing_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth = existing_home / "auth.json"
    if auth.is_file():
        # Reuse CLI login by reference outside the repo, never read/copy credential content.
        (home / "auth.json").symlink_to(auth)
    (home / "config.toml").write_text(
        'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "low"\n'
        'approval_policy = "never"\nsandbox_mode = "read-only"\n'
        '[features]\nhooks = true\nmulti_agent = false\n'
        'skip_host_skill_discovery = true\n'
        f'[projects.{json.dumps(str(workspace))}]\ntrust_level = "trusted"\n',
        encoding="utf-8",
    )
    hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text())
    for groups in hooks["hooks"].values():
        for group in groups:
            for handler in group["hooks"]:
                script = handler["command"].split("/hooks/")[1].rstrip('"')
                handler["command"] = shlex.join([sys.executable, str(PLUGIN / "hooks" / script)])
    write_json(home / "hooks.json", hooks)
    write_json(out / "hooks.json", hooks)
    metadata = {"version": version, "workspace": str(workspace), "codex_home": str(home),
                "out": str(out), "mode": "stub", "executor": "gpt-6.1-sol", "prompt": PROMPT,
                "approval": "pending", "real_task_verified": False}
    write_json(out / "experiment.json", metadata)
    return metadata


def launch(metadata: dict[str, Any], stage: str, run: Runner = subprocess.run) -> None:
    """Launch exactly one executor process per stage; hooks own verification."""
    out = Path(metadata["out"])
    child_env = dict(os.environ)
    # This is a direct-user hook demo, unlike the independent evaluation runner.
    child_env.pop("HARNESS_NESTED", None)
    child_env.update(CODEX_HOME=metadata["codex_home"], HARNESS_STUB="1",
                     HARNESS_PYTHON=sys.executable, HARNESS_EVENT_LOG=str(out / "hooks.jsonl"),
                     PLUGIN_ROOT=str(PLUGIN))
    command = ["codex", "--no-daemon", "--dangerously-bypass-hook-trust", "exec"]
    if stage == "approval":
        command += ["resume", metadata["thread_id"]]
    command += ["--skip-git-repo-check", "--json", "--output-last-message", str(out / f"{stage}-reply.txt"), "-"]
    prompt = PROMPT if stage == "request" else "approve"
    try:
        result = run(command, input=prompt, cwd=metadata["workspace"], env=child_env,
                     text=True, capture_output=True, timeout=180, shell=False, check=False)
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
    contract_text = (ROOT / "schemas/examples/contract.json").read_text()
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
    if set(p.name for p in workspace.iterdir()) != {".harness"}:
        raise ValueError("the synthetic demo unexpectedly wrote implementation files")
    state = json.loads((workspace / ".harness/state.json").read_text())
    session = json.loads((workspace / ".harness/session.json").read_text())
    blocks = [e for e in events if e["event"] == "Stop" and e["output"] and e["output"].get("decision") == "block"]
    if stage == "request":
        if session["phase"] != "awaiting_approval" or state["attempt"] != 0 or blocks:
            raise ValueError("the request did not stop at the approval gate")
        summary = {"contract_visible": True, "approval_pending": True, "verifier_calls": 0}
    else:
        verdict = json.loads((workspace / ".harness/verdict.json").read_text())
        if session["phase"] != "complete" or state["attempt"] != 2 or len(blocks) != 1 or verdict["overall"] != "pass":
            raise ValueError("expected exactly one re-instruction followed by fixture pass")
        summary = {"contract_visible": True, "approval_pending": False, "reinstructions": 1,
                   "verifier_calls": 2, "overall": "pass", "synthetic": True, "real_task_verified": False}
    write_json(out / f"{stage}-summary.json", summary)
    return summary


def start(out: Path, run: Runner = subprocess.run) -> dict[str, Any]:
    metadata = prepare(out.resolve(), run=run)
    launch(metadata, "request", run=run)
    collect(metadata, "request")
    return metadata


def finish(metadata: dict[str, Any], scripted: bool, run: Runner = subprocess.run) -> dict[str, Any]:
    out = Path(metadata["out"])
    if (out / "approval-result.json").exists():
        raise ValueError("approval was already attempted; use a fresh experiment to preserve evidence")
    print((out / "request-reply.txt").read_text())
    if scripted:
        print("SCRIPTED DEMO USER: approve (synthetic fixture demonstration only)")
        approval = "approve"
    else:
        approval = input("Review the summary above. Type approve to continue the stub demonstration: ").strip()
    if approval != "approve":
        raise ValueError("approval not supplied; evidence retained at the approval gate")
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
    args = parser.parse_args()
    if os.environ.get("HARNESS_STUB") != "1":
        parser.error("D-2 supports HARNESS_STUB=1 only; real mode awaits D-3")
    try:
        if args.continue_from:
            metadata = json.loads((args.continue_from.resolve() / "experiment.json").read_text())
        else:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            metadata = start(args.out or PLUGIN / "evidence" / f"d2-{stamp}")
        if not args.approval_only:
            finish(metadata, args.scripted_approval)
        print(f"Evidence: {metadata['out']}")
        return 0
    except Exception as exc:
        print(f"demo failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
