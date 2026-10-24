"""Request/configuration-owned deterministic checks; never execute model output."""

import ast
import hashlib
import json
import re
import shlex
from pathlib import Path
from typing import Any

from controller.contract_validation import validate_command, validate_path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def confined(root: Path, relative: str, *, directory: bool = False) -> Path:
    """Reject traversal, absolute paths and symlink escapes, including absent targets."""
    validate_path(relative, directory=directory)
    candidate = root / relative
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("symlink escapes declared root")
    return candidate


def unavailable(reason: str) -> dict[str, Any]:
    return {"type": "unavailable", "reason": reason}


def safe_argv(command: str | list[str], root: Path) -> list[str]:
    """Accept a conservative direct Python test/compile grammar, with no shell."""
    text = command if isinstance(command, str) else shlex.join(command)
    if any(char in text for char in "\n\r\x00;$`|&<>\\"):
        raise ValueError("unsupported shell syntax")
    argv = shlex.split(text)
    if not argv:
        raise ValueError("empty command")
    executable = argv[0]
    if executable in {"pytest", "py.test"}:
        validated = ["python", "-m", "pytest", *argv[1:]]
    elif executable in {"python", "python3", ".venv/bin/python", ".venv/bin/python3"}:
        validated = ["python", *argv[1:]]
        if "/" in executable:
            confined(root, executable)
    else:
        raise ValueError("unsupported executable; configure a supported Python check")
    # Inline programs and arbitrary modules are deliberately unavailable on v3.
    if len(validated) >= 2 and validated[1].endswith(".py"):
        confined(root, validated[1])
        if len(validated) != 2:
            raise ValueError("script arguments require a separately supported grammar")
    elif len(validated) < 3 or validated[1] != "-m":
        raise ValueError("only direct Python modules or relative scripts are supported")
    elif validated[2] == "compileall":
        for arg in validated[3:]:
            if arg == "-q":
                continue
            if arg.startswith("-"):
                raise ValueError("unsupported compileall option")
            confined(root, arg, directory=True)
    else:
        validate_command(shlex.join(validated))
    for arg in argv[1:]:
        # Include option operands and pytest node paths. Never hide escapes in flags.
        operand = arg.split("=", 1)[-1].split("::", 1)[0]
        if (operand.startswith(("/", "~")) or ".." in Path(operand).parts
                or re.match(r"^[A-Za-z]:", operand)):
            raise ValueError("absolute path or parent traversal in command")
        if "/" in operand:
            confined(root, operand, directory=True)
    return argv


def signature_bytes(path: Path, identifiers: list[str]) -> bytes:
    """Python signatures: ordered qualified names, async flag, arguments, returns.

    Serialize ASTs without source locations; function bodies are excluded.
    Consumers must use the same algorithm, rather than hashing whole files.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, Any] = {}

    def visit(node: ast.AST, prefix: str = "") -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + child.name
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[name] = [isinstance(child, ast.AsyncFunctionDef),
                                   ast.dump(child.args, include_attributes=False),
                                   ast.dump(child.returns, include_attributes=False)
                                   if child.returns is not None else None]
                visit(child, name + ".")
    visit(tree)
    names = [name.removesuffix("()") for name in identifiers]
    if not names or len(set(names)) != len(names) or any(name not in found for name in names):
        raise ValueError("configured Python signature identifier missing or duplicated")
    return json.dumps([[name, found[name]] for name in names],
                      ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _request_target(excerpt: str) -> str:
    quoted = re.findall(r"`([^`\n]+)`", excerpt)
    if not quoted and ("\\" in excerpt or re.search(r"[A-Za-z]:[/\\]", excerpt)):
        raise ValueError("unsupported absolute or Windows path")
    candidates = quoted or re.findall(r"(?<![\w/])(?:[~/.\w-]+/)*[\w.-]+\.[A-Za-z][\w-]*", excerpt)
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) != 1:
        raise ValueError("exactly one explicit file target is required")
    return candidates[0]


def _command_check(spec: dict[str, Any], root: Path, origin: str) -> dict[str, Any]:
    argv = safe_argv(spec["argv"], root)
    cwd = spec.get("cwd", ".")
    confined(root, cwd, directory=True)
    expected = spec.get("expected_exit_code", 0)
    if type(expected) is not int:
        raise ValueError("expected_exit_code must be an integer")
    return {"type": "command", "argv": argv, "cwd": cwd,
            "expected_exit_code": expected, "origin": origin}


def source_clause(request: str, excerpt: str) -> str:
    """Expand a selected excerpt to original sentence/line boundaries in code.

    A model-selected safe substring inside an unsafe command is not authority.
    Multiple distinct occurrences are ambiguous and cannot select an oracle.
    """
    contexts: set[str] = set()
    start = 0
    boundaries = [0, *[match.end() for match in re.finditer(r"\n|(?<=[.!?])\s+", request)], len(request)]
    while (index := request.find(excerpt, start)) >= 0:
        left = max(boundary for boundary in boundaries if boundary <= index)
        right = min(boundary for boundary in boundaries if boundary >= index + len(excerpt))
        contexts.add(request[left:right].strip())
        start = index + 1
    if len(contexts) != 1:
        raise ValueError("request excerpt occurs in ambiguous source clauses")
    return contexts.pop()


def derive_check(kind: str, excerpt: str, request: str, root: Path,
                 config: dict[str, Any]) -> dict[str, Any]:
    """Bindings match original request excerpts exactly; no generated text is authority."""
    try:
        if not excerpt or excerpt not in request:
            raise ValueError("source excerpt is not verbatim request text")
        rules = [rule for rule in config.get("checks", [])
                 if rule.get("source_excerpt") == excerpt and rule.get("kind") == kind]
        if len(rules) > 1:
            raise ValueError("multiple configured oracles for this excerpt")
        spec = rules[0]["check"] if rules else None
        if kind in {"named_file", "protected_file"}:
            target = _request_target(source_clause(request, excerpt))
            path = confined(root, target)
            if kind == "named_file":
                return {"type": "file_exists", "path": target}
            return {"type": "file_unchanged", "path": target,
                    "baseline_sha256": digest(path.read_bytes())}
        if kind in {"named_command", "test_command"} and spec is None:
            excerpt = source_clause(request, excerpt)
            quoted = re.findall(r"`([^`\n]+)`", excerpt)
            match = re.fullmatch(r"\s*(?:Run|Execute|Test with|Verify with)\s+(.+?)[.]?\s*", excerpt, re.I)
            direct = re.fullmatch(r"(?:python3?|\.venv/bin/python3?|pytest) .+", excerpt)
            command = quoted[0] if len(quoted) == 1 else (match[1] if match else excerpt if direct else None)
            if command is None or len(quoted) > 1:
                raise ValueError("no unambiguous request command or configured test command")
            expectation = re.search(r"\b(?:exit(?: code)?|status)\s+(-?\d+)\b", excerpt, re.I)
            # Outside prose is never silently dropped except an explicit exit expectation.
            if quoted:
                tail = excerpt[excerpt.index("`" + command + "`") + len(command) + 2:]
                if tail.strip(" .") and not expectation:
                    raise ValueError("unsupported command suffix")
            return _command_check({"argv": command,
                                   "expected_exit_code": int(expectation[1]) if expectation else 0},
                                  root, "request")
        if spec is None:
            raise ValueError("no explicitly configured oracle covering this requirement")
        if spec["type"] == "command":
            return _command_check(spec, root, "project_config")
        if kind != "constraint":
            raise ValueError("configured oracle is incompatible with requirement kind")
        if spec["type"] == "signature_snapshot":
            path = confined(root, spec["path"])
            if path.suffix != ".py":
                raise ValueError("only Python signature extraction is supported")
            baseline = signature_bytes(path, spec["identifiers"])
            return {"type": "signature_snapshot", "path": spec["path"],
                    "identifiers": spec["identifiers"], "baseline_sha256": digest(baseline)}
        if spec["type"] == "input_immutability":
            command = _command_check(spec, root, "project_config")
            inputs = [{"path": name, "sha256": digest(confined(root, name).read_bytes())}
                      for name in spec["inputs"]]
            if not inputs:
                raise ValueError("input probe needs declared fixtures")
            return {"type": "input_immutability", "argv": command["argv"],
                    "cwd": command["cwd"], "expected_exit_code": command["expected_exit_code"],
                    "inputs": inputs}
        raise ValueError("unsupported configured oracle")
    except (ValueError, OSError, KeyError, TypeError, SyntaxError) as exc:
        return unavailable(f"Check derivation unavailable: {exc}")
