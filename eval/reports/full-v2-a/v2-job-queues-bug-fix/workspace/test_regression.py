import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': ' Straße/ A ', 'value': 4},
            {'id': 'a', 'target': 'STRASSE/ A', 'value': 4},
            {'id': 'z', 'target': 'strasse/ a', 'value': 4},
            {'id': 'high', 'target': 'strasse/ a', 'value': 10**100},
            {'id': 'low', 'target': 'strasse/ a', 'value': -10**100},
            {'id': 'other', 'target': ' A ', 'value': 0},
        ]
        expected = {'queues': {'a': ['other'], 'strasse/ a': ['high', 'z', 'a', 'low']}}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(list(project.run(rows)['queues']), ['a', 'strasse/ a'])
        self.assertEqual(project.run_many([rows, []]), [expected, {'queues': {}}])
        rendered = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(project.render(rows), rendered)
        self.assertEqual(project.render_many([rows, []]), rendered + '{"queues":{}}\n')

    def test_validation_and_precedence(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        rows = ListSubclass([DictSubclass(id=StringSubclass(' A '), target=' B ', value=1)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'a', 'target': 'b', 'value': 1}])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' Straße/ X  Y '), 'strasse/ x  y')
        duplicate = [dict(id='A', target='x', value=1), dict(id='a', target='y', value=1)]
        self.assertEqual(len(validation.validate(duplicate)), 2)
        for api in (project.run, project.render, engine.compute):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^job-queues: duplicate id$'):
                    api(duplicate)
                for bad in (None, {}, dict(id='', target='x', value=1),
                            dict(id='x', target=' ', value=1),
                            dict(id=1, target='x', value=1),
                            dict(id='x', target=None, value=1),
                            dict(id='x', target='y', value=True),
                            dict(id='x', target='y', value=IntSubclass(1)),
                            dict(id='x', target='y', value=1, extra=0)):
                    with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                        api(duplicate + [bad])
        for api in (project.run, project.render, engine.compute, validation.validate):
            for bad in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^job-queues: rows must be a list$'):
                    api(bad)

    def test_fresh_results_and_unchanged_inputs(self) -> None:
        rows = [dict(id=' A ', target=' B ', value=1)]
        before = copy.deepcopy(rows)
        outputs = project.run_many([rows, rows])
        outputs[0]['queues']['b'].append('changed')
        outputs[0]['queues']['new'] = []
        self.assertEqual(outputs[1], {'queues': {'b': ['a']}})
        self.assertEqual(project.run(rows), outputs[1])
        self.assertEqual(rows, before)
        invalid = rows + [dict(id='a', target='different', value=1), {'nested': {'x': []}}]
        invalid_before = copy.deepcopy(invalid)
        for api in (project.run, project.render):
            with self.assertRaises(ValueError):
                api(invalid)
            self.assertEqual(invalid, invalid_before)

    def test_batches_and_runtime_dispatch(self) -> None:
        rows = [dict(id='É', target='Ω', value=1)]
        self.assertEqual(project.render(rows), '{"queues":{"ω":["é"]}}\n')
        for api in (project.run, project.render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(rows)
                compute.assert_called_once_with(rows)
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api([rows, []])
                self.assertEqual(compute.call_args_list, [unittest.mock.call(rows), unittest.mock.call([])])
            for bad in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^job-queues: batches must be a list$'):
                    api(bad)
            first_failure = [dict(id='a', target='x', value=1), dict(id='a', target='y', value=1)]
            batches = [rows, first_failure, None]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^job-queues: duplicate id$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)
        self.assertEqual(project.run([]), {'queues': {}})
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')


if __name__ == '__main__':
    unittest.main()
