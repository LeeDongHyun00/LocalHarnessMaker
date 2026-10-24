import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': 'obsolete', 'value': 100},
            {'id': 'a', 'target': ' Queue ', 'value': 2},
            {'id': 'b', 'target': 'queue', 'value': 3},
            {'id': 'z', 'target': 'QUEUE', 'value': 2},
            {'id': 'negative', 'target': 'Alpha', 'value': -10},
        ]
        expected = {'queues': {'alpha': ['negative'], 'queue': ['b', 'z', 'a']}}
        before = copy.deepcopy(rows)
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['queues']), ['alpha', 'queue'])
        self.assertEqual(run_many([rows, []]), [expected, {'queues': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        self.assertEqual(rows, before)

    def test_normalization_and_validation(self) -> None:
        class Text(str):
            pass

        class Row(dict):
            pass

        class Rows(list):
            pass

        rows = Rows([Row(id=Text(' Straße / X '), target=Text(' Ä / Q '), value=10**200)])
        canonical = [{'id': 'strasse / x', 'target': 'ä / q', 'value': 10**200}]
        self.assertEqual(policy.normalize(Text(' Straße / X ')), 'strasse / x')
        self.assertEqual(validation.validate(rows), canonical)
        self.assertIsNot(validation.validate(rows)[0], rows[0])
        expected = {'queues': {'ä / q': ['strasse / x']}}
        for api in (run, engine.compute):
            self.assertEqual(api(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows]), serialized)

    def test_invalid_rows_and_precedence(self) -> None:
        class Integer(int):
            pass

        invalid = [None, [], {}, {'id': 'x', 'target': 'q', 'value': 1, 'extra': 0}]
        for field, values in [('id', ['', '  ', 1]), ('target', ['', '\t', None]),
                              ('value', [True, Integer(1), 1.0, '1'])]:
            for value in values:
                row = {'id': 'x', 'target': 'q', 'value': 1}
                row[field] = value
                invalid.append(row)
        for bad in invalid:
            rows = [{'id': 'x', 'target': 'q', 'value': 1},
                    {'id': 'X', 'target': 'other', 'value': -1}, bad]
            before = copy.deepcopy(rows)
            for api in (validation.validate, engine.compute, run, render):
                with self.subTest(api=api.__name__, bad=bad):
                    with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                    api([[], rows])
                self.assertEqual(rows, before)

    def test_validate_keeps_all_revisions(self) -> None:
        rows = [{'id': ' X ', 'target': ' A ', 'value': 2},
                {'id': 'x', 'target': ' B ', 'value': -2}]
        result = validation.validate(rows)
        self.assertEqual(result, [{'id': 'x', 'target': 'a', 'value': 2},
                                  {'id': 'x', 'target': 'b', 'value': -2}])
        result[0]['id'] = 'changed'
        self.assertEqual(rows[0]['id'], ' X ')

    def test_list_contracts_and_empty_inputs(self) -> None:
        for bad in (None, (), {}, 'rows', iter([])):
            for api in (validation.validate, engine.compute, run, render):
                with self.assertRaisesRegex(TypeError, '^job-queues: rows must be a list$'):
                    api(bad)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^job-queues: batches must be a list$'):
                    api(bad)
        self.assertEqual(run([]), {'queues': {}})
        self.assertEqual(render([]), '{"queues":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_output_independence(self) -> None:
        rows = [{'id': 'x', 'target': 'q', 'value': 0}]
        outputs = run_many([rows, rows])
        outputs[0]['queues']['q'].append('changed')
        outputs[0]['queues']['new'] = []
        expected = {'queues': {'q': ['x']}}
        self.assertEqual(outputs[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, [{'id': 'x', 'target': 'q', 'value': 0}])

    def test_shared_compute_and_first_failure(self) -> None:
        rows = [{'id': 'x', 'target': 'q', 'value': 1}]
        original = engine.compute
        for api, argument, count in [(run, rows, 1), (render, rows, 1),
                                      (run_many, [rows, rows], 2),
                                      (render_many, [rows, rows], 2)]:
            with patch.object(engine, 'compute', wraps=original) as observed:
                api(argument)
                self.assertEqual(observed.call_count, count)
        for api in (run_many, render_many):
            batches = [rows, None, [{}]]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=original) as observed:
                with self.assertRaisesRegex(TypeError, '^job-queues: rows must be a list$'):
                    api(batches)
                self.assertEqual(observed.call_count, 2)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
