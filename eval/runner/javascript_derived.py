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

from eval.runner.javascript import literal, TOKEN


class Unsupported(ValueError):
    """The program cannot be proven within the supported static subset."""


# Historical FILE-header patterns retain their measured linear matcher.
PATTERNS = {
    r'^FILE ([^\n]+) SHA256 ([a-f0-9]{64})\n([\s\S]*?)(?=^FILE |\s*$)',
    r'^FILE (\S+) SHA256 [a-f0-9]{64}\n',
}
LEX = re.compile(
    r'''\s+|//[^\n]*|/\*[\s\S]*?\*/|"(?:[^"\\]|\\[\s\S])*"|'(?:[^'\\]|\\[\s\S])*'|'''
    r'''`(?:[^`\\]|\\[\s\S])*`|/(?:[^/\\\n]|\\.)+/[a-z]*|'''
    r'''[A-Za-z_$][\w$]*|\d+|\.\.\.|=>|&&|\|\||\+\+|===|!==|<=|>=|==|!=|[^\s]''')
Node = tuple[Any, ...]
GLOBALS = {'load', 'store', 'save', 'text', 'notify', 'tools', 'JSON', 'Object', 'Promise', 'Set'}
METHODS = {'stringify', 'fromEntries', 'all', 'allSettled', 'matchAll', 'filter', 'map', 'has', 'slice', 'keys', 'entries'}


@dataclass(frozen=True)
class Unobserved:
    """A result whose actual contents were not captured by this static reducer."""

    path: tuple[str | int, ...] = ()
    site: int = 0


OPAQUE = object()


@dataclass(frozen=True)
class Spread:
    """An unmodified result spread into a displayed object."""

    source: Unobserved


@dataclass(frozen=True)
class Deferred:
    """Pure computation awaiting a displayed audited result."""

    operation: str
    arguments: tuple[Any, ...]


def storage_identifiers(source: str) -> bool:
    """Strings/comments are indivisible; only helper identifiers invalidate state."""
    for match in TOKEN.finditer(source):
        token = match[0]
        if token in {'store', 'save'} or (token.startswith('`') and '${' in token
                                         and re.search(r'\b(?:store|save)\b', token)):
            return True
    return False


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


def bind_target(target: str | list[str], value: Any, env: dict[str, Any]) -> None:
    """Bind only an exact pair/array destructuring, without defaults or rest."""
    if isinstance(target, str):
        if target in GLOBALS:
            raise Unsupported('shadowed_helper')
        env[target] = value
    elif isinstance(value, list) and len(target) == len(value) and len(set(target)) == len(target):
        for name, item in zip(target, value):
            if name in GLOBALS:
                raise Unsupported('shadowed_helper')
            env[name] = item
    else:
        raise Unsupported('destructuring_value')


def walk(node: Node) -> list[Node]:
    return [node, *(child for part in children(node) for child in walk(part))]


def tool_sites(node: Node) -> bool:
    return any(part[0] == 'call' and part[1][0] == 'member' and part[1][1] == ('name', 'tools')
               for part in walk(node))


def mutating(node: Node) -> bool:
    """A branch assignment can change a later operand without calling a tool."""
    return any(part[0] == 'increment' or part[0] == 'binary' and part[1] == '=' for part in walk(node))


def effectful(node: Node) -> bool:
    return tool_sites(node) or mutating(node) or any(part[0] == 'call' and part[1] in [('name', 'store'), ('name', 'save')]
                                   for part in walk(node) if isinstance(part[1], tuple))


def required_names(nodes: list[Node], *, displays: bool = False) -> set[str]:
    """Slice bindings backwards from tool operands and helper writes only."""
    required: set[str] = set()
    bindings: dict[str, list[Node]] = {}
    all_nodes = [part for node in nodes for part in walk(node)]
    for part in all_nodes:
        if displays and part[0] == 'call' and part[1] == ('name', 'text'):
            required.update(item[1] for arg in part[2] for item in walk(arg) if item[0] == 'name')
        if part[0] == 'for' and part[1][0] == 'bind':
            required.add(part[1][1])
        if part[0] == 'expr' and effectful(part[1]):
            required.update(item[1] for item in walk(part[1]) if item[0] == 'name')
        if part[0] == 'bind':
            bindings.setdefault(part[1], []).append(part[2])
            if effectful(part[2]):
                required.update(item[1] for item in walk(part[2]) if item[0] == 'name')
        if part[0] == 'call' and (part[1] in [('name', 'store'), ('name', 'save')]
                                 if part[1][0] == 'name' else
                                 part[1][0] == 'member' and part[1][1] == ('name', 'tools')):
            for arg in part[2]:
                required.update(item[1] for item in walk(arg) if item[0] == 'name')
        if part[0] in {'for', 'for_of', 'if'} and effectful(part):
            required.update(item[1] for item in walk(part) if item[0] == 'name')
        # Member assignments populate containers subsequently used by operands.
        if part[0] == 'binary' and part[1] == '=':
            required.update(item[1] for item in walk(part) if item[0] == 'name')
    while True:
        expanded = set(required)
        for name in required:
            for expression in bindings.get(name, []):
                expanded.update(item[1] for item in walk(expression) if item[0] == 'name')
        if expanded == required:
            return required
        required = expanded


def regex_work_bound(pattern: str, options: re.RegexFlag) -> None:
    """Reject overlapping repetition and repeated unanchored search rescans.

    The stdlib parser is used only for the already validated translated syntax.
    Disjoint separators keep independently repeated atoms from backtracking
    across each other. Unanchored searches also need a mandatory first atom
    excluded from every repetition, bounding the total rescanned input.
    """
    from re import _parser as parser, _constants as constants

    alphabet = set(range(128))
    categories = {
        constants.CATEGORY_DIGIT: set(range(48, 58)),
        constants.CATEGORY_WORD: set(map(ord, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')),
        constants.CATEGORY_SPACE: set(map(ord, ' \t\r\n\v\f')),
    }
    for negative, positive in [(constants.CATEGORY_NOT_DIGIT, constants.CATEGORY_DIGIT),
                               (constants.CATEGORY_NOT_WORD, constants.CATEGORY_WORD),
                               (constants.CATEGORY_NOT_SPACE, constants.CATEGORY_SPACE)]:
        categories[negative] = alphabet - categories[positive]

    def atoms(nodes: Any) -> list[tuple[set[int], bool, bool]]:
        result = []
        for operation, argument in nodes:
            if operation == constants.AT:
                continue
            if operation == constants.SUBPATTERN:
                result.extend(atoms(argument[-1]))
                continue
            if operation in {constants.MAX_REPEAT, constants.MIN_REPEAT}:
                lower, upper, inner = argument
                members = atoms(inner)
                if any(repeated for _, _, repeated in members):
                    raise Unsupported('regexp_nested_repetition')
                characters = set().union(*(chars for chars, _, _ in members))
                result.append((characters, lower > 0 and all(required for _, required, _ in members), upper > 1))
                continue
            if operation == constants.LITERAL:
                characters = {argument}
            elif operation == constants.NOT_LITERAL:
                characters = alphabet - {argument}
            elif operation == constants.ANY:
                characters = alphabet if options & re.DOTALL else alphabet - {10}
            elif operation == constants.IN:
                characters = set()
                negate = False
                for kind, value in argument:
                    if kind == constants.NEGATE:
                        negate = True
                    elif kind == constants.LITERAL:
                        characters.add(value)
                    elif kind == constants.RANGE:
                        characters.update(range(value[0], value[1] + 1))
                    elif kind == constants.CATEGORY and value in categories:
                        characters.update(categories[value])
                    else:
                        raise Unsupported('regexp_alphabet')
                if negate:
                    characters = alphabet - characters
            else:
                raise Unsupported('regexp_atom')
            result.append((characters, True, False))
        return result

    sequence = atoms(parser.parse(pattern, options))
    repeated_sets = [chars for chars, _, repeated in sequence if repeated]
    anchored = pattern.startswith('^') and (not options & re.MULTILINE or
                                            all(10 not in chars for chars in repeated_sets))
    if repeated_sets and not anchored:
        if not sequence or not sequence[0][1] or any(sequence[0][0] & chars for chars in repeated_sets):
            raise Unsupported('regexp_search_overlap')
    active: set[int] = set()
    for characters, required, repeated in sequence:
        if repeated:
            if active & characters:
                raise Unsupported('regexp_repetition_overlap')
            active.update(characters)
        elif required and not active & characters:
            active.clear()


def regex_matches(pattern: str, flags: str, value: str) -> list[dict[Any, Any]]:
    """Translate a bounded ASCII JS regexp subset without executing JS code.

    No backreferences, lookarounds, alternation, named groups, inline flags,
    Unicode modes or nested repetition. The two historical manifest expressions
    retain their separately measured linear implementation.
    """
    if len(value) > 65536 or not value.isascii() or re.search(r'[\r\x1c-\x1f]', value):
        raise Unsupported('regexp_input_limit')
    if pattern in PATTERNS and flags == 'gm':
        return manifest_matches(pattern, value)
    if (len(pattern) > 1024 or len(set(flags)) != len(flags) or 'g' not in flags
            or set(flags) - set('gms') or not pattern.isascii()):
        raise Unsupported('regexp')
    translated: list[str] = []
    groups: list[bool] = [False]
    in_class = False
    atom = False
    repeated_atom = False
    cursor = 0
    while cursor < len(pattern):
        char = pattern[cursor]
        cursor += 1
        if char == '\\':
            if cursor >= len(pattern):
                raise Unsupported('regexp_escape')
            escape = pattern[cursor]
            cursor += 1
            if escape in 'dDsSwWnrtfv' or escape == 'b':
                translated.append('\\' + escape)
            elif escape in r'\/.^$*+?{}[]()|-':
                translated.append(re.escape(escape))
            elif escape in 'xu':
                size = 2 if escape == 'x' else 4
                digits = pattern[cursor:cursor + size]
                if len(digits) != size or not re.fullmatch('[a-fA-F0-9]+', digits) or int(digits, 16) > 127:
                    raise Unsupported('regexp_escape')
                translated.append(re.escape(chr(int(digits, 16))))
                cursor += size
            else:
                raise Unsupported('regexp_escape')
            atom = True
            repeated_atom = False
        elif in_class:
            if char == '[':
                raise Unsupported('regexp_class')
            translated.append(char)
            if char == ']':
                in_class = False
                atom = True
                repeated_atom = False
        elif char == '[':
            if pattern[cursor:cursor + 1] == ']' or pattern[cursor:cursor + 2] == '^]':
                raise Unsupported('regexp_class')
            in_class = True
            translated.append(char)
        elif char == '(':
            if pattern[cursor:cursor + 1] == '?':
                if pattern[cursor:cursor + 2] != '?:':
                    raise Unsupported('regexp_group')
                translated.append('(?:')
                cursor += 2
            else:
                translated.append('(')
            groups.append(False)
            atom = False
        elif char == ')':
            if len(groups) < 2:
                raise Unsupported('regexp_group')
            repeated_atom = groups.pop()
            groups[-1] |= repeated_atom
            atom = True
            translated.append(char)
        elif char in '*+?{':
            if not atom or repeated_atom:
                raise Unsupported('regexp_repetition')
            quantifier = char
            if char == '{':
                match = re.match(r'\d+(?:,\d*)?}', pattern[cursor:])
                if match is None:
                    raise Unsupported('regexp_repetition')
                quantifier += match[0]
                if any(int(n) > 65536 for n in re.findall(r'\d+', quantifier)):
                    raise Unsupported('regexp_repetition')
                cursor += len(match[0])
            if pattern[cursor:cursor + 1] == '?':
                quantifier += '?'
                cursor += 1
            translated.append(quantifier)
            groups[-1] = True
            atom = False
        elif char == '$':
            translated.append('$' if 'm' in flags else r'\Z')
            atom = False
        elif char in '|}':
            raise Unsupported('regexp_operator')
        else:
            translated.append(char)
            atom = char != '^'
            repeated_atom = False
    if in_class or len(groups) != 1:
        raise Unsupported('regexp_group')
    expression = ''.join(translated)
    options = re.ASCII | (re.MULTILINE if 'm' in flags else 0) | (re.DOTALL if 's' in flags else 0)
    regex_work_bound(expression, options)
    compiled = re.compile(expression, options)
    # Empty/adjacent matches have subtly different JS iteration rules.
    if compiled.match('') is not None:
        raise Unsupported('regexp_empty')
    results = []
    for match in compiled.finditer(value):
        if not match[0] or any(group is None for group in match.groups()) or len(results) >= 4096:
            raise Unsupported('regexp_match_limit')
        results.append({**dict(enumerate((match[0], *match.groups()))), 'index': match.start()})
    return results


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
        elif token == 'if':
            self.take()
            self.take('(')
            condition = self.expression()
            self.take(')')
            yes = self.statement()
            no = None
            if self.peek() == 'else':
                self.take()
                no = self.statement()
            return ('if', condition, yes, no)
        elif token == 'throw':
            self.take()
            node = ('throw', self.expression())
        elif token == 'for':
            self.take()
            self.take('(')
            if self.peek() in {'const', 'let'} and 'of' in self.tokens[self.pos:self.pos + 12]:
                self.take()
                target: Any = self.take()
                if target == '[':
                    target = [self.take()]
                    while self.peek() == ',':
                        self.take()
                        target.append(self.take())
                    self.take(']')
                self.take('of')
                values = self.expression()
                self.take(')')
                return ('for_of', target, values, self.statement())
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
            node = ('regex', pattern, flags)
        elif token == 'await':
            node = ('await', self.expression(12))
        elif token.startswith('`') and token.endswith('`'):
            parts: list[Node] = []
            cursor = 1
            # Interpolations are expressions only, with no nested braces/templates.
            for match in re.finditer(r'(?<!\\)\$\{([^{} `]*(?:[ ][^{} `]*)*)\}', token):
                raw = token[cursor:match.start()]
                decoded_part = literal('`' + raw + '`')
                if decoded_part is None:
                    raise Unsupported('template')
                parts.append(('value', decoded_part))
                inner = Parser(match[1])
                parts.append(inner.expression())
                if inner.peek():
                    raise Unsupported('template_expression')
                cursor = match.end()
            tail = literal('`' + token[cursor:-1] + '`')
            if tail is None:
                raise Unsupported('template')
            parts.append(('value', tail))
            node = ('template', parts)
        elif token == 'async':
            node = self.expression()
        elif token == 'new':
            constructor = self.take()
            if constructor != 'Set':
                node = ('opaque_new', constructor, self.expression())
                return node

            self.take('(')
            node = ('set', self.expression())
            self.take(')')
        elif token == '!':
            node = ('not', self.expression(12))
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
                    if self.peek() == ':':
                        self.take(':')
                        entries.append((name, self.expression()))
                    else:
                        entries.append((name, ('name', name)))
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
        precedence = {'=': 1, '?': 2, '||': 3, '&&': 3, '===': 4, '!==': 4, '==': 4, '!=': 4,
                      '<': 5, '>': 5, '<=': 5, '>=': 5, '+': 7, '-': 7, '*': 8}
        while self.peek():
            op = self.peek()
            if op == '=>' and minimum == 0 and node[0] in {'name', 'array'}:
                self.take()
                target = node[1] if node[0] == 'name' else [entry[1][1] for entry in node[1]]
                if node[0] == 'array' and any(entry[0] != 'item' or entry[1][0] != 'name' for entry in node[1]):
                    raise Unsupported('destructuring')
                node = ('lambda', target, self.expression())
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
    if kind in {'block', 'template'}:
        return node[1]
    if kind == 'call':
        return [node[1], *node[2]]
    return [value for value in node[1:] if isinstance(value, tuple)]


def validate(nodes: list[Node]) -> set[int]:
    """Reject hidden sources, aliases and unenumerable tool calls in all branches."""
    sites: set[int] = set()

    def visit(node: Node, parent: Node | None = None) -> None:
        kind = node[0]
        if kind == 'opaque_new' and node[1] != 'Error':
            raise Unsupported('unknown_constructor')
        if kind in {'bind', 'lambda'}:
            for name in node[1] if isinstance(node[1], list) else [node[1]]:
                if name in GLOBALS or not re.fullmatch(r'[A-Za-z_$][\w$]*', name):
                    raise Unsupported('shadowed_helper')
        if kind == 'name':
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
            elif callee[0] == 'member' and (callee[2][0] != 'value' or callee[2][1] not in METHODS | {'parse', 'test'}):
                raise Unsupported('unknown_method')
            elif callee[0] == 'name' and callee[1] not in {'load', 'store', 'save', 'text', 'notify'}:
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
    guards: list[Any] = field(default_factory=list)
    required: set[str] = field(default_factory=set)
    tool_count: int = 0
    display_required: set[str] = field(default_factory=set)
    write_displays: dict[str, int] = field(default_factory=dict)

    def value(self, node: Node, env: dict[str, Any], saved: dict[str, Any]) -> Any:
        self.steps += 1
        if self.steps > 20000:
            raise Unsupported('step_limit')
        kind = node[0]
        if kind == 'template':
            values = [self.value(part, env, saved) for part in node[1]]
            if not all(isinstance(value, str) for value in values):
                raise Unsupported('template_coercion')
            result = ''.join(values)
            concrete(result)
            return result
        if kind == 'not':
            value = self.value(node[1], env, saved)
            if type(value) is not bool:
                raise Unsupported('boolean_coercion')
            return not value
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
            for key, expression in node[1]:
                value = self.value(expression, env, saved)
                if key == 'spread':
                    if isinstance(value, Unobserved):
                        if not isinstance(result, dict) or any(isinstance(key, Spread) for key in result):
                            raise Unsupported('ambiguous_result_spread')
                        result[Spread(value)] = value
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
            return result
        if kind in {'member', 'index'}:
            value, key = (self.value(part, env, saved) for part in node[1:])
            if isinstance(value, Unobserved) and type(key) in {str, int}:
                return Unobserved((*value.path, key), value.site)
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
                if isinstance(left, (Unobserved, Deferred)) or isinstance(right, (Unobserved, Deferred)):
                    if op not in {'===', '!=='}:
                        raise Unsupported('unobserved_operation')
                    return Deferred(op, (left, right))
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
                if args[0] in self.writes and self.guards:
                    raise Unsupported('guarded_same_script_load')
                value = self.writes.get(args[0], saved.get(args[0]))
                concrete(value)
                return json.loads(json.dumps(value))
            if name in {'store', 'save'} and len(args) == 2 and isinstance(args[0], str):
                self.writes[args[0]] = args[1]
                self.write_displays[args[0]] = len(self.displays)
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
                self.tool_count += 1
                return Unobserved(site=self.tool_count)
            if name != 'exec_command' or len(args) != 1 or not isinstance(args[0], dict):
                raise Unsupported('unsupported_tool')
            command = args[0]
            if not isinstance(command.get('cmd'), str):
                raise Unsupported('unobserved_tool_argument')
            # Do not allow an unknown result nested inside a command/metadata.
            concrete(command)
            self.commands.append(command)
            self.tool_count += 1
            return Unobserved(site=self.tool_count)
        if receiver == ('name', 'JSON') and name == 'parse' and len(args) == 1:
            if isinstance(args[0], (Unobserved, Deferred)):
                return Deferred('parse', tuple(args))
            parsed = json.loads(args[0])
            concrete(parsed)
            return parsed
        if receiver == ('name', 'JSON') and name == 'stringify' and len(args) == 1:
            concrete(args[0])
            return json.dumps(args[0], ensure_ascii=False, separators=(',', ':'))
        if receiver == ('name', 'Object') and name in {'keys', 'entries'} and len(args) == 1:
            concrete(args[0])
            if not isinstance(args[0], dict):
                raise Unsupported('object_arguments')
            return list(args[0]) if name == 'keys' else [[key, item] for key, item in args[0].items()]
        if receiver == ('name', 'Object') and name == 'fromEntries' and len(args) == 1:
            if not isinstance(args[0], list) or not all(
                    isinstance(entry, list) and len(entry) == 2 and isinstance(entry[0], str) for entry in args[0]):
                raise Unsupported('entry_key_coercion')
            return dict(args[0])
        if receiver == ('name', 'Promise') and name in {'all', 'allSettled'} and len(args) == 1:
            if not isinstance(args[0], list):
                raise Unsupported('promise_arguments')
            return args[0] if name == 'all' else [
                {'status': Unobserved(site=-value.site), 'value': value}
                if isinstance(value, Unobserved) else {'status': 'fulfilled', 'value': value}
                for value in args[0]]
        value = self.value(receiver, env, saved)
        if name == 'matchAll' and isinstance(value, str) and len(args) == 1 and args[0][0] == 'regex':
            if len(value) > 65536 or not value.isascii() or re.search(r'[\r\x1c-\x1f]', value):
                raise Unsupported('regexp_input_limit')
            return regex_matches(args[0][1], args[0][2], value)
        if name in {'filter', 'map'} and isinstance(value, list) and len(args) == 1:
            callback, captured = args[0]
            if callback[0] != 'lambda':
                raise Unsupported('callback')
            results = []
            for item in value:
                local = dict(captured)
                bind_target(callback[1], item, local)
                results.append(self.value(callback[2], local, saved))
            if name == 'filter' and not all(type(result) is bool for result in results):
                raise Unsupported('filter_coercion')
            return results if name == 'map' else [item for item, keep in zip(value, results) if keep]
        if name == 'has' and isinstance(value, set) and len(args) == 1:
            return args[0] in value
        if name == 'slice' and isinstance(value, (str, list)) and 1 <= len(args) <= 2 and all(type(i) is int for i in args):
            return value[args[0]:args[1] if len(args) == 2 else None]
        raise Unsupported('method')

    def completed(self, output: Any, *, failed: bool = False) -> dict[str, Any]:
        """Reconstruct result fields only through unmodified displayed structure."""
        blocks = output if isinstance(output, list) else [output]
        observed: list[Any] = []
        raw_blocks: list[str | None] = []
        for block in blocks:
            if isinstance(block, dict) and block.get('type') in {'text', 'input_text'}:
                block = block.get('text')
            if isinstance(block, str):
                try:
                    observed.append(json.loads(block))
                    raw_blocks.append(block)
                except ValueError:
                    # The host emits a separate Script completed/timing preamble.
                    if not block.startswith(('Script completed\n', 'Script failed\n', 'Script error:')):
                        observed.append(OPAQUE)
                        raw_blocks.append(block)
            else:
                observed.append(OPAQUE)
                raw_blocks.append(None)
        results: dict[tuple[int, tuple[str | int, ...]], Any] = {}
        ambiguous: set[tuple[int, tuple[str | int, ...]]] = set()

        def record(value: Unobserved, actual: Any) -> None:
            key = (value.site, value.path)
            if key in results:
                ambiguous.add(key)
            results[key] = actual

        def compatible(shape: Any, actual: Any) -> bool:
            if isinstance(shape, Unobserved):
                return True
            if isinstance(shape, dict) and isinstance(actual, dict):
                return all(isinstance(key, Spread) or key in actual and compatible(item, actual[key])
                           for key, item in shape.items())
            if isinstance(shape, list) and isinstance(actual, list):
                return len(shape) == len(actual) and all(compatible(a, b) for a, b in zip(shape, actual))
            return type(shape) is type(actual) and shape == actual

        def align(shape: Any, actual: Any) -> None:
            if isinstance(shape, Unobserved):
                record(shape, actual)
            elif isinstance(shape, dict) and isinstance(actual, dict):
                explicit = {key for key in shape if isinstance(key, str)}
                for key, item in shape.items():
                    if isinstance(key, Spread):
                        # Explicit fields shadow unknown spread fields. Only the
                        # untouched fields may later be reconstructed.
                        for name, captured in actual.items():
                            if name not in explicit:
                                record(Unobserved((*key.source.path, name), key.source.site), captured)
                    elif key in actual:
                        align(item, actual[key])
            elif isinstance(shape, list) and isinstance(actual, list):
                for item, captured in zip(shape, actual):
                    align(item, captured)

        witnessed = 0
        if len(observed) == len(self.displays) or failed and len(observed) <= len(self.displays):
            for shape, actual, raw in zip(self.displays, observed, raw_blocks):
                if isinstance(shape, Unobserved) and shape.path == ('output',) and raw is not None:
                    record(shape, raw)
                elif compatible(shape, actual):
                    align(shape, actual)
                else:
                    results.clear()
                    break
                witnessed += 1

        def bind(value: Any) -> Any:
            if isinstance(value, Unobserved):
                candidates = [(path, actual) for (site, path), actual in results.items()
                              if site == value.site and value.path[:len(path)] == path
                              and (site, path) not in ambiguous]
                if not candidates:
                    raise Unsupported('unobserved_output')
                path, resolved = max(candidates, key=lambda candidate: len(candidate[0]))
                for key in value.path[len(path):]:
                    resolved = resolved[key]
                concrete(resolved)
                return resolved
            if isinstance(value, Deferred):
                args = [bind(arg) for arg in value.arguments]
                if value.operation == 'parse':
                    parsed = json.loads(args[0])
                    concrete(parsed)
                    return parsed
                if value.operation in {'===', '==', '!==', '!='}:
                    equal = type(args[0]) is type(args[1]) and args[0] == args[1]
                    return equal if value.operation in {'===', '=='} else not equal
                raise Unsupported('deferred_operation')
            if isinstance(value, dict):
                return {key: bind(item) for key, item in value.items()}
            if isinstance(value, list):
                return [bind(item) for item in value]
            concrete(value)
            return value

        result = dict(self.saved)
        for key, value in self.writes.items():
            result.pop(key, None)
            try:
                if failed and self.write_displays[key] >= witnessed:
                    continue
                if all(bind(guard) is True for guard in self.guards):
                    resolved = bind(value)
                    concrete(resolved)
                    result[key] = resolved
            except (Unsupported, KeyError, IndexError, TypeError, ValueError):
                pass
        concrete(result)
        return json.loads(json.dumps(result))

    def statement(self, node: Node, env: dict[str, Any], saved: dict[str, Any]) -> None:
        kind = node[0]
        if kind == 'bind':
            if node[1] not in self.required and not effectful(node[2]):
                if node[1] in self.display_required:
                    try:
                        env[node[1]] = self.value(node[2], env, saved)
                    except (Unsupported, KeyError, TypeError, ValueError):
                        pass
                return
            if node[1] in env:
                raise Unsupported('rebound_name')
            env[node[1]] = self.value(node[2], env, saved)
        elif kind == 'expr':
            if effectful(node[1]):
                self.value(node[1], env, saved)
            else:
                try:
                    self.value(node[1], env, saved)
                except (Unsupported, KeyError, TypeError, ValueError):
                    pass
        elif kind == 'throw':
            if effectful(node):
                raise Unsupported('effectful_throw')
        elif kind == 'if':
            if not effectful(node):
                return
            condition = self.value(node[1], env, saved)
            if (isinstance(condition, (Unobserved, Deferred)) and not tool_sites(node)
                    and not mutating(node) and node[3] is None):
                self.guards.append(condition)
                self.statement(node[2], env, saved)
            elif type(condition) is bool:
                branch = node[2] if condition else node[3]
                if branch is not None:
                    self.statement(branch, env, saved)
            else:
                raise Unsupported('conditional_effect')
        elif kind == 'for_of':
            try:
                values = self.value(node[2], env, saved)
                if not isinstance(values, list) or len(values) > 4096:
                    raise Unsupported('iteration')
                for item in values:
                    local = dict(env)
                    bind_target(node[1], item, local)
                    self.statement(node[3], local, saved)
            except (Unsupported, KeyError, TypeError, ValueError):
                if effectful(node):
                    raise
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
        result.required = required_names(nodes)
        result.display_required = required_names(nodes, displays=True)
        env: dict[str, Any] = {}
        for node in nodes:
            result.statement(node, env, saved)
        if result.sites != sites:
            raise Unsupported('unvisited_tool_site')
        result.saved = saved
        return result
    except (Unsupported, KeyError, IndexError, TypeError, ValueError, RecursionError, OverflowError):
        return None
