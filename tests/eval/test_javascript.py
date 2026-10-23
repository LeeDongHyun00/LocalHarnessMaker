"""Literal code-mode string expressions use JavaScript replacement semantics."""

from pathlib import Path

import pytest

from eval.runner.javascript import TOKEN, string_expression, tool_calls


@pytest.mark.parametrize(('source', 'expected'), [
    ('"aXaX".replace("X", "")', 'aaX'),
    ('"aXaX".replaceAll("X", "")', 'aa'),
    ('"ab".replace("", "-")', '-ab'),
    ('"ab".replaceAll("", "-")', '-a-b-'),
    ('"a" + "b".replace("b", "c") + "d"', 'acd'),
    ('("a" + "b").replace("ab", "ok").replaceAll("o", "O")', 'Ok'),
    ('"abc".replace("b", "$$-$&-$`-$\'")', 'a$-b-a-cc'),
    ('"axa".replaceAll("a", "$`:$\'")', ':xaxax:'),
    ('"a".replace("a", "$1")', '$1'),
    ('"\\u{1f600}".replace("\\ud83d\\ude00", "ok")', 'ok'),
    ('"\\x61\\u0062" + "\\q"', 'abq'),
    ('`python -c \'print("synthetic")\'\npython -m unittest discover -v`',
     'python -c \'print("synthetic")\'\npython -m unittest discover -v'),
    ('`a\r\nb\rc`', 'a\nb\nc'),
    ('`a\\`b\\n\\u0063`', 'a`b\nc'),
])
def test_string_expression_semantics(source: str, expected: str) -> None:
    assert string_expression(TOKEN.findall(source)) == expected


@pytest.mark.parametrize('source', [
    'value', '`a${value}`', 'String("a")', '"a".replace(/a/, "b")',
    '"a".replace("a", value)', '"a".replace(value, "b")',
    '"a".replace("a", () => "b")', '"a".replace("a", "b", "c")',
    '"a".replaceAll("a", "b" + "c")', '"a".trim()', '"a" + value',
    '"a"["replace"]("a", "b")', '"a".replace?.("a", "b")',
    '"a".replaceAll(/a/g, "b")', '"a".toString()',
    '"\\123"', '"\\u{110000}"', '"\\uQQQQ"', '`a${}`', '`a\\${value}`',
])
def test_string_expression_near_misses_are_unresolved(source: str) -> None:
    assert string_expression(TOKEN.findall(source)) is None


COMMAND_VALUES = ['python -m py_compile solution.py', 'python -c \'print("synthetic")\'',
                  'python -m unittest discover -v']
COMMAND_ARRAY = '''["python -m py_compile solution.py", `python -c 'print("synthetic")'`,
                    "python -m unittest discover -v"]'''
COLLECTION_USES = [
    'const results = await Promise.all(commands.map(cmd => tools.exec_command({cmd})));',
    'const results = await Promise.all(commands.map(cmd => tools.exec_command({cmd:cmd})));',
    'await Promise.all(commands.map((cmd) => tools.exec_command({cmd,workdir:"."})));',
    'await Promise.all(commands.map(cmd => { return tools.exec_command({cmd}); }));',
    'for (const cmd of commands) { text(await tools.exec_command({cmd})); }',
    'for (let cmd of commands) text(await tools.exec_command({cmd}));',
    'await tools.exec_command({cmd:commands});',
    'await Promise.allSettled(commands.map(cmd => tools.exec_command({cmd, max_output_tokens:4000})));',
    'await Promise.all(commands.map(cmd => tools.exec_command({cmd, max_output_tokens:4000})));',
]


@pytest.mark.parametrize('binding', ['const', 'let'])
@pytest.mark.parametrize('use', COLLECTION_USES)
def test_literal_collection_resolves_each_command(binding: str, use: str) -> None:
    commands, patches, unknown = tool_calls(f'{binding} commands = {COMMAND_ARRAY}; {use}')
    assert not unknown
    assert patches == []
    assert [command['cmd'] for command in commands] == COMMAND_VALUES


@pytest.mark.parametrize('source', [
    'const commands = ["python --version", dynamic]; USE',
    'let commands = ARRAY; commands = ["other"]; USE',
    'const commands = ARRAY; USE commands.push("other");',
    'const commands = ARRAY; commands.splice(0, 1); USE',
    'const commands = ARRAY; commands[0] = "other"; USE',
    'const commands = ARRAY; const alias = commands; USE',
    'const commands = ARRAY; USE text(commands);',
    'const commands = ARRAY; USE USE',
    'const commands = ARRAY; { const commands = ARRAY; USE }',
    '{ const commands = ARRAY; } USE',
    'var commands = ARRAY; USE',
    'const commands = [`python ${version}`]; USE',
    'const commands = ["python" + " --version"]; USE',
    'const commands = ARRAY; commands.map(cmd => tools.exec_command({cmd:cmd + " --help"}));',
    'const commands = ARRAY; commands.map(cmd => { cmd = "other"; return tools.exec_command({cmd}); });',
    'const commands = ARRAY; commands.map(cmd => 0, tools.exec_command({cmd}));',
    'const commands = ARRAY; commands.map(cmd => tools.exec_command({cmd})); text(cmd);',
    'const commands = ARRAY; for (const cmd of commands) { text(cmd); tools.exec_command({cmd}); }',
    'const commands = ARRAY; for (const cmd of commands) {} tools.exec_command({cmd});',
    'const commands = ARRAY; tools.exec_command({cmd:commands[0]});',
    'const commands = ARRAY; tools.exec_command({cmd:commands.join(";")});',
    'const commands = ARRAY.map(x => x); USE',
    'const commands = ["python --version", ...other]; USE',
    r'const commands = ARRAY; \u0063ommands.push("other"); USE',
    'const commands = ARRAY; with (scope) { USE }',
])
def test_collection_near_misses_are_unresolved(source: str) -> None:
    source = source.replace('ARRAY', COMMAND_ARRAY).replace('USE', COLLECTION_USES[0])
    assert tool_calls(source)[2]


@pytest.mark.parametrize('promise', ['all', 'allSettled'])
def test_retained_array_with_readonly_display(promise: str) -> None:
    source = (Path(__file__).parent / 'fixtures/code-mode-command-array.js').read_text()
    commands, patches, unknown = tool_calls(source.replace('Promise.allSettled', 'Promise.' + promise))
    assert not unknown
    assert patches == []
    assert [command['cmd'] for command in commands] == [
        'python -m py_compile solution.py',
        'python -c \'from solution import solve; values = ["synthetic", "example"]; '
        'assert len(values) == 2; print("synthetic verification", values)\'',
        'python -m unittest discover -v',
    ]


@pytest.mark.parametrize('mutation', [
    'commands[i] = "other"', 'commands[i] += "other"', 'commands[i]++',
    '++commands[i]', 'delete commands[i]', 'delete (commands[i])',
    'commands.push("other")', 'commands.splice(0, 1)', 'commands.pop()',
    'commands.shift()', 'commands.unshift("other")', 'commands.sort()', 'commands.reverse()',
    'const alias = commands', 'commands = ["other"]',
])
@pytest.mark.parametrize('location', ['before', 'callback', 'after'])
def test_display_never_allows_array_mutation_or_escape(mutation: str, location: str) -> None:
    source = (Path(__file__).parent / 'fixtures/code-mode-command-array.js').read_text()
    if location == 'before':
        source = source.replace('const results', mutation + ';\nconst results')
    elif location == 'after':
        source += '\n' + mutation + ';'
    else:
        source = source.replace('=> text({command: commands[i], result})',
                                '=> { ' + mutation + '; text({command: commands[i], result}); }')
    assert tool_calls(source)[2]


@pytest.mark.parametrize(('original', 'replacement'), [
    ('commands[i]', '(commands[i] = "other")'),
    ('commands[i]', 'commands[i++]'),
    ('commands[i]', 'commands[opaque]'),
    ('commands[i]', 'commands[i].trim()'),
    ('commands[i]', 'commands'),
    ('commands[i]', 'commands[i], alias: commands'),
    ('text({command:', 'opaque({command:'),
])
def test_display_near_misses_are_unresolved(original: str, replacement: str) -> None:
    source = (Path(__file__).parent / 'fixtures/code-mode-command-array.js').read_text()
    assert tool_calls(source.replace(original, replacement))[2]


def test_display_before_collection_is_unresolved() -> None:
    source = (Path(__file__).parent / 'fixtures/code-mode-command-array.js').read_text()
    lines = source.splitlines(keepends=True)
    assert tool_calls(''.join(lines[:-2] + [lines[-1], lines[-2]]))[2]
