import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def row(key: str, target: str, value: int = 0) -> dict:
    return {'id': key, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def assert_error(self, function, argument, kind, message) -> None:
        with self.assertRaises(kind) as caught:
            function(argument)
        self.assertEqual(str(caught.exception), 'dependency-graph: ' + message)

    def test_domain_edge(self) -> None:
        rows = [row(' A ', 'A', 99), row('a', ' a ', 99),
                row('z', 'z', -100), row('b', 'a'), row('aa', 'b')]
        expected = {'order': ['a', 'z', 'b', 'aa']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'order': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_validation_order(self) -> None:
        rows = [row(' Straße / X ', ' STRASSE / X ', 10 ** 100),
                row(' A B ', 'Straße / X', -10 ** 100)]
        expected = {'order': ['strasse / x', 'a b']}
        self.assertEqual(policy.normalize(' Straße / X '), 'strasse / x')
        for function in (run, engine.compute):
            self.assertEqual(function(rows), expected)
        self.assertEqual(json.loads(render(rows)), expected)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(render_many([rows]), render(rows))
        canonical = validation.validate(rows + [rows[0]])
        self.assertEqual([r['id'] for r in canonical],
                         ['strasse / x', 'a b', 'strasse / x'])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        self.assertIsNot(canonical[0], rows[0])
        self.assertIsNot(canonical[0], canonical[2])
        # Validation does not select duplicates or resolve dependencies.
        self.assertEqual(validation.validate([row('x', 'missing'), row('x', 'x')]),
                         [row('x', 'missing'), row('x', 'x')])

    def test_structural_errors_precede_domain_errors(self) -> None:
        for prefix in ([row('a', 'a'), row('a', 'a', 1)],
                       [row('a', 'missing')],
                       [row('a', 'b'), row('b', 'a')]):
            rows = prefix + [row('bad', 'bad', True)]
            for function in (run, render, engine.compute, validation.validate):
                self.assert_error(function, rows, ValueError, 'invalid row')
            for function in (run_many, render_many):
                self.assert_error(function, [rows], ValueError, 'invalid row')

    def test_input_types(self) -> None:
        class IntSubclass(int):
            pass

        class StringSubclass(str):
            pass

        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        valid = ListSubclass([DictSubclass(row(StringSubclass(' A '), 'a'))])
        self.assertEqual(run(valid), {'order': ['a']})
        self.assertEqual(run_many(ListSubclass([valid])), [{'order': ['a']}])
        for value in (None, (), {}, 'rows', 1):
            for function in (run, render, engine.compute, validation.validate):
                self.assert_error(function, value, TypeError, 'rows must be a list')
            for function in (run_many, render_many):
                self.assert_error(function, value, TypeError, 'batches must be a list')
        malformed = [None, [], {}, row('', 'a'), row('a', ' \t'),
                     row(1, 'a'), row('a', None), row('a', 'a', True),
                     row('a', 'a', IntSubclass(1)), row('a', 'a', 1.0),
                     dict(row('a', 'a'), extra=0)]
        for invalid in malformed:
            self.assert_error(run, [invalid], ValueError, 'invalid row')

    def test_domain_errors(self) -> None:
        cases = [([row(' A ', 'a'), row('a', 'a', 1)], 'duplicate id'),
                 ([row('a', 'a'), row('a', 'b')], 'duplicate id'),
                 ([row('a', 'missing')], 'missing dependency'),
                 ([row('a', 'b'), row('b', 'a')], 'cycle')]
        for rows, message in cases:
            for function in (run, render, engine.compute):
                self.assert_error(function, rows, ValueError, message)
            for function in (run_many, render_many):
                self.assert_error(function, [rows], ValueError, message)

    def test_empty_and_serialization(self) -> None:
        self.assertEqual(run([]), {'order': []})
        self.assertEqual(render([]), '{"order":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(render([row(' É ', 'é')]), '{"order":["é"]}\n')
        payload = {'z': [{'z': 1, 'a': 'é'}], 'a': {'z': 0, 'a': 2}}
        with patch.object(engine, 'compute', return_value=payload):
            self.assertEqual(render([]),
                             '{"a":{"a":2,"z":0},"z":[{"a":"é","z":1}]}\n')

    def test_call_time_engine_lookup(self) -> None:
        rows = [row('a', 'a')]
        for function, argument, count in ((run, rows, 1), (render, rows, 1),
                                          (run_many, [rows, rows], 2),
                                          (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                function(argument)
                self.assertEqual(compute.call_count, count)
                self.assertTrue(all(call.args[0] is rows
                                    for call in compute.call_args_list))

    def test_atomic_batch_failure_order_and_no_mutation(self) -> None:
        valid = [row(' A ', 'a')]
        failure = [row('x', 'missing')]
        later = [row('bad', 'bad', {'nested': []})]
        batches = [valid, failure, later]
        original = copy.deepcopy(batches)
        for function in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                self.assert_error(function, batches, ValueError, 'missing dependency')
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], valid)
                self.assertIs(compute.call_args_list[1].args[0], failure)
            self.assertEqual(batches, original)
        for function in (run, render, engine.compute, validation.validate):
            self.assert_error(function, later, ValueError, 'invalid row')
            self.assertEqual(batches, original)

    def test_output_independence(self) -> None:
        rows = [row(' A ', 'a')]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        other = run(rows)
        results[0]['order'].append('changed')
        self.assertEqual(results[1], {'order': ['a']})
        self.assertEqual(other, {'order': ['a']})
        self.assertEqual(run(rows), {'order': ['a']})
        self.assertEqual(rows, original)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        self.assertEqual(validation.validate(rows)[0]['id'], 'a')


if __name__ == '__main__':
    unittest.main()
