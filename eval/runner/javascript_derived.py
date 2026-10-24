"""Bounded, static reduction of session-authored JavaScript data.

This is deliberately a small language, not a JavaScript runtime. Nothing from
the captured program is executed by Python, Node, a shell or a host helper.
Concrete arguments still go through the ordinary access audit. Provenance by
itself is insufficient: concatenating innocent strings can create a new path.
"""

from dataclasses import dataclass, field
from bisect import bisect_left
import json
import re
from typing import Any

from eval.runner.javascript import literal


class Unsupported(ValueError):
    """The program cannot be proven within the supported static subset."""


# Only the two observed FILE-header patterns have bounded, known semantics.
PATTERNS = {
    r'^FILE ([^\n]+) SHA256 ([a-f0-9]{64})\n([\s\S]*?)(?=^FILE |\s*$)',
    r'^FILE (\S+) SHA256 [a-f0-9]{64}\n',
}
LEX = re.compile(
    r'''\s+|//[^\n]*|/\*[\s\S]*?\*/|"(?:[^"\\]|\\[\s\S])*"|'(?:[^'\\]|\\[\s\S])*'|'''
    r'''`(?:[^`\\]|\\[\s\S])*`|/(?:[^/\\\n]|\\.)+/[a-z]*|'''
    r'''[A-Za-z_$][\w$]*|\d+|\.\.\.|=>|\+\+|===|!==|<=|>=|==|!=|[^\s]''')
Node = tuple[Any, ...]
GLOBALS = {'load', 'store', 'save', 'text', 'notify', 'tools', 'JSON', 'Object', 'Promise', 'Set'}
METHODS = {'stringify', 'fromEntries', 'all', 'allSettled', 'matchAll', 'filter', 'map', 'has', 'slice'}
@dataclass(frozen=True)
class Unobserved:
    """A result whose actual contents were not captured by this static reducer."""

    path: tuple[str | int, ...] = ()


UNKNOWN = Unobserved()
OPAQUE = object()


def manifest_matches(pattern: str, value: str) -> list[dict[Any, Any]]:
    """Implement the measured regexps without a quadratic whitespace lookahead."""
    if pattern == r'^FILE (\S+) SHA256 [a-f0-9]{64}\n':
        return [{0: m[0], 1: m[1], 'index': m.start()} for m in re.finditer(pattern, value, re.MULTILINE)]
    boundaries: set[int] = set()
    offset = 0
    for line in value.split('\n'):
        if line.startswith('FILE '):
            boundaries.add(offset)
        boundaries.add(offset + len(line.rstrip(' \t\v\f\r')))
        offset += len(line) + 1
    ordered = sorted(boundaries)
    records = []
    for match in re.finditer(r'^FILE ([^\n]+) SHA256 ([a-f0-9]{64})\n', value, re.MULTILINE):
        end = ordered[bisect_left(ordered, match.end())]
        records.append({0: value[match.start():end], 1: match[1], 2: match[2],
                        3: value[match.end():end], 'index': match.start()})
    return records


class Parser:
    """Parse the whole input before reducing any argument or helper write."""

    def __init__(self, source: str) -> None:
        if len(source) > 65536 or not source.isascii():
            raise Unsupported('source_limit')
        self.tokens = [m[0] for m in LEX.finditer(source)
                       if not m[0].isspace() and not m[0].startswith(('//', '/*'))]
        self.pos = 0

    def peek(self) -> str:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ''

    def take(self, token: str | None = None) -> str:
        value = self.peek()
        if not value or token is not None and value != token:
            raise Unsupported('syntax')
        self.pos += 1
        return value

    def statements(self, closing: str = '') -> list[Node]:
        nodes = []
        while self.peek() and self.peek() != closing:
            nodes.append(self.statement())
        if closing:
            self.take(closing)
        return nodes

    def statement(self) -> Node:
        token = self.peek()
        if token in {'const', 'let'}:
            self.take()
            name = self.take()
            self.take('=')
            node = ('bind', name, self.expression(), token)
        elif token == '{':
            self.take()
            return ('block', self.statements('}'))
        elif token == 'for':
            self.take()
            self.take('(')
            initial = self.statement()
            condition = self.expression()
            self.take(';')
            update = self.expression()
            self.take(')')
            return ('for', initial, condition, update, self.statement())
        else:
            node = ('expr', self.expression())
        self.take(';')
        return node

    def expression(self, minimum: int = 0) -> Node:
        token = self.take()
        decoded = literal(token)
        if decoded is not None:
            if not decoded.isascii():
                raise Unsupported('non_ascii_literal')
            node = ('value', decoded)
        elif token.isdecimal():
            if len(token) > 16 or int(token) > 2**53 - 1 or len(token) > 1 and token.startswith('0'):
                raise Unsupported('number_limit')
            node = ('value', int(token))
        elif token in {'true', 'false', 'null'}:
            node = ('value', {'true': True, 'false': False, 'null': None}[token])
        elif token.startswith('/') and token.count('/') >= 2:
            pattern, flags = token[1:].rsplit('/', 1)
            if pattern not in PATTERNS or flags != 'gm':
                raise Unsupported('regexp')
            node = ('regex', pattern)
        elif token == 'await':
            node = ('await', self.expression(12))
        elif token == 'new':
            self.take('Set')
            self.take('(')
            node = ('set', self.expression())
            self.take(')')
        elif token == '-':
            node = ('negative', self.expression(12))
        elif token == '(':
            node = self.expression()
            self.take(')')
        elif token in {'[', '{'}:
            entries: list[Any] = []
            close = ']' if token == '[' else '}'
            while self.peek() != close:
                if self.peek() == '...':
                    self.take()
                    entries.append(('spread', self.expression()))
                elif token == '{':
                    key = self.take()
                    name = literal(key) if literal(key) is not None else key
                    self.take(':')
                    entries.append((name, self.expression()))
                else:
                    entries.append(('item', self.expression()))
                if self.peek() != ',':
                    break
                self.take()
            self.take(close)
            node = ('array' if token == '[' else 'object', entries)
        elif re.fullmatch(r'[A-Za-z_$][\w$]*', token):
            node = ('name', token)
        else:
            raise Unsupported('expression')
        precedence = {'=': 1, '?': 2, '===': 4, '!==': 4, '==': 4, '!=': 4,
                      '<': 5, '>': 5, '<=': 5, '>=': 5, '+': 7, '-': 7, '*': 8}
        while self.peek():
            op = self.peek()
            if op == '=>' and minimum == 0 and node[0] == 'name':
                self.take()
                node = ('lambda', node[1], self.expression())
            elif op == '.' and minimum <= 14:
                self.take()
                node = ('member', node, ('value', self.take()))
            elif op == '[' and minimum <= 14:
                self.take()
                node = ('index', node, self.expression())
                self.take(']')
            elif op == '(' and minimum <= 14:
                self.take()
                args = []
                while self.peek() != ')':
                    args.append(self.expression())
                    if self.peek() != ',':
                        break
                    self.take()
                self.take(')')
                node = ('call', node, args, self.pos)
            elif op == '++' and minimum <= 13:
                self.take()
                node = ('increment', node)
            elif op in precedence and precedence[op] >= minimum:
                self.take()
                if op == '?':
                    yes = self.expression()
                    self.take(':')
                    node = ('conditional', node, yes, self.expression(2))
                else:
                    node = ('binary', op, node, self.expression(precedence[op] + (op != '=')))
            else:
                break
        return node


def children(node: Node) -> list[Node]:
    """Return AST children without confusing object-entry tuples with nodes."""
    kind = node[0]
    if kind in {'array', 'object'}:
        return [entry[1] for entry in node[1]]
    if kind == 'block':
        return node[1]
    if kind == 'call':
        return [node[1], *node[2]]
    return [value for value in node[1:] if isinstance(value, tuple)]


def validate(nodes: list[Node]) -> set[int]:
    """Reject hidden sources, aliases and unenumerable tool calls in all branches."""
    bindings: set[str] = set()
    names: set[str] = set()
    sites: set[int] = set()

    def visit(node: Node, parent: Node | None = None) -> None:
        kind = node[0]
        if kind in {'bind', 'lambda'}:
            name = node[1]
            if name in GLOBALS or not re.fullmatch(r'[A-Za-z_$][\w$]*', name):
                raise Unsupported('shadowed_helper')
            bindings.add(name)
        if kind == 'name':
            names.add(node[1])
            if node[1] == 'tools' and not (parent and parent[0] == 'member' and parent[1] is node):
                raise Unsupported('tool_alias')
        if kind in {'member', 'index'}:
            if kind == 'index' and node[1] == ('name', 'tools'):
                raise Unsupported('computed_tool_access')
            if node[1] == ('name', 'tools'):
                if node[2][0] != 'value' or not isinstance(node[2][1], str):
                    raise Unsupported('dynamic_tool')
                if not parent or parent[0] != 'call' or parent[1] is not node:
                    raise Unsupported('tool_reference')
            if node[2][0] == 'value' and node[2][1] in {'constructor', '__proto__', 'prototype'}:
                raise Unsupported('reflection')
        if kind == 'call':
            callee = node[1]
            if callee[0] == 'member' and callee[1] == ('name', 'Promise') and not (
                    parent and parent[0] == 'await' and parent[1] is node):
                raise Unsupported('unawaited_collection')
            if callee[0] == 'member' and callee[1] == ('name', 'tools'):
                sites.add(node[3])
            elif callee[0] == 'member':
                if callee[2][0] != 'value' or callee[2][1] not in METHODS:
                    raise Unsupported('unknown_method')
            elif callee[0] != 'name' or callee[1] not in {'load', 'store', 'save', 'text', 'notify'}:
                raise Unsupported('unknown_callable')
        if kind in {'binary', 'increment'} and (kind == 'increment' or node[1] == '='):
            target = node[1] if kind == 'increment' else node[2]
            if kind == 'increment' and not (
                    parent and parent[0] == 'for' and parent[3] is node and
                    parent[1][0] == 'bind' and parent[1][3] == 'let' and
                    target == ('name', parent[1][1])):
                raise Unsupported('increment_scope')
            if kind == 'binary' and target[0] == 'name':
                raise Unsupported('binding_assignment')
            if target[0] == 'name' and target[1] in GLOBALS:
                raise Unsupported('helper_mutation')
            if target[0] in {'member', 'index'} and target[1][0] == 'name' and target[1][1] in GLOBALS:
                raise Unsupported('builtin_mutation')
        for child in children(node):
            visit(child, node)

    for node in nodes:
        visit(node)
    if names - bindings - GLOBALS:
        raise Unsupported('unknown_source')
    return sites


@dataclass
class Reduction:
    commands: list[dict[str, Any]] = field(default_factory=list)
    patches: list[str] = field(default_factory=list)
    writes: dict[str, Any] = field(default_factory=dict)
    sites: set[int] = field(default_factory=set)
    steps: int = 0
    displays: list[Any] = field(default_factory=list)
    saved: dict[str, Any] = field(default_factory=dict)

    def value(self, node: Node, env: dict[str, Any], saved: dict[str, Any]) -> Any:
        self.steps += 1
        if self.steps > 20000:
            raise Unsupported('step_limit')
        kind = node[0]
        if kind == 'value':
            return node[1]
        if kind == 'await':
            return self.value(node[1], env, saved)
        if kind == 'name':
            if node[1] not in env:
                raise Unsupported('unbound_value')
            return env[node[1]]
        if kind == 'regex':
            return node
        if kind == 'lambda':
            return (node, dict(env))
        if kind == 'negative':
            return -self.value(node[1], env, saved)
        if kind == 'set':
            values = self.value(node[1], env, saved)
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise Unsupported('set_values')
            return set(values)
        if kind in {'array', 'object'}:
            result: Any = [] if kind == 'array' else {}
            opaque = False
            for key, expression in node[1]:
                value = self.value(expression, env, saved)
                if key == 'spread':
                    if isinstance(value, Unobserved):
                        opaque = True
                    else:
                        if len(result) + len(value) > 4096:
                            raise Unsupported('collection_limit')
                        result.extend(value) if isinstance(result, list) else result.update(value)
                elif kind == 'array':
                    result.append(value)
                else:
                    if key in {'__proto__', 'constructor', 'prototype'} or key in result:
                        raise Unsupported('object_key')
                    result[key] = value
                if len(result) > 4096:
                    raise Unsupported('collection_limit')
            return OPAQUE if opaque else result
        if kind in {'member', 'index'}:
            value, key = (self.value(part, env, saved) for part in node[1:])
            if isinstance(value, Unobserved) and type(key) in {str, int}:
                return Unobserved((*value.path, key))
            if key == 'length' and isinstance(value, (list, str)):
                return len(value)
            if isinstance(value, dict):
                return value[key]
            if isinstance(value, (list, str)) and type(key) is int and 0 <= key < len(value):
                return value[key]
            raise Unsupported('member')
        if kind == 'conditional':
            condition = self.value(node[1], env, saved)
            if type(condition) is not bool:
                raise Unsupported('conditional_coercion')
            return self.value(node[2] if condition else node[3], env, saved)
        if kind in {'increment', 'binary'}:
            if kind == 'increment':
                target, value = node[1], self.value(node[1], env, saved) + 1
            elif node[1] == '=':
                target, value = node[2], self.value(node[3], env, saved)
            else:
                left, right = self.value(node[2], env, saved), self.value(node[3], env, saved)
                op = node[1]
                if op == '+':
                    if type(left) is not type(right) or type(left) not in {int, str}:
                        raise Unsupported('coercion')
                    value = left + right
                    concrete(value)
                    return value
                if op == '-':
                    if type(left) is not int or type(right) is not int:
                        raise Unsupported('numeric_coercion')
                    value = left - right
                    concrete(value)
                    return value
                if op == '*':
                    raise Unsupported('multiplication')
                if type(left) is not type(right) or type(left) not in {int, str, bool, type(None)}:
                    raise Unsupported('comparison_coercion')
                if op in {'===', '=='}:
                    return type(left) is type(right) and left == right
                if op in {'!==', '!='}:
                    return type(left) is not type(right) or left != right
                return {'<': lambda: left < right, '>': lambda: left > right,
                        '<=': lambda: left <= right, '>=': lambda: left >= right}[op]()
            if target[0] == 'name' and target[1] in env:
                concrete(value)
                env[target[1]] = value
            elif target[0] in {'member', 'index'}:
                obj = self.value(target[1], env, saved)
                key = self.value(target[2], env, saved)
                if not isinstance(obj, dict) or not isinstance(key, str) or key in {'__proto__', 'constructor', 'prototype'}:
                    raise Unsupported('assignment')
                obj[key] = value
            else:
                raise Unsupported('assignment')
            return value - 1 if kind == 'increment' else value
        if kind != 'call':
            raise Unsupported('value')
        callee, expressions = node[1:3]
        args = [self.value(arg, env, saved) for arg in expressions]
        if callee[0] == 'name':
            name = callee[1]
            if name in {'text', 'notify'}:
                if name == 'text' and len(args) == 1:
                    self.displays.append(args[0])
                return OPAQUE  # JS undefined is not JSON null.
            if name == 'load' and len(args) == 1 and isinstance(args[0], str):
                if args[0] not in self.writes and args[0] not in saved:
                    raise Unsupported('unknown_store_key')
                value = self.writes.get(args[0], saved.get(args[0]))
                if not isinstance(value, str):
                    raise Unsupported('non_text_load')
                return value
            if name in {'store', 'save'} and len(args) == 2 and isinstance(args[0], str):
                self.writes[args[0]] = args[1]
                return OPAQUE
            raise Unsupported('helper_arguments')
        receiver, method = callee[1], callee[2]
        if method[0] != 'value':
            raise Unsupported('computed_method')
        name = method[1]
        if receiver == ('name', 'tools'):
            self.sites.add(node[3])
            if name == 'apply_patch' and len(args) == 1 and expressions[0][0] == 'value' and isinstance(args[0], str):
                self.patches.append(args[0])
                return UNKNOWN
            if name != 'exec_command' or len(args) != 1 or not isinstance(args[0], dict):
                raise Unsupported('unsupported_tool')
            command = args[0]
            if not isinstance(command.get('cmd'), str):
                raise Unsupported('unobserved_tool_argument')
            # Do not allow an unknown result nested inside a command/metadata.
            concrete(command)
            self.commands.append(command)
            return UNKNOWN
        if receiver == ('name', 'JSON') and name == 'stringify' and len(args) == 1:
            concrete(args[0])
            return json.dumps(args[0], ensure_ascii=False, separators=(',', ':'))
        if receiver == ('name', 'Object') and name == 'fromEntries' and len(args) == 1:
            if not isinstance(args[0], list) or not all(
                    isinstance(entry, list) and len(entry) == 2 and isinstance(entry[0], str) for entry in args[0]):
                raise Unsupported('entry_key_coercion')
            return dict(args[0])
        if receiver == ('name', 'Promise') and name in {'all', 'allSettled'} and len(args) == 1:
            if not isinstance(args[0], list):
                raise Unsupported('promise_arguments')
            return args[0] if name == 'all' else [{'status': OPAQUE, 'value': value} for value in args[0]]
        value = self.value(receiver, env, saved)
        if name == 'matchAll' and isinstance(value, str) and len(args) == 1 and args[0][0] == 'regex':
            if len(value) > 65536 or not value.isascii() or re.search(r'[\r\x1c-\x1f]', value):
                raise Unsupported('regexp_input_limit')
            return manifest_matches(args[0][1], value)
        if name in {'filter', 'map'} and isinstance(value, list) and len(args) == 1:
            callback, captured = args[0]
            if callback[0] != 'lambda':
                raise Unsupported('callback')
            results = [self.value(callback[2], dict(captured, **{callback[1]: item}), saved) for item in value]
            if name == 'filter' and not all(type(result) is bool for result in results):
                raise Unsupported('filter_coercion')
            return results if name == 'map' else [item for item, keep in zip(value, results) if keep]
        if name == 'has' and isinstance(value, set) and len(args) == 1:
            return args[0] in value
        if name == 'slice' and isinstance(value, (str, list)) and 1 <= len(args) <= 2 and all(type(i) is int for i in args):
            return value[args[0]:args[1] if len(args) == 2 else None]
        raise Unsupported('method')

    def completed(self, output: Any) -> dict[str, Any]:
        """Bind only one unmodified text(result) from one audited tool call.

        Display transformations, multiple results, missing/ambiguous blocks
        and truncated JSON cannot establish the original tool value. The
        caller audits the output before using any exported helper state.
        """
        observed: Any = None
        if self.displays == [UNKNOWN] and len(self.commands) == 1 and not self.patches:
            if isinstance(output, list) and len(output) == 1 and isinstance(output[0], dict):
                output = output[0].get('text') if output[0].get('type') == 'text' else None
            if isinstance(output, str):
                try:
                    observed = json.loads(output)
                except ValueError:
                    pass

        def bind(value: Any) -> Any:
            if isinstance(value, Unobserved):
                if observed is None:
                    raise Unsupported('unobserved_output')
                resolved = observed
                for key in value.path:
                    resolved = resolved[key]
                concrete(resolved)
                return resolved
            if isinstance(value, dict):
                return {key: bind(item) for key, item in value.items()}
            if isinstance(value, list):
                return [bind(item) for item in value]
            concrete(value)
            return value

        result = dict(self.saved)
        for key, value in self.writes.items():
            result.pop(key, None)
            if (self.commands or self.patches) and observed is None:
                continue
            if not isinstance(value, (str, Unobserved)):
                continue
            try:
                resolved = bind(value)
                if isinstance(resolved, str):
                    result[key] = resolved
            except (Unsupported, KeyError, IndexError, TypeError):
                pass
        concrete(result)
        return json.loads(json.dumps(result))

    def statement(self, node: Node, env: dict[str, Any], saved: dict[str, Any]) -> None:
        kind = node[0]
        if kind == 'bind':
            if node[1] in env:
                raise Unsupported('rebound_name')
            env[node[1]] = self.value(node[2], env, saved)
        elif kind == 'expr':
            self.value(node[1], env, saved)
        elif kind == 'block':
            local = dict(env)
            for child in node[1]:
                self.statement(child, local, saved)
        elif kind == 'for':
            local = dict(env)
            self.statement(node[1], local, saved)
            for _ in range(4096):
                condition = self.value(node[2], local, saved)
                if type(condition) is not bool:
                    raise Unsupported('loop_coercion')
                if not condition:
                    break
                self.statement(node[4], local, saved)
                self.value(node[3], local, saved)
            else:
                raise Unsupported('loop_limit')
        else:
            raise Unsupported('statement')


def concrete(value: Any, _budget: list[int] | None = None) -> None:
    """Require JSON-shaped finite data; never treat missing tool output as text."""
    budget = _budget if _budget is not None else [20000, 1000000]
    budget[0] -= 1
    if budget[0] < 0 or budget[1] < 0:
        raise Unsupported('data_limit')
    if isinstance(value, str):
        budget[1] -= len(value)
        if not value.isascii() or budget[1] < 0:
            raise Unsupported('string_limit')
        return
    if type(value) is int:
        if abs(value) > 2**53 - 1:
            raise Unsupported('number_limit')
        return
    if type(value) is bool or value is None:
        return
    if isinstance(value, (list, dict)):
        if isinstance(value, dict) and not all(type(key) is str and key.isascii() and not key.isdecimal() for key in value):
            raise Unsupported('object_keys')
        for item in value.values() if isinstance(value, dict) else value:
            concrete(item, budget)
        return
    raise Unsupported('unobserved_value')


def reduce_script(source: str, saved: dict[str, Any]) -> Reduction | None:
    """Resolve only complete, source-closed programs with concrete tool arguments."""
    try:
        parser = Parser(source)
        nodes = parser.statements()
        sites = validate(nodes)
        result = Reduction()
        env: dict[str, Any] = {}
        for node in nodes:
            result.statement(node, env, saved)
        if result.sites != sites:
            raise Unsupported('unvisited_tool_site')
        result.saved = saved
        return result
    except (Unsupported, KeyError, IndexError, TypeError, ValueError, RecursionError, OverflowError):
        return None
