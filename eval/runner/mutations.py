"""Deterministic single-edit AST mutations; generated source stays in private storage."""

import ast
import copy
from dataclasses import dataclass
from typing import Iterator

from eval.runner.audit import digest


@dataclass(frozen=True)
class Mutation:
    """A stable content identity and private review description."""

    source: str
    kind: str
    line: int
    before: str
    after: str

    @property
    def sha256(self) -> str:
        return digest(self.source.encode())


def mutations(source: str) -> Iterator[Mutation]:
    """Visit source order, emitting each supported single-site replacement once."""
    tree = ast.parse(source)
    seen: set[str] = set()
    nodes = list(ast.walk(tree))
    for index, node in enumerate(nodes):
        edits: list[tuple[str, str, object]] = []
        if isinstance(node, ast.Compare):
            for slot, operator in enumerate(node.ops):
                for replacement in (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE):
                    if type(operator) is not replacement:
                        operators = copy.deepcopy(node.ops)
                        operators[slot] = replacement()
                        edits.append(('comparison', 'ops', operators))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            edits.append(('arithmetic', 'op', ast.Sub() if isinstance(node.op, ast.Add) else ast.Add()))
        elif isinstance(node, ast.BoolOp):
            edits.append(('boolean', 'op', ast.Or() if isinstance(node.op, ast.And) else ast.And()))
        elif isinstance(node, ast.Constant) and type(node.value) is int:
            edits.append(('integer', 'value', node.value + 1))
        elif isinstance(node, ast.Return) and node.value is not None:
            if not (isinstance(node.value, ast.Constant) and node.value.value is None):
                edits.append(('return', 'value', ast.Constant(value=None)))
        elif isinstance(node, ast.Slice):
            edits.extend(('slice', field, None) for field in ('lower', 'upper', 'step')
                         if getattr(node, field) is not None)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            edits.append(('not', '__replace__', node.operand))
        for kind, field, value in edits:
            changed = copy.deepcopy(tree)
            target = list(ast.walk(changed))[index]
            if field == '__replace__':
                class Replace(ast.NodeTransformer):
                    def visit_UnaryOp(self, candidate: ast.UnaryOp) -> ast.AST:
                        return copy.deepcopy(value) if candidate is target else self.generic_visit(candidate)
                changed = Replace().visit(changed)
                after = ast.unparse(value)
            else:
                setattr(target, field, value)
                after = ast.unparse(target)
            rendered = ast.unparse(ast.fix_missing_locations(changed)) + '\n'
            if rendered in seen:
                continue
            seen.add(rendered)
            yield Mutation(rendered, kind, node.lineno, ast.unparse(node), after)
