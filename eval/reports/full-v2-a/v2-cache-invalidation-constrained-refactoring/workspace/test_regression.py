import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def row(key: str, target: str, value: int) -> dict:
    return {'id': key, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def assert_error(self, rows: object, error: type[Exception], message: str) -> None:
        for api in (run, render, engine.compute):
            with self.subTest(api=api.__name__):
                with self.assertRaises(error) as caught:
                    api(rows)
                self.assertEqual(str(caught.exception), 'cache-invalidation: ' + message)

    def test_domain_edge(self) -> None:
        rows = [row(' Leaf ', 'BRANCH', 9), row('ROOT', 'root', 0),
                row('branch', 'root', 4), row('leaf', 'branch', 9),
                row('safe', 'safe', 10 ** 200)]
        expected = {'dirty': ['branch', 'leaf', 'root'], 'clean': ['safe']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'dirty': [], 'clean': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_structural_errors_precede_selection_and_domain(self) -> None:
        prefixes = [
            [row('a', 'a', 1), row('A', 'a', 2)],
            [row('a', 'a', -1)],
            [row('a', 'absent', 1)],
            [row('a', 'b', 1), row('b', 'a', 1)],
        ]
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                self.assert_error(prefix + [row('later', 'later', True)],
                                  ValueError, 'invalid row')

    def test_structure_and_exact_integer_type(self) -> None:
        class Integer(int):
            pass

        for rows in (None, (), {}, 'rows'):
            self.assert_error(rows, TypeError, 'rows must be a list')
        for bad in (None, [], {}, row('', 'a', 1), row('a', ' \t', 1),
                    row(1, 'a', 1), row('a', None, 1), row('a', 'a', True),
                    row('a', 'a', Integer(1)), row('a', 'a', 1.0),
                    dict(row('a', 'a', 1), extra=1)):
            self.assert_error([bad], ValueError, 'invalid row')

    def test_normalization_subclasses_and_validation_order(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        text = Text('  Straße / A  B  ')
        key = 'strasse / a  b'
        rows = Rows([Row(row(text, text, 1)), row('Z', 'z', -1),
                     row('STRASSE / A  B', 'strasse / a  b', 2)])
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(policy.normalize(text), key)
        self.assertEqual(canonical, [row(key, key, 1), row('z', 'z', -1),
                                     row(key, key, 2)])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        self.assertEqual(run(Rows([Row(row(text, text, 1))])),
                         {'dirty': [], 'clean': [key]})

    def test_domain_error_precedence(self) -> None:
        self.assert_error([row('a', 'a', -1), row('A', 'a', 1)],
                          ValueError, 'duplicate id')
        self.assert_error([row('a', 'missing', -10 ** 200), row('b', 'c', 1),
                           row('c', 'b', 1)], ValueError, 'negative generation')
        self.assert_error([row('a', 'missing', 1), row('b', 'c', 1),
                           row('c', 'b', 1)], ValueError, 'missing dependency')
        self.assert_error([row('a', 'b', 0), row('b', 'a', 1)], ValueError, 'cycle')

    def test_empty_inputs_and_dictionary_order(self) -> None:
        self.assertEqual(run([]), {'dirty': [], 'clean': []})
        self.assertEqual(list(run([])), ['dirty', 'clean'])
        self.assertEqual(render([]), '{"clean":[],"dirty":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_unicode_json_and_sorted_output(self) -> None:
        rows = [row('É', 'é', 1), row('z', 'z', 0), row('a', 'z', 1)]
        self.assertEqual(run(rows), {'dirty': ['a', 'z'], 'clean': ['é']})
        self.assertEqual(render(rows), '{"clean":["é"],"dirty":["a","z"]}\n')
        self.assertEqual(json.loads(render(rows)), run(rows))

    def test_output_independence_and_no_input_mutation(self) -> None:
        rows = [row('A', 'a', 0)]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['dirty'].append('changed')
        results[0]['clean'].append('changed')
        self.assertEqual(results[1], {'dirty': ['a'], 'clean': []})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['dirty'].append('changed')
        self.assertEqual(empty[1], {'dirty': [], 'clean': []})

    def test_batch_errors_are_atomic_and_in_encounter_order(self) -> None:
        for api in (run_many, render_many):
            for outer in (None, (), {}, 'batches'):
                with self.assertRaises(TypeError) as caught:
                    api(outer)
                self.assertEqual(str(caught.exception),
                                 'cache-invalidation: batches must be a list')
            batches = [[row('OK', 'ok', 1)], [row('bad', 'absent', 1)],
                       [row('invalid', 'invalid', True)]]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaises(ValueError) as caught:
                    api(batches)
                self.assertEqual(str(caught.exception),
                                 'cache-invalidation: missing dependency')
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], batches[0])
                self.assertIs(compute.call_args_list[1].args[0], batches[1])
            self.assertEqual(batches, before)

    def test_all_facades_resolve_compute_at_call_time(self) -> None:
        batches = [[row('b', 'b', 0)], [row('a', 'a', 1)]]
        with patch.object(engine, 'compute', wraps=engine.compute) as compute:
            self.assertEqual(run(batches[0]), {'dirty': ['b'], 'clean': []})
            self.assertEqual(render(batches[0]), '{"clean":[],"dirty":["b"]}\n')
            self.assertEqual(run_many(batches), [
                {'dirty': ['b'], 'clean': []}, {'dirty': [], 'clean': ['a']}])
            self.assertEqual(render_many(batches),
                             '{"clean":[],"dirty":["b"]}\n'
                             '{"clean":["a"],"dirty":[]}\n')
            self.assertEqual(compute.call_count, 6)
            self.assertEqual([call.args[0] for call in compute.call_args_list],
                             [batches[0], batches[0], *batches, *batches])


if __name__ == '__main__':
    unittest.main()
