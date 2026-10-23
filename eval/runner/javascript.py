"""Lexically extract direct tool calls without interpreting JavaScript glue."""

import re
from typing import Any


# Strings/comments are indivisible, so authored patch text cannot become a call.
TOKEN = re.compile(r'''//[^\n]*|/\*[\s\S]*?\*/|"(?:[^"\\]|\\[\s\S])*"|'(?:[^'\\]|\\[\s\S])*'|`(?:[^`\\]|\\[\s\S])*`|[A-Za-z_$][\w$]*|\.\.\.|\?\.|[^\s]''')


def literal(token: str) -> str | None:
    """Decode strings and substitution-free templates, never evaluate code."""
    if len(token) < 2 or token[0] not in {'"', "'", '`'} or token[-1] != token[0]:
        return None
    template = token[0] == '`'
    if template and '${' in token:
        return None
    # JavaScript normalizes raw CR/CRLF in templates, before escape decoding.
    if template:
        token = token.replace('\r\n', '\n').replace('\r', '\n')
    result: list[str] = []
    cursor = 1
    escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v",
               "\\": "\\", '"': '"', "'": "'"}
    while cursor < len(token) - 1:
        char = token[cursor]
        cursor += 1
        if char == token[0] or (not template and char in {"\n", "\r"}):
            return None
        if char != "\\":
            result.append(char)
            continue
        if cursor >= len(token) - 1:
            return None
        char = token[cursor]
        cursor += 1
        if char in escapes:
            result.append(escapes[char])
        elif char in {"\n", "\r", "\u2028", "\u2029"}:
            if char == "\r" and token[cursor:cursor + 1] == "\n":
                cursor += 1
        elif char == "0" and not token[cursor:cursor + 1].isdigit():
            result.append("\0")
        elif char in {"x", "u"}:
            length = 2 if char == "x" else 4
            braced = char == "u" and token[cursor:cursor + 1] == "{"
            end = token.find("}", cursor + 1) if braced else cursor + length
            digits = token[cursor + 1:end] if braced else token[cursor:end]
            if end < 0 or not re.fullmatch(r"[0-9a-fA-F]+", digits) or (not braced and len(digits) != length):
                return None
            value = int(digits, 16)
            if value > 0x10ffff:
                return None
            result.append(chr(value))
            cursor = end + 1 if braced else end
        elif char.isdigit():
            return None  # Legacy octal/decimal escapes depend on strict mode.
        else:
            result.append(char)  # JavaScript identity escape.
    return ("".join(result).encode("utf-16-le", errors="surrogatepass").decode("utf-16-le", errors="surrogatepass")
            if cursor == len(token) - 1 else None)


def replace_literal(value: str, pattern: str, replacement: str, *, all_matches: bool) -> str:
    """Implement string-pattern replacement, including JS dollar substitutions."""
    def units(text: str) -> str:
        data = text.encode("utf-16-le", errors="surrogatepass")
        return "".join(chr(int.from_bytes(data[i:i + 2], "little")) for i in range(0, len(data), 2))

    value, pattern, replacement = map(units, (value, pattern, replacement))
    starts = ([m.start() for m in re.finditer(re.escape(pattern), value)] if all_matches
              else [value.find(pattern)])
    pieces: list[str] = []
    cursor = 0
    for start in starts:
        if start < 0:
            continue
        end = start + len(pattern)
        substitutions = {"$": "$", "&": pattern, "`": value[:start], "'": value[end:]}
        expanded = re.sub(r"\$([$&`'])", lambda match: substitutions[match[1]], replacement)
        pieces.extend((value[cursor:start], expanded))
        cursor = end
    pieces.append(value[cursor:])
    return "".join(pieces).encode("utf-16-le", errors="surrogatepass").decode("utf-16-le", errors="surrogatepass")


def string_expression(tokens: list[str]) -> str | None:
    """Resolve only literal concatenation and literal replace/replaceAll chains."""
    cursor = 0

    def expression(depth: int = 0) -> str:
        nonlocal cursor
        if depth > 64:
            raise ValueError("Expression nesting limit")

        def term() -> str:
            nonlocal cursor
            if cursor < len(tokens) and tokens[cursor] == '(':
                cursor += 1
                value = expression(depth + 1)
                if cursor >= len(tokens) or tokens[cursor] != ')':
                    raise ValueError("Unclosed string expression")
                cursor += 1
            else:
                value = literal(tokens[cursor]) if cursor < len(tokens) else None
                cursor += 1
                if value is None:
                    raise ValueError("Nonliteral string expression")
            while cursor < len(tokens) and tokens[cursor] == '.':
                if (cursor + 6 >= len(tokens) or tokens[cursor + 1] not in {'replace', 'replaceAll'} or
                        tokens[cursor + 2] != '(' or tokens[cursor + 4] != ',' or tokens[cursor + 6] != ')'):
                    raise ValueError("Unsupported string method")
                pattern, replacement = literal(tokens[cursor + 3]), literal(tokens[cursor + 5])
                if pattern is None or replacement is None:
                    raise ValueError("Nonliteral replacement")
                value = replace_literal(value, pattern, replacement, all_matches=tokens[cursor + 1] == 'replaceAll')
                cursor += 7
            return value

        value = term()
        while cursor < len(tokens) and tokens[cursor] == '+':
            cursor += 1
            value += term()
        return value

    try:
        value = expression()
        return value if cursor == len(tokens) else None
    except (ValueError, OverflowError, RecursionError):
        return None


def command_fields(tokens: list[str], pairs: dict[int, int], tool: int) -> list[tuple[str, int, int, int]] | None:
    """Return direct command-object fields as key/position/value-span tuples."""
    if tokens[tool:tool + 5] != ['tools', '.', 'exec_command', '(', '{']:
        return None
    end = pairs.get(tool + 3, -1)
    if pairs.get(tool + 4) != end - 1:
        return None
    fields: list[tuple[str, int, int, int]] = []
    cursor = tool + 5
    while cursor < end - 1:
        position = cursor
        key = literal(tokens[cursor]) or tokens[cursor]
        if not re.fullmatch(r'[A-Za-z_]\w*', key) or tokens[cursor].startswith('`'):
            return None
        if key == 'cmd' and tokens[cursor] == key and tokens[cursor + 1] in {',', '}'}:
            fields.append((key, position, cursor, cursor + 1))
            cursor += 2
            continue
        if tokens[cursor + 1] != ':':
            return None
        start = cursor + 2
        cursor = start
        while cursor < end - 1 and tokens[cursor] != ',':
            cursor = pairs[cursor] + 1 if cursor in pairs else cursor + 1
        fields.append((key, position, start, cursor))
        cursor += 1
    return fields


def collection_commands(tokens: list[str], pairs: dict[int, int],
                        fields: dict[int, list[tuple[str, int, int, int]]]) -> dict[int, list[str]]:
    """Resolve one-use literal arrays only at direct tool command operands.

    Match all identifier occurrences across the input, including after the call.
    Extra bindings, aliases, mutations, escapes and element transformations thus
    cannot be hidden by an otherwise recognized map or for-of loop.
    """
    # Escaped identifiers and dynamic scope defeat textual binding identity.
    if any(token in {'\\', 'with'} for token in tokens):
        return {}
    slots = {start for entries in fields.values() for key, _, start, end in entries
             if key == 'cmd' and end == start + 1}
    keys = {position for entries in fields.values() for _, position, start, _ in entries
            if position != start}
    positions: dict[str, set[int]] = {}
    for i, token in enumerate(tokens):
        if i not in keys:
            positions.setdefault(token, set()).add(i)
    resolved: dict[int, list[str]] = {}
    for i, token in enumerate(tokens[:-4]):
        if (token not in {'const', 'let'} or tokens[i + 2:i + 4] != ['=', '['] or
                (i and tokens[i - 1] not in {';', '{', '}'})):
            continue
        name = tokens[i + 1]
        end = pairs.get(i + 3, -1)
        if end < 0 or (end + 1 < len(tokens) and tokens[end + 1] != ';'):
            continue
        values: list[str] = []
        cursor = i + 4
        while cursor < end:
            value = literal(tokens[cursor])
            if value is None or (cursor + 1 < end and tokens[cursor + 1] != ','):
                break
            values.append(value)
            cursor += 2 if cursor + 1 < end else 1
        if cursor != end or not values:
            continue
        uses = positions.get(name, set()) - {i + 1}
        if len(uses) != 1:
            continue
        use = next(iter(uses))
        if use <= end or any(opening < i < closing < use for opening, closing in pairs.items()
                             if tokens[opening] == '{'):
            continue
        if use in slots:
            resolved[use] = values
            continue
        # commands.map(cmd => tools.exec_command({cmd})), optionally with a
        # parenthesized single parameter or a braced callback body.
        if tokens[use + 1:use + 4] == ['.', 'map', '('] and use + 3 in pairs:
            body_end = pairs[use + 3]
            binding = use + 4
            arrow = binding + 1
            if tokens[binding:binding + 1] == ['('] and pairs.get(binding) == binding + 2:
                binding += 1
                arrow += 2
            if tokens[arrow:arrow + 2] != ['=', '>']:
                continue
            body_start = arrow + 2
            cursor = body_start
            while cursor < body_end and tokens[cursor] != ',':
                cursor = pairs[cursor] + 1 if cursor in pairs else cursor + 1
            if cursor != body_end:
                continue
        # for (const cmd of commands) { ... }, or a single unbraced statement.
        elif (use >= 5 and tokens[use - 5:use - 3] == ['for', '('] and
              tokens[use - 3] in {'const', 'let'} and tokens[use - 1] == 'of' and
              tokens[use + 1:use + 2] == [')'] and pairs.get(use - 4) == use + 1):
            binding = use - 2
            body_start = use + 2
            body_end = body_start
            if tokens[body_start:body_start + 1] == ['{']:
                body_end = pairs.get(body_start, body_start)
            else:
                while body_end < len(tokens) and tokens[body_end] != ';':
                    body_end = pairs[body_end] + 1 if body_end in pairs else body_end + 1
        else:
            continue
        element = tokens[binding]
        if element == name or not re.fullmatch(r'[A-Za-z_$][\w$]*', element):
            continue
        references = positions.get(element, set()) - {binding}
        if not references or any(ref not in slots or not body_start <= ref < body_end for ref in references):
            continue
        for ref in references:
            resolved[ref] = values
    return resolved


def tool_calls(source: str) -> tuple[list[dict[str, Any]], list[str], bool]:
    """Find every tools.name(...) call, independently of surrounding control flow."""
    tokens = [m[0] for m in TOKEN.finditer(source) if not m[0].startswith(('//', '/*'))]
    pairs: dict[int, int] = {}
    stack: list[int] = []
    unknown = False
    for i, token in enumerate(tokens):
        if token in {'(', '[', '{'}:
            stack.append(i)
        elif token in {')', ']', '}'}:
            if not stack or tokens[stack[-1]] != {')': '(', ']': '[', '}': '{'}[token]:
                unknown = True
            else:
                pairs[stack.pop()] = i
        if token in {'eval', 'Function', chr(34), chr(39), '`'} or (token.startswith('`') and '${' in token):
            unknown = True
    unknown |= bool(stack)
    # An unbound bare callable may be an indirect host-tool reference. Local
    # function declarations and the code-mode display helpers are ordinary glue.
    glue = {'text', 'image', 'audio', 'generatedImage', 'store', 'load', 'notify',
            'setTimeout', 'clearTimeout', 'yield_control', 'exit', 'if', 'for', 'while',
            'switch', 'catch', 'with', 'function', 'await', 'String', 'Number', 'Boolean',
            'Array', 'Object', 'Map', 'Set', 'Date', 'RegExp', 'Error', 'Promise'}
    glue.update(tokens[i + 1] for i, word in enumerate(tokens[:-1]) if word in {'function', 'const', 'let', 'var'})
    for i, word in enumerate(tokens[:-1]):
        if (re.fullmatch(r'[A-Za-z_$][\w$]*', word) and tokens[i + 1] == '(' and
                word not in glue and (not i or tokens[i - 1] not in {'.', '?.'})):
            unknown = True
    commands: list[dict[str, Any]] = []
    patches: list[str] = []
    fields = {i: entries for i, token in enumerate(tokens) if token == 'tools'
              and (entries := command_fields(tokens, pairs, i)) is not None}
    collections = collection_commands(tokens, pairs, fields)
    for i, token in enumerate(tokens):
        if token != 'tools':
            continue
        # References/aliases, computed/optional access, rebinding and .call are
        # unresolved even if no ordinary direct call was found elsewhere.
        if (i and tokens[i - 1] in {'.', '?.'} or i + 3 >= len(tokens) or
                tokens[i + 1] != '.' or tokens[i + 3] != '(' or i + 3 not in pairs):
            unknown = True
            continue
        name = tokens[i + 2]
        end = pairs[i + 3]
        start = i + 4
        if name == 'apply_patch':
            patch = string_expression(tokens[start:end])
            if patch is None:
                unknown = True
            else:
                patches.append(patch)
            continue
        if name != 'exec_command' or start >= end or tokens[start] != '{' or pairs.get(start) != end - 1:
            unknown = True
            continue
        arguments: dict[str, Any] = {}
        entries = fields.get(i)
        if entries is None:
            unknown = True
        collection: list[str] | None = None
        for key, _, value_start, value_end in entries or []:
            if key in {'cmd', 'workdir', 'command', 'cwd'}:
                if key == 'cmd' and value_end == value_start + 1 and value_start in collections:
                    collection = collections[value_start]
                    value = collection[0]
                else:
                    value = string_expression(tokens[value_start:value_end])
                if key in arguments or value is None:
                    unknown = True
                arguments[key] = value
        if not isinstance(arguments.get('cmd'), str):
            unknown = True
        if collection:
            commands.extend({**arguments, 'cmd': value} for value in collection)
        else:
            commands.append(arguments)
    return commands, patches, unknown
