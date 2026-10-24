import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


def row(identifier='item', target='bucket', value=1):
    return {'id': identifier, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def assert_domain_error(self, rows, message, exception=ValueError):
        for api in (project.run, project.render, engine.compute,
                    lambda rows: project.run_many([rows]),
                    lambda rows: project.render_many([rows])):
            with self.subTest(api=api):
                with self.assertRaises(exception) as caught:
                    api(rows)
                self.assertEqual(str(caught.exception), 'rate-budgets: ' + message)

    def test_domain_edge(self):
        rows = [row(' A ', 'old', 20), row('b', ' Pool ', 40),
                row('a', 'POOL', 60), row('a', 'ignored', 10),
                row(' A', 'pool', 60)]
        expected = {'remaining': {'pool': 0}}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]),
                         [expected, {'remaining': {}}])
        self.assertEqual(project.render_many([rows, []]),
                         '{"remaining":{"pool":0}}\n{"remaining":{}}\n')
        self.assert_domain_error(rows + [row('c', 'pool', 1)], 'exhausted')

    def test_structural_validation_precedes_selection_and_domain(self):
        for prefix in ([row(value=-1)], [row(value=101)],
                       [row(target='a'), row(target='b')]):
            self.assert_domain_error(prefix + [row(value=True)], 'invalid row')
        huge = 10 ** 200
        rows = [row(value=-huge), row(value=huge), row(' ITEM ', value=huge)]
        self.assertEqual(validation.validate(rows),
                         [row(value=-huge), row(value=huge), row(value=huge)])
        self.assert_domain_error(rows, 'invalid cost')

    def test_invalid_shapes_and_exact_integer_type(self):
        class Integer(int):
            pass

        for rows in (None, (), {}, 'rows', iter([])):
            self.assert_domain_error(rows, 'rows must be a list', TypeError)
        malformed = [None, [], {}, {**row(), 'extra': 0},
                     {'id': 'x', 'target': 'y'}, row(identifier=' \t'),
                     row(target='\n'), row(identifier=1), row(target=None),
                     row(value=True), row(value=Integer(1)), row(value=1.0)]
        for invalid in malformed:
            self.assert_domain_error([invalid], 'invalid row')

    def test_normalization_subclasses_order_and_unicode(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(row(Text(' Straße / X '), Text(' Z / 한 글 '), 0)),
                     row('b', ' A  B ', 1), row(' STRASSE / x', 'new', 2)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [row('strasse / x', 'z / 한 글', 0),
                                     row('b', 'a  b', 1),
                                     row('strasse / x', 'new', 2)])
        self.assertIsNot(canonical, rows)
        self.assertTrue(all(a is not b for a, b in zip(canonical, rows)))
        self.assertEqual(policy.normalize(Text(' Straße / 한 글 ')), 'strasse / 한 글')
        with patch.object(engine, 'resolve', return_value={}) as resolve:
            engine.compute(rows)
        self.assertEqual(resolve.call_args.args[0], [canonical[2], canonical[1]])
        result = project.run(rows)
        self.assertEqual(list(result['remaining']), ['a  b', 'new'])
        unicode_rows = [row(target=' 한 글 / Straße ')]
        self.assertEqual(project.render(unicode_rows),
                         json.dumps(project.run(unicode_rows), ensure_ascii=False,
                                    sort_keys=True, separators=(',', ':')) + '\n')

    def test_ambiguity_is_not_erased_and_cost_precedes_totals(self):
        self.assert_domain_error([row(target='a', value=2),
                                  row(target='b', value=2), row(value=3)],
                                 'ambiguous id')
        self.assert_domain_error([row('a', value=100), row('b', value=1),
                                  row('c', value=-1)], 'invalid cost')
        for cost in (-1, 101, 10 ** 100):
            self.assert_domain_error([row(value=cost)], 'invalid cost')
        self.assertEqual(project.run([row(value=0)]), {'remaining': {'bucket': 100}})

    def test_empty_inputs_and_outer_validation(self):
        self.assertEqual(project.run([]), {'remaining': {}})
        self.assertEqual(project.render([]), '{"remaining":{}}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        for api in (project.run_many, project.render_many):
            for batches in (None, (), {}, 'batches', iter([])):
                with self.assertRaises(TypeError) as caught:
                    api(batches)
                self.assertEqual(str(caught.exception),
                                 'rate-budgets: batches must be a list')

    def test_each_member_uses_current_engine_once_in_order(self):
        batches = [[row('a')], [], [row('b', 'other', 20)]]
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(batches)
            self.assertEqual(compute.call_count, len(batches))
            self.assertEqual([call.args[0] for call in compute.call_args_list], batches)
        for api in (project.run, project.render):
            with patch.object(engine, 'compute', return_value={'z': {'b': 1, 'a': 2},
                                                             'a': {}}) as compute:
                result = api([])
            compute.assert_called_once_with([])
            if api is project.render:
                self.assertEqual(result, '{"a":{},"z":{"a":2,"b":1}}\n')

    def test_batch_failure_order_atomicity_and_input_preservation(self):
        for api in (project.run_many, project.render_many):
            batches = [[row()], [row(value=101)], [row(value=True)]]
            original = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid cost$'):
                    api(batches)
            self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, original)
        for api in (project.run, project.render, validation.validate, engine.compute):
            rows = [row(), {'id': 'bad', 'target': 'bucket', 'value': {'nested': []}}]
            original = copy.deepcopy(rows)
            with self.assertRaises(ValueError):
                api(rows)
            self.assertEqual(rows, original)

    def test_results_are_fresh_across_members_and_calls(self):
        rows = [row()]
        original = copy.deepcopy(rows)
        results = project.run_many([rows, rows])
        results[0]['remaining']['bucket'] = -1
        self.assertEqual(results[1], {'remaining': {'bucket': 99}})
        results[1]['remaining']['new'] = 7
        self.assertEqual(project.run(rows), {'remaining': {'bucket': 99}})
        self.assertEqual(rows, original)
        canonical = validation.validate(rows)
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows, original)
        empty_results = project.run_many([[], []])
        empty_results[0]['remaining']['new'] = 1
        self.assertEqual(empty_results[1], {'remaining': {}})


if __name__ == '__main__':
    unittest.main()
