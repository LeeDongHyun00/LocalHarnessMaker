import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' First_ID ', 'target': ' DOC_A ', 'value': 2},
            {'id': 'last', 'target': 'doc-a', 'value': 20},
            {'id': 'first-id', 'target': 'doc-a', 'value': 2},
            {'id': 'other', 'target': ' A ', 'value': 0},
        ]
        result = project.run(rows)
        self.assertEqual(result, {
            'patches': {'a': ['other'], 'doc-a': ['last', 'first-id']},
            'offsets': {'a': [0], 'doc-a': [20, 2]},
        })
        self.assertEqual(list(result), ['patches', 'offsets'])
        for collection in result.values():
            self.assertEqual(list(collection), ['a', 'doc-a'])

    def test_normalization_and_validation(self) -> None:
        class Text(str):
            pass

        class Row(dict):
            pass

        class Rows(list):
            pass

        rows = Rows([Row(id=Text(' Straße_X / A '), target=Text(' Ü_D / B '), value=10**100)])
        canonical = [{'id': 'strasse-x / a', 'target': 'ü-d / b', 'value': 10**100}]
        self.assertEqual(policy.normalize(rows[0]['id']), canonical[0]['id'])
        self.assertEqual(validation.validate(rows), canonical)
        expected = {'patches': {'ü-d / b': ['strasse-x / a']}, 'offsets': {'ü-d / b': [10**100]}}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(json.loads(project.render(rows)), expected)

    def test_structural_errors_across_entry_points(self) -> None:
        class Integer(int):
            pass

        bad_rows = [None, {}, {'id': 'a', 'target': 'd', 'value': 1, 'extra': 0}]
        for field, values in [('id', ['', '  ', 1]), ('target', ['', '\t', None]),
                              ('value', [True, Integer(1), 1.0, '1'])]:
            for value in values:
                bad_rows.append(dict({'id': 'a', 'target': 'd', 'value': 1}, **{field: value}))
        for entry in (project.run, project.render, engine.compute, validation.validate):
            for invalid in (None, (), {}, iter([])):
                with self.subTest(entry=entry.__name__, invalid=repr(invalid)):
                    with self.assertRaisesRegex(TypeError, '^document-patches: rows must be a list$'):
                        entry(invalid)
            for row in bad_rows:
                with self.subTest(entry=entry.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^document-patches: invalid row$'):
                        entry([row])

    def test_structural_validation_precedes_selection_and_domain(self) -> None:
        prefixes = [
            [{'id': 'a', 'target': 'd', 'value': -1}],
            [{'id': 'a', 'target': 'd', 'value': 1}, {'id': 'a', 'target': 'd', 'value': 2}],
            [{'id': 'a', 'target': 'd', 'value': 1}, {'id': 'b', 'target': 'd', 'value': 1}],
        ]
        for rows in prefixes:
            for entry in (project.run, project.render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^document-patches: invalid row$'):
                    entry(rows + [{'id': 'bad'}])
            canonical = validation.validate(rows)
            self.assertEqual(canonical, rows)
            self.assertIsNot(canonical, rows)
            for original, fresh in zip(rows, canonical):
                self.assertIsNot(original, fresh)

    def test_domain_error_order(self) -> None:
        cases = [
            ([{'id': ' A ', 'target': 'd', 'value': -1},
              {'id': 'a', 'target': 'd', 'value': 2}], 'duplicate id'),
            ([{'id': 'a', 'target': 'd', 'value': 1},
              {'id': 'b', 'target': 'd', 'value': 1},
              {'id': 'c', 'target': 'd', 'value': -1}], 'negative offset'),
            ([{'id': 'a', 'target': ' D_A ', 'value': 0},
              {'id': 'b', 'target': 'd-a', 'value': 0}], 'collision'),
        ]
        for rows, message in cases:
            before = copy.deepcopy(rows)
            for entry in (project.run, project.render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^document-patches: ' + message + '$'):
                    entry(rows)
                self.assertEqual(rows, before)

    def test_fresh_outputs_and_no_mutation(self) -> None:
        rows = [{'id': ' A ', 'target': ' D ', 'value': 3}]
        before = copy.deepcopy(rows)
        first = project.run(rows)
        second = project.run(rows)
        first['patches']['d'].append('changed')
        first['offsets']['d'].clear()
        self.assertEqual(second, project.run(rows))
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        invalid = rows + [{'id': 'bad', 'target': 'd', 'value': {'nested': []}}]
        before_invalid = copy.deepcopy(invalid)
        with self.assertRaises(ValueError):
            project.run(invalid)
        self.assertEqual(invalid, before_invalid)

    def test_render_and_empty(self) -> None:
        self.assertEqual(project.run([]), {'patches': {}, 'offsets': {}})
        rows = [{'id': 'É_\nX', 'target': 'Z', 'value': 1},
                {'id': 'a', 'target': 'A', 'value': 2}]
        self.assertEqual(project.render(rows), json.dumps(project.run(rows), ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(project.render([]), '{"offsets":{},"patches":{}}\n')

    def test_runtime_compute_instrumentation(self) -> None:
        for entry in (project.run, project.render):
            rows = [{'id': 'a', 'target': 'd', 'value': 1}]
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                entry(rows)
                compute.assert_called_once_with(rows)
            with patch.object(engine, 'compute', side_effect=ValueError('instrumented')) as compute:
                with self.assertRaisesRegex(ValueError, '^instrumented$'):
                    entry(rows)
                compute.assert_called_once_with(rows)

    def test_batch_results_and_empty(self) -> None:
        class Batches(list):
            pass

        batches = Batches([
            [{'id': ' Straße_X / A ', 'target': ' Ü_D / B ', 'value': 2},
             {'id': 'last', 'target': 'ü-d / b', 'value': 10**100},
             {'id': 'strasse-x / a', 'target': 'ü-d / b', 'value': 2},
             {'id': 'É_\nX', 'target': ' A ', 'value': 0}],
            [],
            [{'id': 'last', 'target': 'ü-d / b', 'value': 10**100}],
        ])
        before = copy.deepcopy(batches)
        expected = [
            {'patches': {'a': ['é-\nx'], 'ü-d / b': ['last', 'strasse-x / a']},
             'offsets': {'a': [0], 'ü-d / b': [10**100, 2]}},
            {'patches': {}, 'offsets': {}},
            {'patches': {'ü-d / b': ['last']}, 'offsets': {'ü-d / b': [10**100]}},
        ]
        result = project.run_many(batches)
        self.assertEqual(result, expected)
        for member in result:
            for collection in member.values():
                self.assertEqual(list(collection), sorted(collection))
        self.assertEqual(project.render_many(batches), ''.join(
            json.dumps(member, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
            for member in expected))
        self.assertEqual(batches, before)
        for entry, empty in ((project.run_many, []), (project.render_many, '')):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                self.assertEqual(entry(Batches()), empty)
                compute.assert_not_called()

    def test_batch_outer_validation(self) -> None:
        for entry in (project.run_many, project.render_many):
            for invalid in (None, (), {}, '', iter([])):
                with self.subTest(entry=entry.__name__, invalid=repr(invalid)):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^document-patches: batches must be a list$'):
                            entry(invalid)
                        compute.assert_not_called()

    def test_batch_policy_errors_and_first_failure(self) -> None:
        a = {'id': ' A ', 'target': ' D_A ', 'value': 1}
        cases = [
            (None, TypeError, 'rows must be a list'),
            ((a,), TypeError, 'rows must be a list'),
            ([dict(a, value=True)], ValueError, 'invalid row'),
            ([dict(a, value=-1), {'id': 'bad'}], ValueError, 'invalid row'),
            ([a, dict(a, value=2), {'id': 'bad'}], ValueError, 'invalid row'),
            ([a, dict(a, id='b'), {'id': 'bad'}], ValueError, 'invalid row'),
            ([dict(a, value=-1), dict(a, id='a', value=2)], ValueError, 'duplicate id'),
            ([a, dict(a, id='b'), dict(a, id='c', value=-1)], ValueError, 'negative offset'),
            ([a, dict(a, id='b', target='d-a')], ValueError, 'collision'),
        ]
        for entry in (project.run_many, project.render_many):
            for invalid, error, message in cases:
                batches = [[a], invalid, [{'id': 'unreached'}]]
                before = copy.deepcopy(batches)
                with self.subTest(entry=entry.__name__, message=message):
                    with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                        with self.assertRaisesRegex(error, '^document-patches: ' + message + '$'):
                            entry(batches)
                        self.assertEqual(compute.call_count, 2)
                        self.assertIs(compute.call_args_list[0].args[0], batches[0])
                        self.assertIs(compute.call_args_list[1].args[0], batches[1])
                    self.assertEqual(batches, before)

    def test_batch_runtime_compute_instrumentation(self) -> None:
        batches = [[{'id': 'a', 'target': 'd', 'value': 1}], []]
        for entry in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                entry(batches)
                self.assertEqual(compute.call_count, len(batches))
                for call, rows in zip(compute.call_args_list, batches):
                    self.assertIs(call.args[0], rows)
            failure = ValueError('instrumented')
            with patch.object(engine, 'compute', side_effect=failure) as compute:
                with self.assertRaises(ValueError) as caught:
                    entry(batches)
                self.assertIs(caught.exception, failure)
                compute.assert_called_once_with(batches[0])

    def test_batch_nested_independence(self) -> None:
        rows = [{'id': ' A ', 'target': ' D ', 'value': 3}]
        batches = [rows, rows]
        before = copy.deepcopy(batches)
        first = project.run_many(batches)
        second = project.run_many(batches)
        self.assertIsNot(first[0], first[1])
        for key in ('patches', 'offsets'):
            self.assertIsNot(first[0][key], first[1][key])
            self.assertIsNot(first[0][key]['d'], first[1][key]['d'])
        first[0]['patches']['d'].append('changed')
        first[0]['offsets']['d'].clear()
        first[0]['patches']['extra'] = []
        self.assertEqual(first[1], second[0])
        self.assertEqual(second, project.run_many(batches))
        empty = project.run_many([[], []])
        empty[0]['patches']['new'] = []
        self.assertEqual(empty[1], {'patches': {}, 'offsets': {}})
        for entry in (project.run_many, project.render_many):
            entry(batches)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
