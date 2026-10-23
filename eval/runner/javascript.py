"""Lexically extract direct tool calls without interpreting JavaScript glue."""

import re
from typing import Any


# Strings/comments are indivisible, so authored patch text cannot become a call.
TOKEN = re.compile(r'''//[^\n]*|/\*[\s\S]*?\*/|"(?:[^"\\]|\\[\s\S])*"|'(?:[^'\\]|\\[\s\S])*'|`(?:[^`\\]|\\[\s\S])*`|[A-Za-z_$][\w$]*|\.\.\.|\?\.|[^\s]''')


def literal(token: str) -> str | None:
    """Decode modern JavaScript quoted strings, never evaluate source code."""
    if len(token) < 2 or token[0] not in {'"', "'"} or token[-1] != token[0]:
        return None
    result: list[str] = []
    cursor = 1
    escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v",
               "\\": "\\", '"': '"', "'": "'"}
    while cursor < len(token) - 1:
        char = token[cursor]
        cursor += 1
        if char in {"\n", "\r", token[0]}:
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
        cursor = start + 1
        while cursor < end - 1:
            key = literal(tokens[cursor]) or tokens[cursor]
            if cursor + 1 >= end - 1 or tokens[cursor + 1] != ':' or not re.fullmatch(r'[A-Za-z_]\w*', key):
                unknown = True
                break
            value_start = cursor + 2
            cursor = value_start
            while cursor < end - 1 and tokens[cursor] != ',':
                cursor = pairs[cursor] + 1 if cursor in pairs else cursor + 1
            if key in {'cmd', 'workdir', 'command', 'cwd'}:
                value = string_expression(tokens[value_start:cursor])
                if key in arguments or value is None:
                    unknown = True
                arguments[key] = value
            cursor += 1
        if not isinstance(arguments.get('cmd'), str):
            unknown = True
        commands.append(arguments)
    return commands, patches, unknown
