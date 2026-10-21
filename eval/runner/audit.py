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


def audit_logs(paths: list[Path], private: PrivateGraders, *, require_completion: bool = True) -> dict[str, Any]:
    """Scan every raw and decoded JSONL record; uncertainty invalidates a run."""
    matches: list[dict[str, Any]] = []
    errors: list[str] = []
    logs: list[dict[str, Any]] = []
    completed = False
    for path in paths:
        data = path.read_bytes()
        logs.append({"name": path.name, "sha256": digest(data), "bytes": len(data)})
        if not data:
            errors.append(f"empty_log:{path.name}")
        for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            decoded: Any = None
            try:
                decoded = json.loads(line)
                if not isinstance(decoded, dict):
                    raise ValueError("JSON event must be an object")
                completed |= decoded.get("type") == "turn.completed"
            except (ValueError, TypeError):
                errors.append(f"malformed_event:{path.name}:{number}")
            searchable = unquote(line + "\n" + json.dumps(decoded, ensure_ascii=False))
            # json.dumps re-escapes strings, so also inspect every decoded leaf.
            def leaves(value: Any) -> list[str]:
                if isinstance(value, str):
                    return [value]
                if isinstance(value, dict):
                    return [s for key, item in value.items() for s in [str(key), *leaves(item)]]
                if isinstance(value, list):
                    return [s for item in value for s in leaves(item)]
                return []
            searchable += "\n" + unquote("\n".join(leaves(decoded)))
            for marker, label in private.markers().items():
                if marker.casefold() in searchable.casefold():
                    matches.append({"log": path.name, "line": number, "marker": label,
                                    "evidence_sha256": digest(line.encode()),
                                    "redacted_evidence": private.redact(line)})
    if require_completion and not completed:
        errors.append("missing_turn_completed")
    return {
        "method": "access_audit", "status": "access_detected" if matches else "inconclusive" if errors else "clean",
        "root_fingerprint": digest(str(private.root).encode()),
        "grader_fingerprints": [digest(p.read_bytes()) for p in private.files],
        "logs": logs, "matches": matches, "errors": errors,
        "scope": "Observed JSONL only; absence of matches does not prove denied access.",
    }
