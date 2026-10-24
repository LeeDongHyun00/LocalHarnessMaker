"""Non-importing Python identity extraction shared by baselines and ledgers."""

from __future__ import annotations

import ast
import json

def identities(source: bytes) -> dict[str, dict[str, str]]:
    tree = ast.parse(source)
    result: dict[str, dict[str, str]] = {"name": {}, "signature": {}, "constant": {}}

    def visit(body: list[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + node.name
                if name in result["name"]:
                    raise ValueError(f"ambiguous Python binding: {name}")
                result["name"][name] = name
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    signature = name + "(" + ast.unparse(node.args) + ")"
                    if node.returns:
                        signature += " -> " + ast.unparse(node.returns)
                    if isinstance(node, ast.AsyncFunctionDef):
                        signature = "async " + signature
                    result["signature"][name] = signature
                visit(node.body, name + ".")
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        name = prefix + target.id
                        if name in result["name"]:
                            raise ValueError(f"ambiguous Python binding: {name}")
                        result["name"][name] = name
                        if node.value is not None:
                            try:
                                ast.literal_eval(node.value)
                            except (ValueError, TypeError):
                                continue
                            result["constant"][name] = ast.dump(node.value, include_attributes=False)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name != "*":
                        name = prefix + (alias.asname or alias.name.split(".")[0])
                        if name in result["name"]:
                            raise ValueError(f"ambiguous Python binding: {name}")
                        result["name"][name] = name
    visit(tree.body)
    return result


def signature_name(value: str) -> str:
    return value.removeprefix("async ").split("(", 1)[0].strip()


def signature_snapshot_bytes(source: bytes, identifiers: list[str]) -> bytes:
    """Canonical UTF-8 JSON [requested identifier, observed signature] pairs.

    Missing identifiers are represented by null, so removed/changed signatures
    differ mechanically from the pre-edit snapshot. Capture with this function.
    """
    extracted = identities(source)["signature"]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate snapshot identifiers")
    pairs = [[value, extracted.get(signature_name(value))] for value in identifiers]
    return (json.dumps(pairs, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def identifier_found(source: bytes, kind: str, value: str) -> bool:
    extracted = identities(source)
    if kind == "name":
        return value in extracted["name"]
    if kind == "signature":
        return extracted["signature"].get(signature_name(value)) == value
    # A bare constant name asserts a literal binding. NAME = literal additionally
    # pins its value; equality compares syntax trees, never eval/import execution.
    if "=" not in value:
        return value in extracted["constant"]
    name, literal = value.split("=", 1)
    expression = ast.parse(literal.strip(), mode="eval").body
    ast.literal_eval(expression)
    return extracted["constant"].get(name.strip()) == ast.dump(expression, include_attributes=False)
