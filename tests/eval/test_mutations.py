"""Synthetic operator coverage without real reference or grader material."""

import ast

from eval.runner.mutations import mutations


def test_all_mutation_operators_are_deterministic_and_single_site() -> None:
    source = ('def example(values, x):\n'
              ' if not (x > 2 and x < 9):\n'
              '  return values[1:3:2]\n'
              ' return x + 1\n')
    first = list(mutations(source))
    assert first == list(mutations(source))
    assert {item.kind for item in first} == {'comparison', 'arithmetic', 'boolean', 'integer', 'return', 'slice', 'not'}
    assert len({item.sha256 for item in first}) == len(first)
    for item in first:
        compile(ast.parse(item.source), '<synthetic>', 'exec')
        assert item.before != item.after
