import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def row(key, target, value):
    return {'id': key, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [row(' Leaf ', 'MID', 9), row('Root', 'ROOT', 0),
                row('mid', 'root', 3), row(' leaf', 'mid ', 9),
                row('Clean', 'clean', 10 ** 100)]
        expected = {'dirty': ['leaf', 'mid', 'root'], 'clean': ['clean']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'dirty': [], 'clean': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_validation_order(self) -> None:
        rows = [row(' Straße / X ', ' STRASSE / X ', -1),
                row(' Other ', 'Missing', 2), row('strasse / x', 'other', 1)]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [row('strasse / x', 'strasse / x', -1),
                                     row('other', 'missing', 2),
                                     row('strasse / x', 'other', 1)])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        self.assertEqual(policy.normalize(' É / A  B '), 'é / a  b')
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows[0]['id'], ' Straße / X ')
        self.assert_error(rows + [row('bad', 'bad', True)], ValueError, 'invalid row')
        self.assert_error(rows, ValueError, 'duplicate id')

    def assert_error(self, rows, kind, message) -> None:
        for call in (run, render, engine.compute,
                     lambda value: run_many([value]),
                     lambda value: render_many([value])):
            with self.subTest(call=call, message=message):
                with self.assertRaises(kind) as caught:
                    call(rows)
                self.assertEqual(str(caught.exception), 'cache-invalidation: ' + message)

    def test_structure(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StrSubclass(str):
            pass

        class IntSubclass(int):
            pass

        self.assertEqual(run(ListSubclass([DictSubclass(row(StrSubclass(' A '), 'a', 1))])),
                         {'dirty': [], 'clean': ['a']})
        for rows in (None, (), {}, 'abc'):
            self.assert_error(rows, TypeError, 'rows must be a list')
        for bad in (None, [], {}, row('', 'a', 1), row('a', '  ', 1),
                    row(1, 'a', 1), row('a', None, 1), row('a', 'a', True),
                    row('a', 'a', IntSubclass(1)), row('a', 'a', 1.0),
                    dict(row('a', 'a', 1), extra=2)):
            self.assert_error([bad], ValueError, 'invalid row')

    def test_domain_error_precedence(self) -> None:
        self.assert_error([row('a', 'missing', -1), row('b', 'c', 1), row('c', 'b', 1)],
                          ValueError, 'negative generation')
        self.assert_error([row('a', 'missing', 1), row('b', 'c', 1), row('c', 'b', 1)],
                          ValueError, 'missing dependency')
        self.assert_error([row('a', 'b', 0), row('b', 'a', 1)], ValueError, 'cycle')
        self.assert_error([row('A', 'a', -1), row('a', 'a', 1)], ValueError, 'duplicate id')
        for domain in ([row('a', 'a', -1)], [row('a', 'missing', 1)],
                       [row('a', 'b', 1), row('b', 'a', 1)]):
            self.assert_error(domain + [{}], ValueError, 'invalid row')

    def test_fresh_results_and_no_mutation(self) -> None:
        rows = [row(' A ', 'a', 0)]
        snapshot = copy.deepcopy(rows)
        results = run_many([rows, rows])
        self.assertEqual(list(results[0]), ['dirty', 'clean'])
        results[0]['dirty'].append('changed')
        results[0]['clean'].append('changed')
        self.assertEqual(results[1], {'dirty': ['a'], 'clean': []})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(rows, snapshot)
        bad = [row(' A ', 'a', -1), row('a', 'a', 1)]
        before = copy.deepcopy(bad)
        for call in (run_many, render_many):
            with self.assertRaises(ValueError):
                call([rows, bad, rows])
            self.assertEqual(bad, before)
            self.assertEqual(rows, snapshot)

    def test_shared_compute_and_atomic_order(self) -> None:
        rows = [row('a', 'a', 1)]
        for call, argument, count in ((run, rows, 1), (render, rows, 1),
                                      (run_many, [rows, rows], 2),
                                      (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                call(argument)
                self.assertEqual(compute.call_count, count)
        for call in (run_many, render_many):
            error = ValueError('instrumented failure')
            with patch.object(engine, 'compute', side_effect=[{'dirty': [], 'clean': []}, error]) as compute:
                with self.assertRaises(ValueError) as caught:
                    call([rows, rows, None])
                self.assertIs(caught.exception, error)
                self.assertEqual(compute.call_count, 2)
            with self.assertRaisesRegex(ValueError, 'negative generation'):
                call([[row('a', 'a', -1)], None])

    def test_render_empty_and_outer_validation(self) -> None:
        rows = [row(' É ', 'é', 0)]
        self.assertEqual(render(rows), '{"clean":[],"dirty":["é"]}\n')
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False,
                                                sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'dirty': [], 'clean': []})
        self.assertEqual(render([]), '{"clean":[],"dirty":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for call in (run_many, render_many):
            for outer in (None, (), {}, 'abc'):
                with self.assertRaises(TypeError) as caught:
                    call(outer)
                self.assertEqual(str(caught.exception), 'cache-invalidation: batches must be a list')

    def test_deep_dependency_chain(self) -> None:
        rows = [row(str(i), str(max(0, i - 1)), int(i != 0)) for i in range(2000)]
        self.assertEqual(run(rows), {'dirty': sorted(str(i) for i in range(2000)), 'clean': []})


if __name__ == '__main__':
    unittest.main()
