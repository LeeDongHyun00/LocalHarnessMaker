"""Audit observed grader access without publishing grader locations."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import unquote


def digest(data: bytes) -> str:
    """Return a stable evidence fingerprint."""
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class PrivateGraders:
    """Keep all private locations in memory, supplied by the trusted parent."""

    root: Path
    files: tuple[Path, ...]
    aliases: tuple[str, ...] = ()
    name_aliases: tuple[str, ...] = ()

    @classmethod
    def load(cls, root: Path, task_id: str, repository: Path) -> "PrivateGraders":
        resolved = root.expanduser().resolve()
        if resolved.is_relative_to(repository.resolve()) or repository.resolve().is_relative_to(resolved):
            raise ValueError("Private grader root must be outside and separate from the repository")
        task = (resolved / task_id).resolve()
        if not task.is_relative_to(resolved) or not task.is_dir():
            raise ValueError("Private task graders are unavailable")
        files = tuple(sorted(task.glob("test_*.py")))
        if not files or any(p.is_symlink() or not p.is_file() for p in files):
            raise ValueError("Private task requires regular test_*.py files")
        metadata = task / "audit-names.json"
        names = json.loads(metadata.read_text()).get("historical_names", []) if metadata.exists() else []
        if not isinstance(names, list) or any(not isinstance(name, str) or Path(name).name != name for name in names):
            raise ValueError("Historical grader aliases must be bare filenames")
        return cls(resolved, files, (str(root.expanduser().absolute()),), tuple(names))

    def markers(self) -> dict[str, str]:
        """Include both symlink spellings and platform-canonical paths."""
        markers = {str(self.root): "private_root"}
        markers.update({alias: "private_root" for alias in self.aliases})
        home = str(Path.home())
        if str(self.root).startswith(home + "/"):
            markers["~" + str(self.root)[len(home):]] = "private_root"
        for index, path in enumerate(self.files, 1):
            markers[path.name] = f"grader_file_{index}"
        markers.update({name: f"historical_grader_{index}" for index, name in enumerate(self.name_aliases, 1)})
        return markers

    def redact(self, text: str) -> str:
        """Never place an actual private location in a repository artifact."""
        def plain(value: str) -> str:
            decoded = unquote(value)
            changed = False
            for marker, label in sorted(self.markers().items(), key=lambda item: -len(item[0])):
                for spelling in {marker, json.dumps(marker)[1:-1]}:
                    updated = re.sub(re.escape(spelling), f"<{label}>", decoded, flags=re.IGNORECASE)
                    changed |= updated != decoded
                    decoded = updated
            return decoded if changed else value

        def walk(value: Any) -> Any:
            if isinstance(value, str):
                return plain(value)
            if isinstance(value, dict):
                return {plain(key): walk(item) for key, item in value.items()}
            if isinstance(value, list):
                return [walk(item) for item in value]
            return value

        try:
            value = json.loads(text)
            sanitized = walk(value)
            if sanitized != value:
                return json.dumps(sanitized, ensure_ascii=False) + ("\n" if text.endswith("\n") else "")
            return text
        except ValueError:
            if "\n" in text.rstrip("\n"):
                return "".join(self.redact(line) for line in text.splitlines(keepends=True))
            return plain(text)


def executor_environment(private: PrivateGraders, codex_home: Path) -> dict[str, str]:
    """Allow only runtime environment; remove grader paths and API credentials."""
    allowed = {"HOME", "PATH", "USER", "LOGNAME", "LANG", "LC_ALL", "TERM", "TMPDIR",
               "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE"}
    environment = {
        key: value for key, value in os.environ.items()
        if key in allowed and not any(marker in unquote(value) for marker in private.markers())
    }
    environment.update({"CODEX_HOME": str(codex_home), "HARNESS_NESTED": "1"})
    if any(marker in value for marker in private.markers() for value in environment.values()):
        raise ValueError("Private grader location would reach executor environment")
    return environment


def audit_logs(paths: list[Path], private: PrivateGraders, *, require_completion: bool = True,
               workspace: Path | None = None, repository: Path | None = None,
               grading_roots: tuple[Path, ...] = ()) -> dict[str, Any]:
    """Audit supported tool records only; unresolved access is inconclusive."""
    matches: list[dict[str, Any]] = []
    errors: list[str] = []
    logs: list[dict[str, Any]] = []
    repository = (repository or Path(__file__).resolve().parents[2]).resolve()
    roots = [Path.home() / ".codex", repository.parent / "codex-bridge", repository,
             private.root, *grading_roots]
    aliases = {"~/.codex": Path.home() / ".codex", "$HOME/.codex": Path.home() / ".codex",
               "${HOME}/.codex": Path.home() / ".codex"}
    calls: dict[str, str] = {}
    pending_calls: set[str] = set()
    pending_items: set[str] = set()

    def leaves(value: Any) -> list[str]:
        if isinstance(value, str):
            return [unquote(value)]
        if isinstance(value, dict):
            return [s for item in value.values() for s in leaves(item)]
        if isinstance(value, list):
            return [s for item in value for s in leaves(item)]
        return []

    for path in paths:
        if not path.is_file():
            errors.append(f"missing_log:{path.name}")
            continue
        data = path.read_bytes()
        logs.append({"name": path.name, "sha256": digest(data), "bytes": len(data)})
        terminal = False
        native = False
        if not data or not data.endswith(b"\n"):
            errors.append(f"empty_or_truncated_log:{path.name}")
        for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                    raise ValueError("Unsupported event")
            except (ValueError, TypeError):
                errors.append(f"malformed_event:{path.name}:{number}")
                continue
            kind = event["type"]
            terminal |= kind in {"turn.completed", "turn.failed", "error"}
            native |= kind in {"session_meta", "turn_context", "response_item", "event_msg"}
            item = event.get("item", {})
            if kind == "response_item":
                item = event.get("payload", {})
            if not isinstance(item, dict):
                errors.append(f"unsupported_item:{path.name}:{number}")
                continue
            item_type = item.get("type", "")
            tool = ""
            if item_type in {"function_call", "custom_tool_call"}:
                tool = item.get("name", "unknown")
                call_id = item.get("call_id", "")
                calls[call_id] = tool
                pending_calls.add(call_id)
            elif item_type in {"function_call_output", "custom_tool_call_output"}:
                call_id = item.get("call_id", "")
                tool = calls.get(call_id, "unknown")
                pending_calls.discard(call_id)
                if tool == "unknown":
                    errors.append(f"unpaired_tool_output:{path.name}:{number}")
            elif item_type in {"command_execution", "file_change", "mcp_tool_call", "web_search"}:
                tool = item_type
            elif kind.startswith("item.") and ("command" in item or "arguments" in item):
                tool = item.get("name", "command_execution")
            elif kind == "response_item" and item_type not in {"message", "reasoning", "compaction"}:
                errors.append(f"unsupported_response_item:{path.name}:{number}")
            elif kind.startswith("item.") and item_type not in {"agent_message", "reasoning", "todo_list"}:
                errors.append(f"unsupported_tool:{path.name}:{number}")
            elif kind not in {"thread.started", "turn.started", "turn.completed", "turn.failed", "error",
                              "item.started", "item.updated", "item.completed", "session_meta", "turn_context", "response_item", "event_msg"}:
                errors.append(f"unsupported_event:{path.name}:{number}")
            if tool and kind == "item.started":
                if not item.get("id"):
                    errors.append(f"missing_tool_item_id:{path.name}:{number}")
                pending_items.add(item.get("id", ""))
            elif tool and kind == "item.completed":
                pending_items.discard(item.get("id", ""))
            if not tool:
                continue
            text = "\n".join(leaves(item))
            # Native arguments are often a JSON string containing escaped path text.
            for value in leaves(item):
                try:
                    text += "\n" + "\n".join(leaves(json.loads(value)))
                except ValueError:
                    pass
            for alias, target in aliases.items():
                text = text.replace(alias, str(target))
            hits: set[str] = set()
            for marker, label in private.markers().items():
                if marker.casefold() in text.casefold():
                    hits.add(label)
            # Extract operands from commands/results, JSON strings, and patch paths.
            for token in re.findall(r"(?:/|\.\.?/|~/|[A-Za-z0-9_.-]+/)[^\s\"'<>;,|(){}\[\]]+", text):
                token = token.rstrip(":.")
                candidate = Path(token).expanduser()
                if not candidate.is_absolute():
                    if workspace is None:
                        errors.append(f"unresolved_relative_path:{path.name}:{number}")
                        continue
                    candidate = workspace / candidate
                canonical = candidate.resolve()
                if workspace is not None and canonical.is_relative_to(workspace.resolve()):
                    continue
                if any(canonical.is_relative_to(root.resolve()) for root in roots):
                    hits.add(str(candidate))
            if "$" in text or "`" in text:
                errors.append(f"unresolved_operand:{path.name}:{number}")
            for hit in sorted(hits):
                matches.append({"log": path.name, "line": number, "marker": hit, "tool": tool,
                                "operation": "execute" if "command" in tool or "exec" in tool else "unknown",
                                "evidence_sha256": digest(line.encode()), "redacted_evidence": private.redact(line)})
        if require_completion and not native and not terminal:
            errors.append(f"missing_terminal_event:{path.name}")
    if require_completion and (pending_calls or pending_items):
        errors.append("unfinished_tool_events")
    if not paths:
        errors.append("missing_logs")
    return {"method": "access_audit", "status": "access_detected" if matches else "inconclusive" if errors else "clean",
            "root_fingerprint": digest(str(private.root).encode()),
            "grader_fingerprints": [digest(p.read_bytes()) for p in private.files],
            "logs": logs, "matches": matches, "errors": errors,
            "scope": "Observed tool events only; a clean audit does not prove isolation."}
