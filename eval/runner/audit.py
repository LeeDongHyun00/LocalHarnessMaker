"""Audit observed grader access without publishing grader locations."""

from dataclasses import dataclass
from functools import lru_cache
import ast
import glob
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import tokenize
from typing import Any
from urllib.parse import unquote

from eval.runner.javascript import tool_calls


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
    public_root: Path | None = None

    @classmethod
    def load(cls, root: Path, task_id: str, repository: Path) -> "PrivateGraders":
        resolved = root.expanduser().resolve()
        if resolved.is_relative_to(repository.resolve()) or repository.resolve().is_relative_to(resolved):
            raise ValueError("Private grader root must be outside and separate from the repository")
        supplied_task = resolved / task_id
        task = supplied_task.resolve()
        if (not task_id or task_id.startswith(".") or Path(task_id).name != task_id or
                supplied_task.is_symlink() or task.parent != resolved or not task.is_dir()):
            raise ValueError("Private task graders are unavailable")
        files = tuple(sorted(task.glob("test_*.py")))
        if not files or any(p.is_symlink() or not p.is_file() for p in files):
            raise ValueError("Private task requires regular test_*.py files")
        metadata = task / "audit-names.json"
        names = json.loads(metadata.read_text()).get("historical_names", []) if metadata.exists() else []
        if not isinstance(names, list) or any(not isinstance(name, str) or Path(name).name != name for name in names):
            raise ValueError("Historical grader aliases must be bare filenames")
        return cls(resolved, files, (str(root.expanduser().absolute()),), tuple(names),
                   repository / "eval/tasks")

    def line_fingerprints(self, cache: "FingerprintCache | None" = None) -> set[str]:
        """Return hidden-line hashes, optionally sharing an invocation snapshot."""
        if cache is not None:
            return set(cache.fingerprints(self))
        return self._compute_line_fingerprints()

    def _compute_line_fingerprints(self) -> set[str]:
        """Analyze unique immediate task graders against the public corpus once."""
        public: list[str] = []
        if self.public_root is not None:
            for task in self.public_root.iterdir() if self.public_root.is_dir() else ():
                if not task.is_dir():
                    continue
                paths = [task / name for name in ("prompt.md", "day2.md", "expected.json", "meta.json")]
                paths.extend((task / "workspace").rglob("*"))
                public.extend(path.read_text(errors="replace") for path in paths if path.is_file())
        public_lines = {normalize_line(line) for text in public for line in text.splitlines()}
        public_literals: set[str | int | float | complex] = set()
        for text in public:
            try:
                for token in tokenize.generate_tokens(io.StringIO(text).readline):
                    if token.type in {tokenize.STRING, tokenize.NUMBER}:
                        try:
                            value = ast.literal_eval(token.string)
                        except (ValueError, SyntaxError):
                            continue
                        if type(value) in {str, int, float, complex}:
                            public_literals.add(value)
            except (tokenize.TokenError, IndentationError, SyntaxError):
                # Prose need not tokenize as Python; substring checks still
                # cover the entire file, including text after a token error.
                pass
        fingerprints: set[str] = set()
        seen: set[str] = set()
        for source in grader_sources(self.root):
            data = source.read_bytes()
            content_hash = digest(data)
            if content_hash in seen:
                continue
            seen.add(content_hash)
            text = data.decode("utf-8", errors="replace")
            tree = ast.parse(text)
            nodes = tuple(ast.walk(tree))
            # Docstrings, the module entry guard and unittest's launcher are
            # scaffolding, even when their literals happen to be absent publicly.
            boilerplate: set[int] = set()
            for node in nodes:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    boilerplate.add(id(node.value))
                if ((isinstance(node, ast.If) and any(isinstance(child, ast.Name) and child.id == "__name__"
                                                     for child in ast.walk(node.test))) or
                    (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                     isinstance(node.func.value, ast.Name) and node.func.value.id == "unittest" and
                     node.func.attr == "main")):
                    expression = node.test if isinstance(node, ast.If) else node
                    boilerplate.update(id(child) for child in ast.walk(expression))
            lines = text.splitlines()
            # AST columns are UTF-8 byte offsets. Avoid get_source_segment's
            # full-source split for every literal in a large grader.
            encoded = text.encode("utf-8")
            offsets = [0]
            for line in encoded.splitlines(keepends=True):
                offsets.append(offsets[-1] + len(line))
            for node in nodes:
                if (not isinstance(node, ast.Constant) or id(node) in boilerplate or
                        type(node.value) not in {str, int, float, complex}):
                    continue
                value = str(node.value)
                spelling = encoded[offsets[node.lineno - 1] + node.col_offset:
                                   offsets[(node.end_lineno or node.lineno) - 1] +
                                   (node.end_col_offset or 0)].decode("utf-8") or value
                # Substring exclusion is deliberately conservative: a short
                # common number/string cannot establish hidden provenance.
                if (not value.strip() or node.value in public_literals or
                        any(value in item or spelling in item or json.dumps(value)[1:-1] in item for item in public)):
                    continue
                for number in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                    line = normalize_line(lines[number - 1])
                    if len(line) >= 16 and line not in public_lines:
                        fingerprints.add(digest(line.encode()))
        return fingerprints

    def markers(self) -> dict[str, str]:
        """Include both symlink spellings and platform-canonical paths."""
        markers = {str(self.root): "private_root"}
        markers.update({alias: "private_root" for alias in self.aliases})
        for marker, label in tuple(markers.items()):
            if marker == "/private/var" or marker.startswith("/private/var/"):
                markers[marker[len("/private"):]] = label
            elif marker == "/var" or marker.startswith("/var/"):
                markers["/private" + marker] = label
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


def grader_sources(root: Path) -> list[Path]:
    """Enumerate ROOT/task/test_*.py only; never descend into dot storage."""
    return [source for task in sorted(root.iterdir())
            if not task.name.startswith(".") and not task.is_symlink() and task.is_dir()
            for source in sorted(task.glob("test_*.py"))
            if not source.is_symlink() and source.is_file()]


class FingerprintCache:
    """Share immutable corpus analysis within one runner/re-audit invocation."""

    def __init__(self) -> None:
        self._snapshots: dict[tuple[Path, Path | None], frozenset[str]] = {}

    def fingerprints(self, private: PrivateGraders) -> frozenset[str]:
        """Cache across tasks with the same private and public corpus roots."""
        key = (private.root.resolve(), private.public_root.resolve() if private.public_root else None)
        if key not in self._snapshots:
            self._snapshots[key] = frozenset(private._compute_line_fingerprints())
        return self._snapshots[key]


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


def normalize_line(line: str) -> str:
    """Ignore indentation/spacing, retaining only a digest in audit records."""
    return " ".join(line.split())


def unwrap_shell(command: str) -> str:
    """Remove literal executor shell wrappers while preserving the inner syntax."""
    for _ in range(8):
        words = shlex.split(command)
        if (len(words) == 3 and Path(words[0]).name in {"zsh", "bash", "sh", "dash"}
                and words[1] in {"-c", "-lc", "-cl"}):
            command = words[2]
        else:
            return command
    raise ValueError("Shell wrapper nesting exceeds audit limit")


def shell_tokens(command: str) -> list[tuple[str, str]]:
    """Use shlex for values and retain each raw word for local quote checks."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = ""
    values = list(lexer)
    raw_words = re.findall(r"(?:[^\s;&|()'\"\\]|\\.|'[^']*'|\"(?:[^\"\\]|\\.)*\")+|[;&|()]+",
                           command, flags=re.DOTALL)
    if len(raw_words) != len(values):
        raise ValueError("Unresolved shell token boundaries")
    return list(zip(values, raw_words))


def canonical_path(path: Path) -> str:
    """Compare macOS temporary paths using the same /private/var spelling."""
    value = str(path.resolve()).casefold().rstrip("/")
    if value == "/var" or value.startswith("/var/"):
        value = "/private" + value
    return value


def workspace_glob(pattern: Path, workspace: Path | None) -> bool:
    """A static directory inside the workspace bounds a non-traversing glob."""
    if workspace is None:
        return False
    value = str(pattern)
    first = min(value.index(ch) for ch in "*?[" if ch in value)
    if ".." in Path(value[first:]).parts:
        return False
    prefix = value[:first]
    directory = Path(prefix.rsplit("/", 1)[0] or "/").resolve()
    allowed = canonical_path(workspace)
    canonical = canonical_path(directory)
    return canonical == allowed or canonical.startswith(allowed + "/")


def command_operands(command: str, cwd: Path | None, *,
                     workspace: Path | None = None) -> tuple[list[tuple[Path, bool]], bool]:
    """Resolve supported shell operands; uncertainty never establishes cleanliness."""
    operands: list[tuple[Path, bool]] = []
    unresolved = False
    try:
        command = unwrap_shell(command)
        tokens = shell_tokens(command)
    except ValueError:
        return [], True
    if "$" in command or "`" in command:
        unresolved = True
    if re.search(r"(?:base64|xxd|openssl).*\|.*(?:sh|bash|python|perl|ruby)\b", command):
        unresolved = True
    groups: list[list[tuple[str, str]]] = [[]]
    for token, raw in tokens:
        if token in {";", "&&", "||", "|", "(", ")", "&"} and raw == token:
            groups.append([])
        else:
            groups[-1].append((token, raw))
    stack: list[Path | None] = []
    for group in groups:
        if not group:
            continue
        executable = Path(group[0][0]).name
        recursive = executable in {"find", "rg", "du", "tar", "rsync"} or (
            executable in {"grep", "ls", "cp"} and any(
                arg.startswith("-") and ("r" in arg.lower() or "recursive" in arg)
                for arg, _ in group[1:]))
        if executable == "popd":
            if stack:
                cwd = stack.pop()
            else:
                unresolved = True
            continue
        if executable in {"zsh", "bash", "sh", "dash"} and len(group) >= 3 and group[1][0] in {"-c", "-lc", "-cl"}:
            nested, unknown = command_operands(group[2][0], cwd, workspace=workspace)
            operands.extend(nested)
            unresolved |= unknown
            continue
        args = group[1:]
        if executable in {"cd", "pushd"} and not args:
            args = [("~", "~")]
        pattern_options = {
            "rg": {"-g", "--glob", "--iglob", "-e", "--regexp"},
            "find": {"-name", "-iname", "-path", "-ipath", "-wholename"},
            "grep": {"--include", "--exclude", "-e", "--regexp"},
        }.get(executable, set())
        skip_pattern = False
        path_count = 0
        for token, raw in args:
            if executable == "make" and re.match(r"[A-Za-z_][A-Za-z0-9_]*=", token):
                token, raw = token.split("=", 1)[1], raw.split("=", 1)[1]
            if skip_pattern:
                skip_pattern = False
                continue
            if token in pattern_options:
                skip_pattern = True
                continue
            if any(token.startswith(option + "=") for option in pattern_options):
                continue
            if token.startswith("-") or token in {"+", "{}"}:
                continue
            if token.startswith("~") and token != "~" and not token.startswith("~/"):
                unresolved = True
                continue
            expanded = Path(token).expanduser()
            if not expanded.is_absolute():
                if cwd is None:
                    if "/" in token or executable in {"cd", "pushd"}:
                        unresolved = True
                    continue
                expanded = cwd / expanded
            magical = glob.has_magic(str(expanded))
            concrete = [Path(value) for value in glob.glob(str(expanded), recursive=True)] if magical else [expanded]
            bounded = magical and workspace_glob(expanded, workspace)
            if magical and not bounded:
                unresolved = True
            # Quote provenance belongs to this word, never the shell wrapper or
            # another argument (for example sed's quoted address expression).
            whole_quote = re.fullmatch(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"", raw, flags=re.DOTALL)
            mixed_quote = ("'" in raw or '"' in raw or "\\" in raw) and not whole_quote
            if mixed_quote and ("/" in token or Path(token).suffix or executable in {"cd", "pushd"}) and not expanded.exists() and not magical:
                unresolved = True
            for candidate in concrete:
                operands.append((candidate.resolve(), recursive))
            path_count += 1
            if executable in {"cd", "pushd"}:
                if len(concrete) != 1 or magical or not concrete[0].is_dir():
                    unresolved = True
                    cwd = None
                else:
                    if executable == "pushd":
                        stack.append(cwd)
                    cwd = concrete[0].resolve()
                break
        if skip_pattern:
            unresolved = True
        if recursive and not path_count and cwd is not None:
            operands.append((cwd.resolve(), True))
    return operands, unresolved


def custom_commands(item: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], bool]:
    """Decode literal native custom inputs without executing executor code."""
    source = item.get("input")
    if not isinstance(source, str):
        return [], [], True
    try:
        arguments = json.loads(source)
    except ValueError:
        arguments = None
    name = item.get("name", "")
    if isinstance(arguments, dict):
        if name.endswith("apply_patch"):
            patch = arguments.get("patch", arguments.get("input"))
            return [], [patch] if isinstance(patch, str) else [], not isinstance(patch, str)
        if name in {"exec_command", "shell", "shell_command"}:
            return [arguments], [], not any(key in arguments for key in ("cmd", "command"))
        return [], [], True
    if name.endswith("apply_patch"):
        return [], [source], not source.startswith("*** Begin Patch")
    if name != "exec":
        if name in {"exec_command", "shell", "shell_command"}:
            return [{"cmd": source}], [], False
        return [], [], True
    return tool_calls(source)


def change_paths(item: dict[str, Any]) -> list[str]:
    """Extract file-change targets and moves, excluding authored contents/diffs."""
    paths = [value for key, value in item.items()
             if key in {"path", "file_path", "move_path"} and isinstance(value, str)]
    changes = item.get("changes")
    if isinstance(changes, dict):
        paths.extend(changes)
        for change in changes.values():
            if isinstance(change, dict):
                paths.extend(change_paths(change))
    elif isinstance(changes, list):
        for change in changes:
            if isinstance(change, dict):
                paths.extend(change_paths(change))
    return paths


def patch_paths(patch: str) -> list[str]:
    """Return literal patch header paths; added/deleted text is not an operand."""
    return re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", patch, re.MULTILINE)


def valid_native_metadata(kind: str, payload: Any) -> bool:
    """Validate the observed snapshot/usage envelope, allowing evolving fields."""
    if not isinstance(payload, dict):
        return False
    if kind == "world_state":
        return type(payload.get("full")) is bool and isinstance(payload.get("state"), dict)
    if kind == "thread_settings_applied":
        settings = payload.get("thread_settings")
        if not isinstance(payload.get("thread_id"), str) or not payload["thread_id"] or not isinstance(settings, dict):
            return False
        strings = ("model", "model_provider_id", "approval_policy", "approvals_reviewer", "cwd", "reasoning_effort")
        if not all(isinstance(settings.get(key), str) and settings[key] for key in strings):
            return False
        if not all(isinstance(settings.get(key), list) and all(isinstance(v, str) for v in settings[key])
                   for key in ("runtime_workspace_roots", "disabled_plugin_ids")):
            return False
        profile = settings.get("permission_profile")
        if (not isinstance(profile, dict) or not isinstance(profile.get("type"), str) or
                not isinstance(profile.get("network"), str) or not isinstance(profile.get("file_system"), dict)):
            return False
        filesystem = profile["file_system"]
        if not isinstance(filesystem.get("type"), str) or not isinstance(filesystem.get("entries"), list):
            return False
        for entry in filesystem["entries"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("access"), str):
                return False
            path = entry.get("path")
            if not isinstance(path, dict):
                return False
            if path.get("type") == "path":
                if not isinstance(path.get("path"), str):
                    return False
            elif path.get("type") == "special":
                if not isinstance(path.get("value"), dict) or not isinstance(path["value"].get("kind"), str):
                    return False
            else:
                return False
            if "missing_path_behavior" in entry and not isinstance(entry["missing_path_behavior"], str):
                return False
        mode = settings.get("collaboration_mode")
        if not isinstance(mode, dict) or not isinstance(mode.get("mode"), str) or not isinstance(mode.get("settings"), dict):
            return False
        applied = mode["settings"]
        return (isinstance(applied.get("model"), str) and isinstance(applied.get("reasoning_effort"), str) and
                "developer_instructions" in applied and
                (applied["developer_instructions"] is None or isinstance(applied["developer_instructions"], str)))
    for key in ("usage", "turn_token_usage", "thread_token_usage"):
        counts = payload.get(key)
        if key not in payload and key != "usage":
            continue
        if not isinstance(counts, dict) or not {"input_tokens", "output_tokens"} <= counts.keys():
            return False
        if any(type(value) is not int or value < 0 for value in counts.values()):
            return False
    return True


def audit_logs(paths: list[Path], private: PrivateGraders, *, require_completion: bool = True,
               workspace: Path | None = None, repository: Path | None = None,
               grading_roots: tuple[Path, ...] = (),
               fingerprint_cache: FingerprintCache | None = None) -> dict[str, Any]:
    """Audit tool access and native metadata disclosure; retain every error."""
    matches: list[dict[str, Any]] = []
    errors: list[str] = []
    logs: list[dict[str, Any]] = []
    repository = (repository or Path(__file__).resolve().parents[2]).resolve()
    roots = [Path.home() / ".claude", Path.home() / ".codex", repository.parent / "codex-bridge", repository,
             private.root, *grading_roots]
    aliases = {prefix + name: Path.home() / name
               for name in (".codex", ".claude")
               for prefix in ("~/", "$HOME/", "${HOME}/")}
    fingerprints = private.line_fingerprints(fingerprint_cache)
    calls: dict[str, str] = {}
    pending_calls: set[str] = set()
    pending_items: set[str] = set()

    def leaves(value: Any) -> list[str]:
        if isinstance(value, str):
            return [unquote(value)]
        if isinstance(value, dict):
            return [s for key, item in value.items() for s in [unquote(key), *leaves(item)]]
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
            native_kinds = {"session_meta", "turn_context", "response_item", "event_msg",
                            "world_state", "token_usage_record"}
            native |= kind in native_kinds
            if kind not in native_kinds | {"thread.started", "turn.started", "turn.completed", "turn.failed", "error",
                                           "item.started", "item.updated", "item.completed"}:
                errors.append(f"unsupported_event:{path.name}:{number}:{kind}")
                continue
            payload = event.get("payload")
            metadata_kind = ("thread_settings_applied" if kind == "event_msg" and isinstance(payload, dict)
                             and payload.get("type") == "thread_settings_applied" else kind)
            metadata = metadata_kind in {"world_state", "token_usage_record", "thread_settings_applied"}
            if metadata and not valid_native_metadata(metadata_kind, payload):
                errors.append(f"malformed_{metadata_kind}:{path.name}:{number}")
            item = event.get("item", {})
            if kind == "response_item":
                item = event.get("payload", {})
            elif metadata:
                item = event
            elif kind == "event_msg":
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    errors.append(f"malformed_event_msg:{path.name}:{number}")
                    continue
                event_type = payload.get("type")
                if event_type == "item_completed":
                    item = payload.get("item")
                    if isinstance(item, dict):
                        item = dict(item)
                        native_type = item.get("type")
                        translated = {"CommandExecution": "command_execution", "FileChange": "file_change",
                                      "McpToolCall": "mcp_tool_call", "WebSearch": "web_search",
                                      "UserMessage": "agent_message", "AgentMessage": "agent_message",
                                      "Reasoning": "reasoning"}
                        if native_type not in translated:
                            errors.append(f"unsupported_native_item:{path.name}:{number}")
                        item["type"] = translated.get(native_type, native_type)
                elif event_type not in {"task_started", "task_complete", "token_count"}:
                    errors.append(f"unsupported_event_msg:{path.name}:{number}")
            if not isinstance(item, dict):
                errors.append(f"unsupported_item:{path.name}:{number}")
                continue
            item_type = item.get("type", "")
            tool = metadata_kind if metadata else ""
            if metadata:
                pass
            elif item_type in {"function_call", "custom_tool_call"}:
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
            if tool and kind == "item.started":
                if not item.get("id"):
                    errors.append(f"missing_tool_item_id:{path.name}:{number}")
                pending_items.add(item.get("id", ""))
            elif tool and kind == "item.completed":
                pending_items.discard(item.get("id", ""))
            if not tool:
                continue
            custom, patches, unknown = custom_commands(item) if item_type == "custom_tool_call" else ([], [], False)
            patch_call = item_type in {"function_call", "custom_tool_call"} and tool.endswith("apply_patch")
            if patch_call and item_type == "function_call":
                arguments = item.get("arguments")
                custom, patches, unknown = custom_commands({"name": tool, "input": arguments})
            if unknown:
                errors.append(f"unresolved_custom_input:{path.name}:{number}")
            targets = [target for patch in patches for target in patch_paths(patch)]
            if item_type == "file_change":
                targets.extend(change_paths(item))
                scanned = {"paths": targets}
            elif item_type == "custom_tool_call" or patch_call:
                scanned = {"commands": custom, "paths": targets}
                if unknown:
                    scanned["unresolved_input"] = item.get("input", item.get("arguments"))
            else:
                scanned = item
            text = "\n".join(leaves(scanned))
            # Native arguments are often a JSON string containing escaped path text.
            for value in leaves(scanned):
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
            if metadata:
                for root in (private.root, *grading_roots):
                    if any(str(alias).casefold() in text.casefold() for alias in (root, root.resolve())):
                        hits.add("private_context_path")
            @lru_cache(maxsize=8192)
            def protected(candidate: Path, recursive: bool = False) -> bool:
                canonical = canonical_path(candidate)
                for root in ((private.root, *grading_roots) if metadata else roots):
                    # Only the repository restriction has a workspace exception.
                    if root == repository and workspace is not None:
                        allowed = canonical_path(workspace)
                        if canonical == allowed or canonical.startswith(allowed + "/"):
                            continue
                    target = canonical_path(root)
                    if canonical == target or canonical.startswith(target + "/"):
                        return True
                    if recursive and (target.startswith(canonical + "/") or canonical == ""):
                        return True
                return False

            arguments = item.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except ValueError:
                    arguments = {"cmd": arguments}
            if not isinstance(arguments, dict):
                arguments = {}
            command = item.get("command", item.get("cmd", arguments.get("cmd", arguments.get("command"))))
            event_cwd = item.get("workdir", item.get("cwd", arguments.get("workdir", arguments.get("cwd",
                        event.get("workdir", event.get("cwd"))))))
            cwd = Path(event_cwd).expanduser() if isinstance(event_cwd, str) else workspace
            if cwd is not None and not cwd.is_absolute():
                cwd = workspace / cwd if workspace else None
            commands = [{"command": command, "cwd": str(cwd) if cwd else None}, *custom]
            if item_type == "custom_tool_call":
                commands = custom
            elif patch_call or item_type == "file_change":
                commands = []
            for command_item in ([] if metadata else commands):
                command = command_item.get("command", command_item.get("cmd"))
                if isinstance(command, list) and all(isinstance(word, str) for word in command):
                    command = shlex.join(command)
                if not isinstance(command, str):
                    if command is not None:
                        errors.append(f"unresolved_operand:{path.name}:{number}")
                    continue
                directory = command_item.get("workdir", command_item.get("cwd"))
                if directory is not None and (not isinstance(directory, str) or "$" in directory or "`" in directory):
                    errors.append(f"unresolved_operand:{path.name}:{number}")
                command_cwd = Path(directory).expanduser() if isinstance(directory, str) else cwd
                if command_cwd is not None and not command_cwd.is_absolute():
                    command_cwd = workspace / command_cwd if workspace else None
                operands, unresolved = command_operands(command, command_cwd, workspace=workspace)
                if unresolved:
                    errors.append(f"unresolved_operand:{path.name}:{number}")
                if ((command_cwd is not None and protected(command_cwd)) or
                        any(protected(candidate, recursive) for candidate, recursive in operands)):
                    hits.add("protected_path")
            def explicit_paths(value: Any) -> list[str]:
                if isinstance(value, dict):
                    found = [v for k, v in value.items() if k in {"path", "file_path", "move_path"} and isinstance(v, str)]
                    if isinstance(value.get("changes"), dict):
                        found.extend(value["changes"])
                    return found + [p for v in value.values() for p in explicit_paths(v)]
                if isinstance(value, list):
                    return [p for v in value for p in explicit_paths(v)]
                return []

            path_operands = [] if metadata else targets + explicit_paths(scanned)
            for operand in path_operands:
                candidate = Path(operand).expanduser()
                if not candidate.is_absolute():
                    if cwd is None:
                        errors.append(f"unresolved_tool_path:{path.name}:{number}")
                        continue
                    candidate = cwd / candidate
                if protected(candidate):
                    hits.add("protected_path")
            # Structured non-shell tools and results still carry concrete paths.
            # A boundary prevents retrying the variable-length prefix at every
            # character of a long slash-free word (quadratic on large inputs).
            for token in re.findall(r"(?<![A-Za-z0-9_.-])(?:/|\.\.?/|~/|[A-Za-z0-9_.-]+/)[^\s\"'<>;,|(){}\[\]]+", text):
                candidate = Path(token.rstrip(":.")).expanduser()
                if not candidate.is_absolute():
                    if cwd is None:
                        if not metadata:
                            errors.append(f"unresolved_relative_path:{path.name}:{number}")
                        continue
                    candidate = cwd / candidate
                if protected(candidate):
                    hits.add("protected_path")
            # Fingerprints establish observed output, never executor authorship.
            # Input checks above use shell operands or file targets, not contents.
            output = (item.get("output") if item_type in {"function_call_output", "custom_tool_call_output"}
                      else item.get("aggregated_output") if item_type == "command_execution" else None)
            for value in leaves(output):
                if any(digest(normalize_line(output_line).encode()) in fingerprints
                       for output_line in value.splitlines()):
                    hits.add("private_line_fingerprint")
            for hit in sorted(hits):
                matches.append({"log": path.name, "line": number, "marker": hit, "tool": tool,
                                "operation": "read" if metadata else "execute" if "command" in tool or "exec" in tool else "unknown",
                                "evidence_sha256": digest(line.encode()), "redacted_evidence":
                                "Private location reached executor context through native metadata." if metadata else
                                "Observed protected access; see external stream hash."})
        if require_completion and not native and not terminal:
            errors.append(f"missing_terminal_event:{path.name}")
    if require_completion and (pending_calls or pending_items):
        errors.append("unfinished_tool_events")
    if not paths:
        errors.append("missing_logs")
    return {"method": "access_audit", "status": "access_detected" if matches else "inconclusive" if errors else "clean",
            "root_fingerprint": digest(str(private.root).encode()),
            "grader_fingerprints": [digest(p.read_bytes()) for p in private.files],
            "line_fingerprints": sorted(fingerprints),
            "logs": logs, "matches": matches, "errors": errors,
            "scope": "Observed tool events and native metadata; a clean audit does not prove isolation."}
