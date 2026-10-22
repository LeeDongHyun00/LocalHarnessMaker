"""Lexically extract direct tool calls without interpreting JavaScript glue."""

import ast
import re
from typing import Any


# Strings/comments are indivisible, so authored patch text cannot become a call.
TOKEN = re.compile(r'''//[^\n]*|/\*[\s\S]*?\*/|"(?:[^"\\]|\\[\s\S])*"|'(?:[^'\\]|\\[\s\S])*'|`(?:[^`\\]|\\[\s\S])*`|[A-Za-z_$][\w$]*|\.\.\.|\?\.|[^\s]''')


def literal(token: str) -> str | None:
    """Decode a quoted string only; expressions and interpolation stay unknown."""
    if not token.startswith(('"', "'")):
        return None
    try:
        value = ast.literal_eval(token)
        return value if isinstance(value, str) else None
    except (ValueError, SyntaxError):
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
            patch = literal(tokens[start]) if start < end else None
            if patch is None or start + 1 != end:
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
                value = literal(tokens[value_start]) if cursor == value_start + 1 else None
                if key in arguments or value is None:
                    unknown = True
                arguments[key] = value
            cursor += 1
        if not isinstance(arguments.get('cmd'), str):
            unknown = True
        commands.append(arguments)
    return commands, patches, unknown
