import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Child ', 'target': 'absent', 'value': -1},
            {'id': 'ROOT', 'target': 'root', 'value': 1},
            {'id': 'child', 'target': ' ROOT ', 'value': 2},
        ]
        expected = {'migrations': ['root', 'child']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'migrations': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_lower_revision_and_strict_version_order(self) -> None:
        rows = [
            {'id': 'root', 'target': 'root', 'value': 10},
            {'id': 'child', 'target': 'root', 'value': 2},
            {'id': 'root', 'target': 'root', 'value': 1},
        ]
        self.assertEqual(run(rows), {'migrations': ['root', 'child']})
        rows[-1]['value'] = 2
        for api in (run, render, engine.compute):
            with self.assertRaisesRegex(ValueError, '^schema-migration: version order$'):
                api(rows)

    def test_structural_validation_precedes_domain(self) -> None:
        rows = [
            {'id': 'a', 'target': 'missing', 'value': -1},
            {'id': ' A ', 'target': 'a', 'value': 0},
            {'id': 'bad', 'target': 'bad', 'value': True},
        ]
        for api in (run, render, engine.compute, validation.validate):
            with self.assertRaisesRegex(ValueError, '^schema-migration: invalid row$'):
                api(rows)
        self.assertEqual(validation.validate(rows[:-1]), [
            {'id': 'a', 'target': 'missing', 'value': -1},
            {'id': 'a', 'target': 'a', 'value': 0},
        ])

    def test_domain_error_priority(self) -> None:
        rows = [
            {'id': 'a', 'target': 'missing', 'value': 2},
            {'id': 'b', 'target': 'a', 'value': 0},
        ]
        for message, value in [('invalid version', 0), ('missing predecessor', 1)]:
            rows[1]['value'] = value
            with self.assertRaisesRegex(ValueError, '^schema-migration: ' + message + '$'):
                run(rows)

    def test_normalization_types_and_large_versions(self) -> None:
        class Text(str):
            pass

        class Row(dict):
            pass

        class Rows(list):
            pass

        class Integer(int):
            pass

        name = Text('  Straße / A  B  ')
        rows = Rows([Row(id=name, target=name, value=10 ** 100)])
        expected = {'migrations': ['strasse / a  b']}
        self.assertEqual(policy.normalize(name), 'strasse / a  b')
        for api in (run, engine.compute):
            self.assertEqual(api(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(json.loads(render(rows)), expected)
        self.assertEqual(render_many([rows]), render(rows))
        for value in (True, Integer(1), 1.0):
            with self.assertRaisesRegex(ValueError, '^schema-migration: invalid row$'):
                run([{'id': 'a', 'target': 'a', 'value': value}])

    def test_invalid_shapes(self) -> None:
        for api in (run, render, engine.compute, validation.validate):
            with self.assertRaisesRegex(TypeError, '^schema-migration: rows must be a list$'):
                api(())
        for row in ({}, {'id': ' ', 'target': 'a', 'value': 1},
                    {'id': 'a', 'target': None, 'value': 1},
                    {'id': 'a', 'target': 'a', 'value': 1, 'extra': {}}, []):
            with self.assertRaisesRegex(ValueError, '^schema-migration: invalid row$'):
                run([row])

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': 'a', 'value': 1}]
        original = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        outputs[0]['migrations'].append('changed')
        self.assertEqual(outputs[1], {'migrations': ['a']})
        self.assertEqual(run(rows), outputs[1])
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        malformed = rows + [{'id': 'b', 'target': 'b', 'value': {'nested': []}}]
        original = copy.deepcopy(malformed)
        for api in (run, render, run_many, render_many):
            with self.assertRaises(ValueError):
                api([malformed] if api in (run_many, render_many) else malformed)
            self.assertEqual(malformed, original)

    def test_batches_are_ordered_atomic_and_dynamic(self) -> None:
        good = [{'id': 'a', 'target': 'a', 'value': 1}]
        bad = [{'id': 'b', 'target': 'missing', 'value': 1}]
        later = [{'id': 'bad'}]
        batches = [good, bad, later]
        original = copy.deepcopy(batches)
        compute = engine.compute
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=compute) as observed:
                with self.assertRaisesRegex(ValueError, '^schema-migration: missing predecessor$'):
                    api(batches)
                self.assertEqual(observed.call_args_list, [unittest.mock.call(good), unittest.mock.call(bad)])
            self.assertEqual(batches, original)
            with patch.object(engine, 'compute', wraps=compute) as observed:
                api([good, good])
                self.assertEqual(observed.call_count, 2)
            with self.assertRaisesRegex(TypeError, '^schema-migration: batches must be a list$'):
                api(())
        for api in (run, render):
            with patch.object(engine, 'compute', wraps=compute) as observed:
                api(good)
                observed.assert_called_once_with(good)

    def test_serialization_and_empty_results(self) -> None:
        rows = [{'id': ' É ', 'target': 'é', 'value': 1}]
        self.assertEqual(render(rows), '{"migrations":["é"]}\n')
        nested = {'z': {'b': 1, 'a': 2}, 'a': ['é', {'z': 0, 'a': 1}]}
        with patch.object(engine, 'compute', return_value=nested):
            self.assertEqual(render([]), json.dumps(run([]), ensure_ascii=False, sort_keys=True,
                                                   separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'migrations': []})
        self.assertEqual(render([]), '{"migrations":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
