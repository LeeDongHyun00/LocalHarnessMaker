import copy
import json
import unittest
from unittest.mock import patch

from project import engine, render, render_many, run, run_many
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' Straße/West ', 'value': 1},
            {'id': 'b', 'target': 'STRASSE/WEST', 'value': -5},
            {'id': 'a', 'target': 'strasse/west', 'value': 5},
            {'id': 'A', 'target': 'strasse/west', 'value': 2},
            {'id': 'a', 'target': 'STRASSE/WEST', 'value': 5},
        ]
        expected = {'balances': {'strasse/west': 0}, 'history': [5, 0]}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'balances': {}, 'history': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_negative_prefix_and_ambiguity(self) -> None:
        negative = [
            {'id': 'a', 'target': 'x', 'value': -1},
            {'id': 'b', 'target': 'x', 'value': 2},
        ]
        ambiguous = [
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'A', 'target': 'y', 'value': 1},
            {'id': 'a', 'target': 'x', 'value': 3},
        ]
        for rows, message in ((negative, 'negative prefix'), (ambiguous, 'ambiguous id')):
            for api in (run, render, engine.compute):
                with self.subTest(api=api.__name__, message=message):
                    with self.assertRaisesRegex(ValueError, '^event-replay: ' + message + '$'):
                        api(rows)

    def test_structural_validation_has_priority(self) -> None:
        for rows in (
            [{'id': 'a', 'target': 'x', 'value': -1}],
            [{'id': 'a', 'target': 'x', 'value': 1},
             {'id': 'a', 'target': 'y', 'value': 1}],
        ):
            canonical = validate(rows)
            self.assertEqual(len(canonical), len(rows))
            rows.append({'id': 'broken'})
            for api in (run, render, engine.compute, validate):
                with self.assertRaisesRegex(ValueError, '^event-replay: invalid row$'):
                    api(rows)

    def test_validation_types_and_canonical_copies(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        rows = ListSubclass([DictSubclass(id=StringSubclass(' Ä/B  C '),
                                        target=StringSubclass(' Straße/東 '), value=10**100)])
        self.assertEqual(normalize(rows[0]['id']), 'ä/b  c')
        canonical = validate(rows)
        self.assertEqual(canonical, [{'id': 'ä/b  c', 'target': 'strasse/東', 'value': 10**100}])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(run(rows)['history'], [10**100])
        malformed = [None, [], {}, {'id': 'a', 'target': 'b', 'value': 1, 'extra': 0}]
        for field, values in (('id', ['', ' \t', None, 1]),
                              ('target', ['', '\n', None, 1]),
                              ('value', [True, IntSubclass(1), 1.0, '1', None])):
            for value in values:
                row = {'id': 'a', 'target': 'b', 'value': 1}
                row[field] = value
                malformed.append(row)
        for row in malformed:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^event-replay: invalid row$'):
                    validate([row])
        for value in (None, (), {}, 'rows'):
            for api in (run, render, engine.compute, validate):
                with self.assertRaisesRegex(TypeError, '^event-replay: rows must be a list$'):
                    api(value)

    def test_render_and_recursive_order(self) -> None:
        rows = [{'id': 'a', 'target': ' Z/東 ', 'value': 2},
                {'id': 'b', 'target': ' Ä ', 'value': 3},
                {'id': 'c', 'target': 'a', 'value': 0}]
        result = run(rows)
        self.assertEqual(list(result), ['balances', 'history'])
        self.assertEqual(list(result['balances']), ['a', 'z/東', 'ä'])
        self.assertEqual(result['history'], [2, 3, 0])
        self.assertEqual(render(rows), json.dumps(result, ensure_ascii=False, sort_keys=True,
                                                separators=(',', ':')) + '\n')
        self.assertEqual(render(rows), '{"balances":{"a":0,"z/東":2,"ä":3},"history":[2,3,0]}\n')
        self.assertEqual(run([]), {'balances': {}, 'history': []})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_independent_results_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 2}]
        batches = [rows, rows]
        original = copy.deepcopy(batches)
        results = run_many(batches)
        results[0]['balances']['x'] = 99
        results[0]['history'].append(99)
        self.assertEqual(results[1], {'balances': {'x': 2}, 'history': [2]})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(batches, original)
        for api in (run_many, render_many):
            failing = [rows, [{'id': 'b', 'target': 'x', 'value': -1}],
                       [{'id': 'bad', 'target': {'nested': []}, 'value': 1}]]
            original = copy.deepcopy(failing)
            with self.assertRaisesRegex(ValueError, '^event-replay: negative prefix$'):
                api(failing)
            self.assertEqual(failing, original)

    def test_batch_contract_and_runtime_compute(self) -> None:
        batches = [[{'id': 'a', 'target': 'x', 'value': 1}], []]
        for api in (run_many, render_many):
            for value in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^event-replay: batches must be a list$'):
                    api(value)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(batches)
                self.assertEqual(compute.call_args_list, [unittest.mock.call(rows) for rows in batches])
            failing = [batches[0], [{'id': 'a', 'target': 'x', 'value': -1}], None]
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^event-replay: negative prefix$'):
                    api(failing)
                self.assertEqual(compute.call_count, 2)
            with self.assertRaisesRegex(TypeError, '^event-replay: rows must be a list$'):
                api([None])
        for api in (run, render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(batches[0])
                compute.assert_called_once_with(batches[0])


if __name__ == '__main__':
    unittest.main()
