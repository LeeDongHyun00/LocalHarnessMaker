"""Static contract checks without workspace access or verifier imports.

The command grammar is a conservative subset of verifier/sandbox.py. Paths are
validated lexically: target files may be created later, so existence and symlink
containment remain the verifier's runtime responsibility.
"""

import ast
import re
import shlex
from pathlib import PurePosixPath
from typing import Any


_MUTATING_CALLS = {
    "remove", "unlink", "rmdir", "rmtree", "rename", "replace", "truncate",
    "system", "popen", "exec", "eval", "execv", "execve", "spawn", "run",
    "write_text", "write_bytes", "mkdir", "touch",
}
_FILE = r"(?<![\w/])(?:[\w.-]+/)*[\w-]+\.[A-Za-z][\w-]*"


def validate_path(value: str, *, directory: bool = False) -> None:
    """Accept one unambiguous relative path, never a prose/list operand."""
    if (not value or value != value.strip() or value.startswith(("/", "~"))
            or "\\" in value or re.match(r"^[A-Za-z]:", value)
            or any(char in value for char in "\x00\n\r\t;,|<>*?[]{}")
            or ".." in PurePosixPath(value).parts
            or re.search(r"\s(?:and|or|contain\w*|has|have|must|should)\s", value, re.I)
            or (not directory and value in {".", "./"})
            or (" " in value and not PurePosixPath(value).suffix and "/" not in value)):
        raise ValueError("path must be one relative workspace path, not prose or a list")
    # Spaces in a real filename are supported; sentences and multi-file lists are not.
    if len(re.findall(_FILE, value)) > 1:
        raise ValueError("path contains multiple file operands")


def validate_command(command: str) -> None:
    """Check accepted direct Python forms without executing or resolving inputs."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    argv = list(lexer)
    if (len(argv) < 3 or argv[0] not in {"python", "python3"}
            or any(token in {";", "&&", "||", "|", ">", ">>", "<", "&"}
                   for token in argv)):
        raise ValueError("use one direct python -m py_compile/pytest/unittest or python -c check")
    if argv[1] == "-c" and len(argv) == 3:
        try:
            tree = ast.parse(argv[2])
        except SyntaxError as exc:
            raise ValueError(f"invalid Python check: {exc.msg}") from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if name in _MUTATING_CALLS:
                    raise ValueError(f"destructive or indirect execution call: {name}")
                if name == "open" and (len(node.args) > 1 or node.keywords):
                    raise ValueError("open checks must use default read-only mode")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if re.match(r"/(?:tmp|private|var|Users|home|etc|usr|opt|dev)(?:/|$)", node.value):
                    raise ValueError("absolute filesystem path in Python check")
                if "../" in node.value:
                    raise ValueError("parent traversal in Python check")
        return
    if argv[1] != "-m" or argv[2] not in {"py_compile", "pytest", "unittest"}:
        raise ValueError("unsupported Python invocation")
    module = argv[2]
    arguments = argv[3:]
    if module == "py_compile":
        if not arguments:
            raise ValueError("py_compile requires file operands")
        for token in arguments:
            if token.startswith("-"):
                raise ValueError(f"unsupported command option: {token}")
            validate_path(token)
        return
    discover = module == "unittest" and bool(arguments) and arguments[0] == "discover"
    tokens = arguments[1:] if discover else arguments
    flags = ({"-v", "-q", "-b", "-f"} if module == "unittest" else
             {"-q", "-v", "-s", "-x", "-rA", "--tb=short", "--disable-warnings"})
    operands = {"-k"} | ({"-s", "-p", "-t"} if discover else set())
    if module == "pytest":
        operands.add("-p")
    index = positional = 0
    while index < len(tokens):
        token = tokens[index]
        if token in flags:
            index += 1
            continue
        option = token[:2]
        if option in operands:
            if token == option:
                index += 1
                if index >= len(tokens) or tokens[index].startswith("-"):
                    raise ValueError(f"missing command option value: {option}")
                value = tokens[index]
            else:
                value = token[2:]
            if not value:
                raise ValueError(f"missing command option value: {option}")
            if option in {"-s", "-t"}:
                validate_path(value, directory=True)
            elif option == "-p":
                if module == "pytest" and value != "no:cacheprovider":
                    raise ValueError("unsupported pytest plugin")
                if module == "unittest" and ("/" in value or "\\" in value or value in {".", ".."}):
                    raise ValueError("discovery pattern must be a filename pattern")
        elif token.startswith("-"):
            raise ValueError(f"unsupported command option: {token}")
        elif discover:
            if positional in {0, 2}:
                validate_path(token, directory=True)
            elif positional == 1:
                if "/" in token or "\\" in token or token in {".", ".."}:
                    raise ValueError("discovery pattern must be a filename pattern")
            else:
                raise ValueError("too many unittest discover arguments")
            positional += 1
        elif module == "unittest" and "/" not in token and not token.endswith(".py"):
            if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", token):
                raise ValueError("unsupported unittest target")
        else:
            validate_path(token.split("::", 1)[0], directory=True)
        index += 1


def criterion_errors(contract: dict[str, Any]) -> dict[int, str]:
    """Return every invalid criterion index and its actionable repair reason."""
    errors: dict[int, str] = {}
    for index, item in enumerate(contract["success_criteria"]):
        check = item["check"]
        try:
            if check["type"] in {"file_exists", "regex"}:
                validate_path(check["path"])
            if check["type"] == "regex":
                try:
                    re.compile(check["pattern"])
                except (re.error, OverflowError, RecursionError) as exc:
                    raise ValueError(f"invalid Python regex: {exc}; put global inline flags at the start") from exc
            elif check["type"] == "command":
                validate_command(check["command"])
            elif check["type"] == "llm_judge":
                rubric = check["rubric"]
                if re.search(
                    r"\b(?:test|execution|runtime|command|pytest|unittest)\s+(?:execution\s+)?"
                    r"(?:results?|outputs?|logs?|exit\s+codes?|passed|passes|succeeds|success)\b"
                    r"|\b(?:tests?|commands?|pytest|unittest)\s+(?:(?:all|must|should|have|has)\s+)*(?:pass|passed|passes|succeed|succeeds|ran|were run)\b"
                    r"|\b(?:run|execute)\s+(?:the\s+)?(?:tests?|pytest|unittest|commands?)\b",
                    rubric, re.I,
                ):
                    raise ValueError("llm_judge must be decidable from workspace files alone; use a command criterion for execution evidence")
        except ValueError as exc:
            errors[index] = str(exc)
    return errors


def repair_target_stops(contract: dict[str, Any], request: str) -> None:
    """Remove missing-target prerequisites when a request explicitly asks for work.

    This lexical repair is deliberately bounded to named files in action clauses.
    Broader semantic contradictions are covered by the prompt, not guessed here.
    """
    targets: set[str] = set()
    for clause in re.split(r"[\n;]|(?<=[.!?])\s+", request):
        action = re.search(r"\b(?:add|create|write|edit|modify|update|fix|implement|extend|change)\b", clause, re.I)
        if action and not re.search(r"\b(?:not|never|don't|mustn't)\s*$", clause[:action.start()], re.I):
            outputs = re.split(
                r"\b(?:using|from|based on|given|provided|supplied|by reading|reading|read)\b",
                clause[action.end():], maxsplit=1, flags=re.I,
            )[0]
            targets.update(re.findall(_FILE, outputs))
    kept: list[str] = []
    for condition in contract["stop_conditions"]:
        files = set(re.findall(_FILE, condition))
        affected = files & targets
        missing = re.search(r"\b(?:missing|unavailable|absent|inaccessible|nonexistent|not\s+(?:exist|found|present|available)|cannot\s+(?:find|read|access)|does\s+not\s+exist|doesn['’]t\s+exist)\b", condition, re.I)
        if affected and missing and files <= targets:
            for path in sorted(affected):
                assumption = f"{path}: the file may not exist yet and may be created."
                if assumption not in contract["assumptions"]:
                    contract["assumptions"].append(assumption)
        else:
            kept.append(condition)
    contract["stop_conditions"] = kept
