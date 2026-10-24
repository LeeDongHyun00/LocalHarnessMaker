import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' DOC_A ', 'target': 'Straße_X / Y', 'value': 0},
            {'id': 'doc-a', 'target': 'STRASSE-X / Y', 'value': 0},
            {'id': 'Doc_B', 'target': ' STRASSE_X / Y ', 'value': 7},
            {'id': 'doc-c', 'target': 'alpha', 'value': 10 ** 100},
        ]
        result = run(rows)
        self.assertEqual(result, {'index': {
            'alpha': {'count': 10 ** 100, 'documents': ['doc-c']},
            'strasse-x / y': {'count': 7, 'documents': ['doc-a', 'doc-b']},
        }})
        self.assertEqual(list(result), ['index'])
        self.assertEqual(list(result['index']), ['alpha', 'strasse-x / y'])
        self.assertEqual(list(result['index']['alpha']), ['count', 'documents'])

    def test_validation_is_fresh_and_does_not_select(self) -> None:
        rows = [{'id': ' A_B ', 'target': ' É / X_Y ', 'value': -1}] * 2
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'a-b', 'target': 'é / x-y', 'value': -1},
            {'id': 'a-b', 'target': 'é / x-y', 'value': -1},
        ])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], canonical[1])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' A_B / Straße '), 'a-b / strasse')

    def test_structural_errors_and_precedence(self) -> None:
        class IntSubclass(int):
            pass

        invalid_rows = [None, [], {}, {'id': 'a', 'target': 'b'},
                        {'id': 'a', 'target': 'b', 'value': 1, 'extra': 2}]
        invalid_rows += [{'id': ident, 'target': target, 'value': value}
                         for ident, target, value in [
                             (' ', 'b', 1), ('a', '\t', 1), (1, 'b', 1),
                             ('a', None, 1), ('a', 'b', True),
                             ('a', 'b', IntSubclass(1)), ('a', 'b', 1.0)]]
        for api in (run, render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows'):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^text-indexing: rows must be a list$'):
                        api(rows)
            for bad in invalid_rows:
                rows = [{'id': 'a', 'target': 'b', 'value': -1},
                        {'id': 'a', 'target': 'c', 'value': 1}, bad]
                before = copy.deepcopy(rows)
                with self.subTest(api=api.__name__, bad=bad):
                    with self.assertRaisesRegex(ValueError, '^text-indexing: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_duplicate_precedes_negative(self) -> None:
        for api in (run, render, engine.compute):
            with self.assertRaisesRegex(ValueError, '^text-indexing: duplicate id$'):
                api([{'id': 'A_B', 'target': 'b', 'value': -1},
                     {'id': ' a-b ', 'target': 'b', 'value': 1}])
            with self.assertRaisesRegex(ValueError, '^text-indexing: negative count$'):
                api([{'id': 'a', 'target': 'b', 'value': -10 ** 100}])

    def test_subclasses_and_empty(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' A_B '), target=Text(' Z '), value=0)])
        self.assertEqual(run(rows), {'index': {'z': {'count': 0, 'documents': ['a-b']}}})
        self.assertEqual(run([]), {'index': {}})
        self.assertEqual(render([]), '{"index":{}}\n')

    def test_render_and_runtime_compute(self) -> None:
        rows = [{'id': 'É_B', 'target': ' Z_É ', 'value': 2},
                {'id': 'x', 'target': 'a', 'value': 1}]
        expected = run(rows)
        with patch.object(engine, 'compute', wraps=engine.compute) as compute:
            self.assertEqual(run(rows), expected)
            compute.assert_called_once_with(rows)
        with patch.object(engine, 'compute', wraps=engine.compute) as compute:
            actual = render(rows)
            compute.assert_called_once_with(rows)
        self.assertEqual(actual, json.dumps(expected, ensure_ascii=False,
                                           sort_keys=True, separators=(',', ':')) + '\n')
        self.assertIn('é', actual)
        self.assertEqual(actual.count('\n'), 1)

    def test_output_isolation_and_input_preservation(self) -> None:
        rows = [{'id': 'A', 'target': 'B', 'value': 1}]
        before = copy.deepcopy(rows)
        first, second = run(rows), run(rows)
        first['index']['b']['documents'].append('other')
        first['index']['b']['count'] = 99
        self.assertEqual(second, {'index': {'b': {'count': 1, 'documents': ['a']}}})
        self.assertEqual(run(rows), second)
        self.assertEqual(rows, before)
        failing = rows + [{'id': ' a ', 'target': 'b', 'value': 2}]
        before = copy.deepcopy(failing)
        with self.assertRaises(ValueError):
            run(failing)
        self.assertEqual(failing, before)

    def test_batch_signatures_outer_types_and_empty(self) -> None:
        import inspect

        class Batches(list):
            pass

        for api in (run_many, render_many):
            self.assertEqual(list(inspect.signature(api).parameters), ['batches'])
            for batches in (None, (), {}, 'batches', iter([]), 0):
                with self.subTest(api=api.__name__, batches=batches):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^text-indexing: batches must be a list$'):
                            api(batches)
                        compute.assert_not_called()
            for batches in ([], Batches()):
                with patch.object(engine, 'compute') as compute:
                    self.assertEqual(api(batches), [] if api is run_many else '')
                    compute.assert_not_called()
        self.assertEqual(run_many(Batches([[]])), [{'index': {}}])
        self.assertEqual(render_many(Batches([[]])), '{"index":{}}\n')

    def test_batch_policies_rendering_and_compute_order(self) -> None:
        batches = [[
            {'id': ' DOC_A ', 'target': 'Straße_X / Y', 'value': 0},
            {'id': 'doc-a', 'target': 'STRASSE-X / Y', 'value': 0},
            {'id': 'Doc_B', 'target': ' STRASSE_X / Y ', 'value': 7},
            {'id': 'doc-c', 'target': 'alpha', 'value': 10 ** 100},
        ], [], [{'id': 'doc-a', 'target': ' É ', 'value': 2}]]
        before = copy.deepcopy(batches)
        expected = [{'index': {
            'alpha': {'count': 10 ** 100, 'documents': ['doc-c']},
            'strasse-x / y': {'count': 7, 'documents': ['doc-a', 'doc-b']},
        }}, {'index': {}}, {'index': {'é': {'count': 2, 'documents': ['doc-a']}}}]
        for api in (run_many, render_many):
            seen = []
            original_compute = engine.compute

            def compute(rows):
                self.assertIs(rows, batches[len(seen)])
                seen.append(rows)
                return original_compute(rows)

            with patch.object(engine, 'compute', side_effect=compute) as mocked:
                actual = api(batches)
                self.assertEqual(mocked.call_count, len(batches))
            if api is run_many:
                self.assertEqual(actual, expected)
                self.assertEqual(list(actual[0]['index']), ['alpha', 'strasse-x / y'])
            else:
                self.assertEqual(actual, ''.join(json.dumps(result, ensure_ascii=False,
                    sort_keys=True, separators=(',', ':')) + '\n' for result in expected))
                self.assertEqual(actual.count('\n'), len(batches))
            self.assertEqual(batches, before)

    def test_batch_errors_precedence_and_atomic_failure(self) -> None:
        valid = [{'id': 'a', 'target': 'b', 'value': 1}]
        negative = [{'id': 'a', 'target': 'b', 'value': -1}]
        conflict = negative + [{'id': ' A ', 'target': 'b', 'value': 1}]
        cases = [(None, TypeError, 'rows must be a list'),
                 (conflict + [{}], ValueError, 'invalid row'),
                 (conflict, ValueError, 'duplicate id'),
                 (negative, ValueError, 'negative count')]
        for api in (run_many, render_many):
            for bad, error, message in cases:
                for position in range(3):
                    batches = [copy.deepcopy(valid) for _ in range(3)]
                    batches[position] = copy.deepcopy(bad)
                    before = copy.deepcopy(batches)
                    seen = []
                    original_compute = engine.compute

                    def compute(rows):
                        self.assertIs(rows, batches[len(seen)])
                        seen.append(rows)
                        return original_compute(rows)

                    with self.subTest(api=api.__name__, message=message, position=position):
                        with patch.object(engine, 'compute', side_effect=compute) as mocked:
                            with self.assertRaisesRegex(error, '^text-indexing: ' + message + '$'):
                                api(batches)
                            self.assertEqual(mocked.call_count, position + 1)
                        self.assertEqual(batches, before)
            # A later structural failure cannot overtake an earlier domain failure.
            with self.assertRaisesRegex(ValueError, '^text-indexing: negative count$'):
                api([negative, [{}]])

    def test_batch_nested_result_isolation(self) -> None:
        rows = [{'id': 'A', 'target': 'B', 'value': 1}]
        batches = [rows, rows]
        before = copy.deepcopy(batches)
        first = run_many(batches)
        second = run_many(batches)
        first[0]['index']['b']['documents'].append('other')
        first[0]['index']['b']['count'] = 99
        expected = {'index': {'b': {'count': 1, 'documents': ['a']}}}
        self.assertEqual(first[1], expected)
        self.assertEqual(second, [expected, expected])
        first[0]['index']['new'] = {}
        self.assertNotIn('new', first[1]['index'])
        self.assertEqual(batches, before)
        self.assertIs(batches[0], batches[1])


if __name__ == '__main__':
    unittest.main()
