import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Child ', 'target': 'missing', 'value': 100},
            {'id': 'z', 'target': 'z', 'value': 0},
            {'id': 'a', 'target': 'child', 'value': -1},
            {'id': 'CHILD', 'target': ' Z ', 'value': -100},
        ]
        expected = {'order': ['z', 'child', 'a']}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, {'order': []}])
        self.assertEqual(project.render_many([rows, []]),
                         project.render(rows) + '{"order":[]}\n')

    def test_waves_and_cycles(self) -> None:
        rows = [
            {'id': 'a', 'target': 'z', 'value': 999},
            {'id': 'z', 'target': 'z', 'value': -999},
            {'id': 'b', 'target': 'b', 'value': 0},
            {'id': 'c', 'target': 'b', 'value': 0},
        ]
        self.assertEqual(project.run(rows), {'order': ['b', 'z', 'a', 'c']})
        for rows, message in [
            ([{'id': 'a', 'target': 'b', 'value': 0}], 'missing dependency'),
            ([{'id': 'a', 'target': 'b', 'value': 0},
              {'id': 'b', 'target': 'a', 'value': 0}], 'cycle'),
        ]:
            with self.assertRaisesRegex(ValueError, '^dependency-graph: ' + message + '$'):
                project.run(rows)

    def test_validation_precedes_selection_and_domain(self) -> None:
        rows = [
            {'id': 'A', 'target': 'missing', 'value': 1},
            {'id': 'a', 'target': 'a', 'value': 0},
        ]
        self.assertEqual(validation.validate(rows), [
            {'id': 'a', 'target': 'missing', 'value': 1},
            {'id': 'a', 'target': 'a', 'value': 0},
        ])
        for api in (project.run, project.render, engine.compute):
            with self.assertRaisesRegex(ValueError, '^dependency-graph: invalid row$'):
                api(rows + [{'id': 'broken'}])

    def test_structural_rules(self) -> None:
        class IntSubclass(int):
            pass

        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StrSubclass(str):
            pass

        for api in (project.run, project.render, engine.compute, validation.validate):
            with self.assertRaisesRegex(TypeError, '^dependency-graph: rows must be a list$'):
                api(())
            for bad in (None, {}, {'id': 'a', 'target': 'a', 'value': True},
                        {'id': 'a', 'target': 'a', 'value': IntSubclass(1)},
                        {'id': ' ', 'target': 'a', 'value': 1},
                        {'id': 'a', 'target': 2, 'value': 1},
                        {'id': 'a', 'target': 'a', 'value': 1, 'extra': 2}):
                with self.assertRaisesRegex(ValueError, '^dependency-graph: invalid row$'):
                    api([bad])
        rows = ListSubclass([DictSubclass(id=StrSubclass(' A '), target='a', value=10**200)])
        self.assertEqual(project.run(rows), {'order': ['a']})

    def test_unicode_normalization_and_rendering(self) -> None:
        name = ' Straße / 中  文 '
        canonical = 'strasse / 中  文'
        rows = [{'id': name, 'target': name, 'value': 0}]
        self.assertEqual(policy.normalize(name), canonical)
        self.assertEqual(validation.validate(rows)[0]['id'], canonical)
        self.assertEqual(project.run(rows), {'order': [canonical]})
        self.assertEqual(project.render(rows), '{"order":["strasse / 中  文"]}\n')

    def test_batch_atomicity_and_encounter_order(self) -> None:
        first = [{'id': 'x', 'target': 'missing', 'value': 1}]
        later = [{'id': 'bad', 'nested': {'unchanged': []}}]
        batches = [first, later]
        before = copy.deepcopy(batches)
        for api in (project.run_many, project.render_many):
            with self.assertRaisesRegex(ValueError, '^dependency-graph: missing dependency$'):
                api(batches)
            self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^dependency-graph: batches must be a list$'):
                api(())
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')

    def test_fresh_containers_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': 'a', 'value': 0}]
        before = copy.deepcopy(rows)
        results = project.run_many([rows, rows])
        results[0]['order'].append('changed')
        self.assertEqual(results[1], {'order': ['a']})
        self.assertEqual(project.run(rows), {'order': ['a']})
        canonical = validation.validate(rows)
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows, before)
        empty = project.run_many([[], []])
        empty[0]['order'].append('changed')
        self.assertEqual(empty[1], {'order': []})

    def test_runtime_engine_delegation_and_serialization(self) -> None:
        rows = [{'id': 'a', 'target': 'a', 'value': 0}]
        for api, argument, count in (
            (project.run, rows, 1), (project.render, rows, 1),
            (project.run_many, [rows, rows], 2),
            (project.render_many, [rows, rows], 2),
        ):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
        result = {'z': {'β': 2, 'a': 1}, 'a': [2, 1]}
        with patch.object(engine, 'compute', return_value=result):
            self.assertEqual(project.render(rows), json.dumps(
                result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')


if __name__ == '__main__':
    unittest.main()
