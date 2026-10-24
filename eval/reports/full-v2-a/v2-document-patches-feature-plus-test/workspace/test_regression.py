import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' Old ', 'value': 1},
            {'id': 'b', 'target': ' Doc/Σ ', 'value': 4},
            {'id': 'a', 'target': ' DOC/Σ ', 'value': 8},
            {'id': 'A', 'target': 'ignored', 'value': 2},
            {'id': 'a', 'target': 'doc/σ', 'value': 8},
            {'id': 'c', 'target': ' A  B ', 'value': 10**100},
        ]
        expected = {
            'patches': {'a  b': ['c'], 'doc/σ': ['a', 'b']},
            'offsets': {'a  b': [10**100], 'doc/σ': [8, 4]},
        }
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, self.empty()])
        self.assertEqual(project.render_many([rows, []]),
                         project.render(rows) + project.render([]))
        self.assertEqual(list(project.run(rows)), ['patches', 'offsets'])
        for mapping in project.run(rows).values():
            self.assertEqual(list(mapping), ['a  b', 'doc/σ'])

    @staticmethod
    def empty() -> dict:
        return {'patches': {}, 'offsets': {}}

    def assert_all_errors(self, rows: object, kind: type[Exception], message: str) -> None:
        before = copy.deepcopy(rows)
        calls = (
            lambda: project.run(rows),
            lambda: project.render(rows),
            lambda: engine.compute(rows),
            lambda: project.run_many([rows]),
            lambda: project.render_many([rows]),
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises(kind) as caught:
                    call()
                self.assertEqual(str(caught.exception), message)
                self.assertEqual(rows, before)

    def test_structure_and_precedence(self) -> None:
        class IntSubclass(int):
            pass

        for rows in (None, (), {}, 'rows'):
            self.assert_all_errors(rows, TypeError, 'document-patches: rows must be a list')
        invalid_rows = [
            None, [], {},
            {'id': 'a', 'target': 'd', 'value': 0, 'extra': 1},
            {'id': ' ', 'target': 'd', 'value': 0},
            {'id': 'a', 'target': '\t', 'value': 0},
            {'id': 1, 'target': 'd', 'value': 0},
            {'id': 'a', 'target': None, 'value': 0},
            {'id': 'a', 'target': 'd', 'value': True},
            {'id': 'a', 'target': 'd', 'value': IntSubclass(1)},
            {'id': 'a', 'target': 'd', 'value': 1.0},
        ]
        prefixes = [
            [],
            [{'id': 'a', 'target': 'd', 'value': -1}],
            [{'id': 'a', 'target': 'd', 'value': 1},
             {'id': 'a', 'target': 'e', 'value': 1}],
            [{'id': 'a', 'target': 'd', 'value': 1},
             {'id': 'b', 'target': 'd', 'value': 1}],
        ]
        for prefix in prefixes:
            for invalid in invalid_rows:
                self.assert_all_errors(prefix + [invalid], ValueError,
                                       'document-patches: invalid row')

    def test_validation_is_canonical_without_selection(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StrSubclass(str):
            pass

        rows = ListSubclass([
            DictSubclass(id=StrSubclass(' Straße/ A  B '),
                         target=StrSubclass(' DOC/Σ '), value=-3),
            {'id': 'STRASSE/ A  B', 'target': 'other', 'value': -3},
        ])
        before = copy.deepcopy(rows)
        expected = [
            {'id': 'strasse/ a  b', 'target': 'doc/σ', 'value': -3},
            {'id': 'strasse/ a  b', 'target': 'other', 'value': -3},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, expected)
        self.assertEqual(policy.normalize(rows[0]['id']), expected[0]['id'])
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        self.assertEqual(validation.validate(rows), expected)
        accepted = ListSubclass([DictSubclass(id=StrSubclass(' A '), target=' D ', value=0)])
        self.assertEqual(project.run(accepted),
                         {'patches': {'d': ['a']}, 'offsets': {'d': [0]}})

    def test_domain_failures(self) -> None:
        ambiguous = [
            {'id': ' A ', 'target': 'd', 'value': 2},
            {'id': 'a', 'target': 'e', 'value': 2},
            {'id': 'a', 'target': 'f', 'value': 3},
        ]
        self.assert_all_errors(ambiguous, ValueError, 'document-patches: ambiguous id')
        collision = [
            {'id': 'a', 'target': ' D ', 'value': 2},
            {'id': 'b', 'target': 'd', 'value': 2},
        ]
        self.assert_all_errors(collision, ValueError, 'document-patches: collision')
        self.assert_all_errors(collision + [{'id': 'c', 'target': 'e', 'value': -1}],
                               ValueError, 'document-patches: negative offset')

    def test_serialization_and_empty(self) -> None:
        rows = [{'id': ' Straße ', 'target': ' Σ ', 'value': 0}]
        self.assertEqual(project.render(rows),
                         '{"offsets":{"σ":[0]},"patches":{"σ":["strasse"]}}\n')
        self.assertEqual(project.render(rows), json.dumps(project.run(rows),
                         ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(project.run([]), self.empty())
        self.assertEqual(project.render([]), '{"offsets":{},"patches":{}}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        for api in (project.run_many, project.render_many):
            for outer in (None, (), {}, ''):
                with self.assertRaises(TypeError) as caught:
                    api(outer)
                self.assertEqual(str(caught.exception), 'document-patches: batches must be a list')

    def test_batch_atomicity_and_runtime_engine_lookup(self) -> None:
        good = [{'id': 'a', 'target': 'd', 'value': 1}]
        bad = [{'id': 'a', 'target': 'd', 'value': -1}]
        later = [{'invalid': {'nested': []}}]
        for api in (project.run_many, project.render_many):
            batches = [good, bad, later]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaises(ValueError) as caught:
                    api(batches)
                self.assertEqual(str(caught.exception), 'document-patches: negative offset')
                self.assertEqual(compute.call_args_list, [unittest.mock.call(good), unittest.mock.call(bad)])
            self.assertEqual(batches, before)
        for api, argument, count in (
            (project.run, good, 1), (project.render, good, 1),
            (project.run_many, [good, good], 2),
            (project.render_many, [good, good], 2),
        ):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)

    def test_output_independence(self) -> None:
        rows = [{'id': 'a', 'target': 'd', 'value': 1}]
        before = copy.deepcopy(rows)
        results = project.run_many([rows, rows])
        expected = {'patches': {'d': ['a']}, 'offsets': {'d': [1]}}
        for key in ('patches', 'offsets'):
            self.assertIsNot(results[0][key], results[1][key])
            self.assertIsNot(results[0][key]['d'], results[1][key]['d'])
        results[0]['patches']['d'].append('changed')
        results[0]['offsets']['d'][0] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(rows, before)
        empty = project.run_many([[], []])
        empty[0]['patches']['new'] = []
        self.assertEqual(empty[1], self.empty())


if __name__ == '__main__':
    unittest.main()
