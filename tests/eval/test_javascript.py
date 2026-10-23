"""Literal code-mode string expressions use JavaScript replacement semantics."""

import pytest

from eval.runner.javascript import TOKEN, string_expression


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
    '"\\123"', '"\\u{110000}"', '"\\uQQQQ"',
])
def test_string_expression_near_misses_are_unresolved(source: str) -> None:
    assert string_expression(TOKEN.findall(source)) is None
