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
from typing import Any, Callable
from urllib.parse import unquote

from eval.runner.javascript import tool_calls
from eval.runner.javascript_derived import Reduction, reduce_script, storage_identifiers
from eval.runner.fingerprint_history import FingerprintHistory, input_texts


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
    def load(cls, root: Path, task_id: str, repository: Path, *, task_root: str | None = None) -> "PrivateGraders":
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
                   repository / (task_root or ("eval/tasks-v2" if task_id.startswith("v2-") else "eval/tasks")))

    def line_fingerprints(self, cache: "FingerprintCache | None" = None) -> set[str]:
        """Return hidden-line hashes, optionally sharing an invocation snapshot."""
        if cache is not None:
            return set(cache.fingerprints(self))
        return self._compute_line_fingerprints()

    def _compute_line_fingerprints(self) -> set[str]:
        """Analyze unique immediate task graders against the public corpus once."""
        public: list[str] = []
        if self.public_root is not None:
            roots = {self.public_root}
            # Grader sources span versions, so public exclusions must too.
            if self.public_root.name in {"tasks", "tasks-v2"}:
                roots.update(self.public_root.parent / name for name in ("tasks", "tasks-v2"))
            for root in sorted(roots):
                for task in root.iterdir() if root.is_dir() else ():
                    if task.is_dir():
                        public.extend(public_inputs(task))
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
            decorator_lines: set[int] = set()
            for node in nodes:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    for decorator in node.decorator_list:
                        decorator_lines.update(range(decorator.lineno, (decorator.end_lineno or decorator.lineno) + 1))
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
                    if (len(line) >= 16 and line not in public_lines and number not in decorator_lines
                            and not generic_grader_line(line)):
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
                return "\n".join(self.redact(line) for line in text.split("\n"))
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


def public_inputs(task: Path) -> list[str]:
    """Read shipped task inputs, never an executor's mutable workspace."""
    paths = [task / name for name in ("prompt.md", "day2.md", "expected.json", "meta.json")]
    paths.extend((task / "workspace").rglob("*"))
    return [path.read_text(errors="replace") for path in paths if path.is_file()]


def generic_grader_line(line: str) -> bool:
    """Exclude Python scaffolding that cannot establish private provenance."""
    return (not line or line.startswith(("#", "@", "import ", "from "))
            or not re.search(r"\w", line)
            or bool(re.fullmatch(r"class\s+\w+\s*\(\s*(?:unittest\.)?TestCase\s*\)\s*:", line))
            or bool(re.fullmatch(r"(?:async\s+)?def\s+test_\w+\s*\(\s*self\s*\)\s*(?:->\s*None\s*)?:", line))
            or bool(re.match(r"if\s+__name__\s*==", line)))


def normalize_line(line: str) -> str:
    """Ignore indentation/spacing, retaining only a digest in audit records."""
    return " ".join(line.split())


def unwrap_shell(command: str) -> str:
    """Remove literal executor shell wrappers while preserving the inner syntax."""
    for _ in range(8):
        if not re.match(r"^\s*(?:/[^\s]+/)?(?:zsh|bash|sh|dash)\s", command):
            return command
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


def shell_data_spans(command: str, *, expansions: list[str] | None = None) -> list[tuple[int, int]]:
    """Locate heredoc bodies/delimiters and comments for shell-loop detection.

    Bodies end at literal delimiter lines, regardless of quotes in their data.
    Unquoted bodies return expansion text separately; protected-path checks
    still inspect the original command. Quoted arguments stay single words.
    """
    if "<<" not in command and "#" not in command:
        return []
    spans: list[tuple[int, int]] = []
    pending: list[tuple[str, bool, bool]] = []
    word = re.compile(r"(?:[^\s;&|()<>'\"\\]|\\.|'[^']*'|\"(?:[^\"\\]|\\.)*\")+", re.DOTALL)
    index = 0
    quote: str | None = None
    while index < len(command):
        ch = command[index]
        if quote is not None:
            if ch == "\\" and quote == '"':
                index += 2
                continue
            if ch == quote:
                quote = None
        elif ch == "\\":
            index += 2
            continue
        elif ch in "'\"":
            quote = ch
        elif ch == "#" and (index == 0 or command[index - 1] in " \t\r\n;&|()"):
            end = command.find("\n", index)
            end = len(command) if end < 0 else end
            spans.append((index, end))
            index = end
            continue
        elif command.startswith("((", index):
            # An arithmetic shift is not a heredoc redirection.
            end = command.find("))", index + 2)
            index = len(command) if end < 0 else end + 2
            continue
        elif command.startswith("<<<", index):
            index += 3
            continue
        elif command.startswith("<<", index):
            index += 2
            strip_tabs = command[index:index + 1] == "-"
            index += int(strip_tabs)
            while command[index:index + 1] in {" ", "\t"}:
                index += 1
            match = word.match(command, index)
            if match is not None:
                delimiter = shlex.split(match.group())
                if len(delimiter) == 1:
                    pending.append((delimiter[0], strip_tabs, any(ch in match.group() for ch in "\\'\"")))
                index = match.end()
            continue
        elif ch == "\n" and pending:
            index += 1
            for delimiter, strip_tabs, quoted in pending:
                start = index
                found = False
                while index < len(command):
                    end = command.find("\n", index)
                    end = len(command) if end < 0 else end + 1
                    line_start = index
                    line = command[index:end].removesuffix("\n")
                    index = end
                    if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                        found = True
                        if not quoted and expansions is not None:
                            expansions.append(command[start:line_start])
                        break
                if not found:
                    raise ValueError("Unterminated heredoc")
                spans.append((start, index))
            pending.clear()
            continue
        index += 1
    if pending:
        raise ValueError("Unterminated heredoc")
    return spans


def literal_loop_tokens(tokens: list[tuple[str, str]], command: str, *,
                        data: list[tuple[int, int]] | None = None,
                        cwd: Path | None = None, workspace: Path | None = None) -> tuple[list[tuple[str, str]], bool]:
    """Unroll one literal for loop, retaining uncertainty for every other form.

    This is operand extraction, not shell execution: inspect both sides of an
    if and every literal iteration, even when a file does not currently exist.
    Rejected forms retain their original tokens so concrete access still wins.
    """
    separators = {";", "&&", "||", "|", "&"}
    data = shell_data_spans(command) if data is None else data
    loops: list[int] = []
    positions: list[int] = []
    offset = 0
    for i, (value, raw) in enumerate(tokens):
        position = command.index(raw, offset)
        positions.append(position)
        at_start = (i == 0 or "\n" in command[offset:position] or
                    tokens[i - 1][1] in separators | {"(", "do", "then", "else"})
        if (at_start and value == raw and value in {"for", "while", "until", "select"}
                and not any(start <= position < end for start, end in data)):
            loops.append(i)
        offset = position + len(raw)
    if not loops:
        return tokens, False
    if len(loops) != 1 or tokens[loops[0]][0] != "for":
        return tokens, True
    start = loops[0]
    if start and tokens[start - 1][1] not in separators:
        return tokens, True
    header = tokens[start + 1:]
    if (len(header) < 6 or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", header[0][1])
            or header[1] != ("in", "in")):
        return tokens, True
    variable = header[0][0]
    boundary = next((i for i in range(start + 3, len(tokens)) if tokens[i] == (";", ";")), -1)
    if boundary < 0 or tokens[boundary + 1:boundary + 2] != [("do", "do")]:
        return tokens, True
    words = tokens[start + 3:boundary]
    # Literal absolute/relative paths need no expansion. Only bounded relative
    # static globs may expand; variables and substitutions always fail closed.
    if not words or any(not value or any(ch in raw for ch in "$`{}~\\\n") or
                        raw in separators | {"(", ")"} for value, raw in words):
        return tokens, True
    resolved_words: list[str] = []
    for value, raw in words:
        if glob.has_magic(value):
            if (raw != value or Path(value).is_absolute() or ".." in Path(value).parts
                    or cwd is None or not workspace_glob(cwd / value, workspace)):
                return tokens, True
            matches = glob.glob(str(cwd / value), recursive=True)
            resolved_words.extend(str(Path(match).relative_to(cwd)) for match in matches)
            if not matches:
                resolved_words.append(value)  # Same bounded no-match rule as direct globs.
        else:
            resolved_words.append(value)
    ends = [i for i, pair in enumerate(tokens) if pair == ("done", "done")]
    if len(ends) != 1:
        return tokens, True
    end = ends[0]
    if any(begin < positions[end] + len(tokens[end][1]) and finish > positions[start]
           for begin, finish in data):
        return tokens, True
    newline_after = (end + 1 < len(tokens) and
                     "\n" in command[positions[end] + len(tokens[end][1]):positions[end + 1]])
    if (end <= boundary + 2 or tokens[end - 1] != (";", ";") or
            (end + 1 < len(tokens) and tokens[end + 1][1] not in separators and not newline_after)):
        return tokens, True
    # No other assignment, mutation, directory change or indirect shell code can
    # be allowed to alter the induction variable or the meaning of its operands.
    forbidden = {"cd", "pushd", "popd", "read", "readarray", "mapfile", "vared", "getopts",
                 "export", "unset", "typeset", "declare", "local", "readonly", "integer", "float", "let", "set",
                 "eval", "source", ".", "exec", "command", "builtin", "env", "trap", "alias", "unalias",
                 "sh", "bash", "zsh", "dash", "break", "continue", "return",
                 "case", "esac", "elif", "else", "function", "do", "{", "}"}
    outside_header = [pair for i, pair in enumerate(tokens)
                      if not start <= i < boundary + 2 and i != end
                      and not any(begin <= positions[i] < finish for begin, finish in data)]
    if (any(Path(value).name in forbidden or value == raw and any(ch in raw for ch in "()") or
            re.match(r"[A-Za-z_][A-Za-z0-9_]*(?:=|\+=|\[)", value) or
            re.search(rf"(?:\+\+|--){variable}\b|\b{variable}(?:\+\+|--)", value)
            for value, raw in outside_header) or
            any(value == "printf" for value, _ in outside_header) and
            any(value == "-v" for value, _ in outside_header)):
        return tokens, True
    body = tokens[boundary + 2:end]
    groups: list[list[tuple[str, str]]] = [[]]
    for pair in body:
        if pair[1] in separators:
            groups.append([])
        else:
            groups[-1].append(pair)
    # Only simple commands and a single if/then/fi are supported. Strip the
    # control words so recursive command flags keep their ordinary semantics.
    commands: list[list[tuple[str, str]]] = []
    conditional: str | None = None
    for group in groups:
        if not group:
            continue
        if group[0] == ("if", "if") and conditional is None:
            conditional = "condition"
            group = group[1:]
        elif group[0] == ("then", "then") and conditional == "condition":
            conditional = "body"
            group = group[1:]
        elif group == [("fi", "fi")] and conditional == "body":
            conditional = None
            continue
        if (not group or any(raw in {"if", "then", "fi", "in", "done"} for _, raw in group)
                or "$" in group[0][1] or "`" in group[0][1]):
            return tokens, True
        if (Path(group[0][0]).name in {"python", "python3", "perl", "ruby", "node"} and
                any(value in {"-c", "-e", "--eval"} for value, _ in group[1:])):
            return tokens, True
        commands.append(group)
    if conditional is not None or not commands:
        return tokens, True
    reference = re.compile(r"\$(?:\{" + variable + r"\}|" + variable + r"(?![A-Za-z0-9_]))")
    expanded: list[tuple[str, str]] = []
    for word in resolved_words:
        for group in commands:
            for value, raw in group:
                if "$" in raw or "`" in raw:
                    # Option values, redirections and embedded program text are
                    # not the ordinary filesystem words handled by this parser.
                    if value.startswith("-") or any(ch in value for ch in "=<>();@'\""):
                        return tokens, True
                    quote: str | None = None
                    position = 0
                    while position < len(raw):
                        ch = raw[position]
                        if ch in "'\"" and (quote is None or quote == ch):
                            quote = ch if quote is None else None
                        elif ch == "$":
                            match = reference.match(raw, position)
                            if (quote == "'" or match is None or
                                    quote is None and any(c.isspace() for c in word)):
                                return tokens, True
                            position = match.end()
                            continue
                        elif ch in "`\\*?[]{}~":
                            return tokens, True
                        position += 1
                    value = reference.sub(lambda _: word, value)
                    # The fully resolved word is literal; preserve word boundaries
                    # rather than feeding inserted text through a shell parser.
                    raw = shlex.quote(value)
                expanded.append((value, raw))
            expanded.append((";", ";"))
    return tokens[:start] + expanded + tokens[end + 1:], False


def command_operands(command: str, cwd: Path | None, *,
                     workspace: Path | None = None) -> tuple[list[tuple[Path, bool]], bool]:
    """Resolve supported shell operands; uncertainty never establishes cleanliness."""
    operands: list[tuple[Path, bool]] = []
    unresolved = False
    try:
        command = unwrap_shell(command)
        expansions: list[str] = []
        spans = shell_data_spans(command, expansions=expansions)
        # Shell quote parsing never enters a heredoc body. Keep line positions
        # while removing data and delimiters from operand extraction.
        for start, end in reversed(spans):
            command = command[:start] + re.sub(r"[^\n]", " ", command[start:end]) + command[end:]
        unresolved = any("$" in body or "`" in body for body in expansions)
        tokens = shell_tokens(command)
    except ValueError:
        return [], True
    tokens, loop_unknown = literal_loop_tokens(tokens, command, data=spans, cwd=cwd, workspace=workspace)
    unresolved |= loop_unknown
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
        process_patterns = executable in {"pkill", "pgrep", "killall"}
        for _, raw in group:
            # A quoted process regex's end anchor is data, not shell expansion.
            if process_patterns and re.fullmatch(r"'[^']*'", raw, flags=re.DOTALL):
                continue
            if "$" in raw or "`" in raw:
                unresolved = True
        if process_patterns:
            # These operands select processes, never files. Shell redirections
            # still need the ordinary operand audit; do not exempt their paths.
            if not any("<" in raw or ">" in raw for _, raw in group[1:]):
                continue
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
        return tool_calls('tools.' + name + '(' + source + ')') if re.fullmatch(r'\w+', name) else ([], [], True)
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
    if kind == "clock.sleep":
        item = payload.get("item")
        return (isinstance(item, dict) and
                set(item) == {"type", "kind", "id", "durationMs"} and
                item["type"] == "Extension" and item["kind"] == kind and
                isinstance(item["id"], str) and bool(item["id"]) and
                type(item["durationMs"]) is int and item["durationMs"] >= 0 and
                all(isinstance(payload.get(key), str) and payload[key]
                    for key in ("thread_id", "turn_id")) and
                all(type(payload.get(key)) is int and payload[key] >= 0
                    for key in ("started_at_ms", "completed_at_ms")) and
                payload["completed_at_ms"] >= payload["started_at_ms"])
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


def audit_retained_logs(paths: list[Path], private: PrivateGraders, *,
                        retained_context: dict[str, Any] | None = None,
                        _audit: Callable[..., dict[str, Any]] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Audit copied day-1 bytes in their original filesystem context only.

    Day-2 events always use the new workspace and protected roots. A changed
    retained log cannot inherit the historical context without invalidation.
    """
    audit = _audit or audit_logs
    if not retained_context:
        return audit(paths, private, **kwargs)
    runtime = Path(retained_context['runtime'])
    pinned = retained_context['logs']
    retained = [path for path in paths if str(path) in pinned]
    fresh = [path for path in paths if str(path) not in pinned]
    history = FingerprintHistory(private.line_fingerprints(kwargs.get('fingerprint_cache')))
    kwargs = dict(kwargs, _fingerprint_history=history)
    results = []
    if retained:
        historical = dict(kwargs, workspace=Path(retained_context['workspace']),
                          grading_roots=tuple(Path(p).resolve() for p in retained_context['grading_roots']
                                              if Path(p).resolve() != runtime.resolve()))
        results.append(audit(retained, private, **historical))
        for path in retained:
            if (not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)
                                        if p.is_relative_to(Path(retained_context['copied_runtime']))) or
                    digest(path.read_bytes()) != pinned[str(path)]):
                results[-1]['errors'].append('retained_context_log_hash_mismatch:' + path.name)
        from eval.runner.workspace_verification import verify as verify_workspace
        try:
            recorded = dict(retained_context)
            artifact_evidence = retained_context.get('workspace_artifact_evidence')
            if artifact_evidence:
                recorded['segments'] = artifact_evidence['executor_segments']
            published = retained_context.get('published_workspace')
            workspace_matches = verify_workspace(
                Path(retained_context['workspace']), recorded, artifact_evidence,
                published_workspace=Path(published) if published else None) is not None
        except (OSError, ValueError):
            workspace_matches = False
        if not workspace_matches:
            results[-1]['errors'].append('retained_context_workspace_hash_mismatch')
        if not runtime.is_absolute():
            results[-1]['errors'].append('invalid_retained_context')
    if fresh or not paths:
        current = dict(kwargs, grading_roots=(*kwargs.get('grading_roots', ()), runtime))
        results.append(audit(fresh, private, **current))
    combined = dict(results[0])
    for key in ('logs', 'matches', 'errors'):
        combined[key] = [item for result in results for item in result[key]]
    combined['resolutions'] = [item for result in results for item in result.get('resolutions', [])]
    combined['matches'].extend(history.matches())
    combined['status'] = ('access_detected' if combined['matches'] else
                          'inconclusive' if combined['errors'] else 'clean')
    return combined


def interrupted_logs(runtime: Path, segments: list[dict[str, Any]]) -> set[Path]:
    """Exempt only the absent terminal of explicitly interrupted captures."""
    return {runtime / segment["events"] for segment in segments
            if segment.get("exit_code") == -2 and segment.get("interrupted") is True}


def audit_logs(paths: list[Path], private: PrivateGraders, *, require_completion: bool = True,
               interrupted_paths: set[Path] | None = None,
               workspace: Path | None = None, repository: Path | None = None,
               grading_roots: tuple[Path, ...] = (),
               fingerprint_cache: FingerprintCache | None = None,
               _fingerprint_history: FingerprintHistory | None = None) -> dict[str, Any]:
    """Audit tool access and native metadata disclosure; retain every error."""
    matches: list[dict[str, Any]] = []
    errors: list[str] = []
    logs: list[dict[str, Any]] = []
    repository = (repository or Path(__file__).resolve().parents[2]).resolve()
    repository_canonical = canonical_path(repository)
    roots = [Path.home() / ".claude", Path.home() / ".codex", repository.parent / "codex-bridge", repository,
             private.root, *grading_roots]
    aliases = {prefix + name: Path.home() / name
               for name in (".codex", ".claude")
               for prefix in ("~/", "$HOME/", "${HOME}/")}
    fingerprints = private.line_fingerprints(fingerprint_cache)
    history = _fingerprint_history or FingerprintHistory(fingerprints)
    calls: dict[str, str] = {}
    pending_calls: set[str] = set()
    pending_items: set[str] = set()
    resolutions: list[dict[str, Any]] = []

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
        session: str | None = None
        # Helpers belong to one native session stream, never another task/log.
        # Publish stores only after the corresponding output has been audited.
        saved: dict[str, Any] = {}
        saved_session: str | None = None
        pending_stores: dict[str, Reduction] = {}
        writing_scripts: set[str] = set()
        if not data or not data.endswith(b"\n"):
            errors.append(f"empty_or_truncated_log:{path.name}")
        for number, line in enumerate(data.decode("utf-8", errors="replace").removesuffix("\n").split("\n"), 1):
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                    raise ValueError("Unsupported event")
            except (ValueError, TypeError):
                errors.append(f"malformed_event:{path.name}:{number}")
                continue
            kind = event["type"]
            if kind == 'thread.started':
                session = event.get('thread_id')
            elif kind == 'session_meta' and isinstance(event.get('payload'), dict):
                session = event['payload'].get('session_id', event['payload'].get('id'))
            if not isinstance(session, str):
                session = None
            if session != saved_session:
                saved.clear()
                pending_stores.clear()
                writing_scripts.clear()
                saved_session = session
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
                if (event_type in {"item_started", "item_completed"} and
                        isinstance(payload.get("item"), dict) and
                        payload["item"].get("type") == "Extension"):
                    extension_kind = payload["item"].get("kind")
                    if extension_kind != "clock.sleep":
                        errors.append(f"unsupported_native_item:{path.name}:{number}:{extension_kind}")
                    elif not valid_native_metadata(extension_kind, payload):
                        errors.append(f"malformed_clock.sleep:{path.name}:{number}")
                    # Extensions have no ordinary tool operands. Only the exact
                    # observed sleep shape is supported; new fields fail closed.
                    continue
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
            reduction = None
            code_script = (item_type == 'custom_tool_call' and tool == 'exec'
                           and isinstance(item.get('input'), str))
            if code_script:
                if storage_identifiers(item['input']):
                    writing_scripts.add(item.get('call_id', ''))
                # Work on a snapshot: rejected scripts must not mutate previous
                # helper values. Only this parser's complete subset can add trust.
                reduction = reduce_script(item['input'], json.loads(json.dumps(saved))) if session else None
                if pending_stores:
                    errors.append(f'overlapping_code_mode_scripts:{path.name}:{number}')
                    reduction = None
                if reduction is not None:
                    if unknown:
                        custom = reduction.commands
                        patches = reduction.patches
                        unknown = False
                        resolutions.append({'log': path.name, 'line': number, 'tool': tool,
                                            'reason': 'derived_from_audited_outputs',
                                            'evidence_sha256': digest(line.encode())})
                else:
                    # Only helper writes can change the persistent store.
                    if storage_identifiers(item['input']):
                        saved.clear()
                        pending_stores.clear()
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
                    target = canonical_path(root)
                    # Only the repository restriction has a workspace exception.
                    if target == repository_canonical and workspace is not None:
                        allowed = canonical_path(workspace)
                        if canonical == allowed or canonical.startswith(allowed + "/"):
                            continue
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
            authored_commands = [value for command_item in commands
                                 if isinstance(value := command_item.get('command', command_item.get('cmd')), str)]
            # Array-form native shell commands preserve literal code operands too.
            authored_commands.extend(shlex.join(value) for command_item in commands
                                     if isinstance(value := command_item.get('command', command_item.get('cmd')), list)
                                     and all(isinstance(word, str) for word in value))
            alignment_command = None
            if item_type == 'command_execution' and authored_commands:
                try:
                    alignment_command = unwrap_shell(authored_commands[0])
                except ValueError:
                    pass
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
            output = (item.get("output") if item_type in {"function_call_output", "custom_tool_call_output"}
                      else item.get("aggregated_output") if item_type == "command_execution" else None)
            evidence = {"log": path.name, "line": number, "tool": tool,
                        "operation": "execute" if "command" in tool or "exec" in tool else "unknown",
                        "evidence_sha256": digest(line.encode()),
                        "redacted_evidence": "Observed protected access; see external stream hash."}
            if fingerprints:
                history.observe(path=path, line=number, event=event, item=item,
                                authored=input_texts(authored_commands, patches), output=leaves(output),
                                session=session, command=alignment_command, evidence=evidence)
            for hit in sorted(hits):
                matches.append({"log": path.name, "line": number, "marker": hit, "tool": tool,
                                "operation": "read" if metadata else "execute" if "command" in tool or "exec" in tool else "unknown",
                                "evidence_sha256": digest(line.encode()), "redacted_evidence":
                                "Private location reached executor context through native metadata." if metadata else
                                "Observed protected access; see external stream hash."})
            if code_script and reduction is not None:
                # Uncertainty anywhere in the input prevents exporting state.
                if not hits and not unknown and not any(error.endswith(f':{path.name}:{number}') for error in errors):
                    pending_stores[item.get('call_id', '')] = reduction
                elif storage_identifiers(item['input']):
                    saved.clear()
                    pending_stores.clear()
            elif item_type == 'custom_tool_call_output':
                stored = pending_stores.pop(item.get('call_id', ''), None)
                failed = (item.get('is_error') is True or item.get('isError') is True or bool(item.get('error')) or
                          any(re.search(r'^(?:Script error:|Script failed|Script running with cell ID|Error executing (?:tool|code))',
                                        value.lstrip()) for value in leaves(item.get('output'))))
                yielded = any(value.lstrip().startswith('Script running with cell ID')
                              for value in leaves(item.get('output')))
                writing = item.get('call_id', '') in writing_scripts
                writing_scripts.discard(item.get('call_id', ''))
                if stored is not None and not hits and not yielded:
                    try:
                        saved = stored.completed(item.get('output'), failed=failed)
                    except (ValueError, TypeError, RecursionError, OverflowError):
                        saved.clear()
                        errors.append(f'unresolved_stored_output:{path.name}:{number}')
                elif writing and (hits or failed):
                    saved.clear()
                    pending_stores.clear()
        if require_completion and not native and not terminal and path not in (interrupted_paths or set()):
            errors.append(f"missing_terminal_event:{path.name}")
    if require_completion and (pending_calls or pending_items):
        errors.append("unfinished_tool_events")
    if not paths:
        errors.append("missing_logs")
    if _fingerprint_history is None:
        matches.extend(history.matches())
    return {"method": "access_audit", "status": "access_detected" if matches else "inconclusive" if errors else "clean",
            "root_fingerprint": digest(str(private.root).encode()),
            "grader_fingerprints": [digest(p.read_bytes()) for p in private.files],
            "line_fingerprints": sorted(fingerprints),
            "logs": logs, "matches": matches, "errors": errors,
            "resolutions": resolutions,
            "scope": "Observed tool events and native metadata; a clean audit does not prove isolation."}
