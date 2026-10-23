import copy
import json
import unittest
from unittest.mock import call, patch

from project import render, render_many, run, run_many
from project import policy
from project.engine import compute
from project.validation import validate


def booking(identifier='b1', resource='room', start=1, end=2):
    return {'id': identifier, 'resource': resource, 'start': start, 'end': end}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [booking(' B2 ', ' ROOM ', 2, 3), booking('B1', 'room', 1, 2)]
        self.assertEqual(run(rows), {
            'bookings': [booking('b1'), booking('b2', start=2, end=3)],
            'resources': ['room'],
        })
        with self.assertRaisesRegex(ValueError, '^reservations: conflict$'):
            run([booking('a', start=1, end=3), booking('b', start=2, end=4)])
        self.assertEqual(len(run([booking('a'), booking('b', 'other')])['bookings']), 2)

    def test_runtime_policy_patch(self):
        rows = [booking(' B1 ', ' ROOM ')]
        normalized = {'bookings': [booking('patched:b1', 'patched:room')],
                      'resources': ['patched:room']}
        serialized = json.dumps(normalized, sort_keys=True, separators=(',', ':')) + '\n'
        for function, argument, expected in (
            (run, rows, normalized), (render, rows, serialized),
            (run_many, [rows], [normalized]), (render_many, [rows], serialized),
            (compute, rows, normalized), (validate, rows, normalized['bookings']),
        ):
            with self.subTest(function=function.__name__):
                with patch.object(policy, 'normalize', side_effect=lambda value: 'patched:' + value.strip().casefold()) as mocked:
                    self.assertEqual(function(argument), expected)
                    self.assertEqual(mocked.call_args_list, [call(' B1 '), call(' ROOM ')])
        self.assertEqual(policy.normalize(' Straße '), 'strasse')

    def test_field_errors_precede_domain_errors(self):
        for prefix in (
            [booking('a'), booking(' A ')],
            [booking('a'), booking('b')],
        ):
            rows = prefix + [booking('bad', end=True)]
            for function, argument in ((run, rows), (render, rows),
                                       (run_many, [[], rows]), (render_many, [[], rows])):
                with self.subTest(function=function.__name__, rows=rows):
                    with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                        function(argument)
        with self.assertRaisesRegex(ValueError, '^reservations: duplicate id$'):
            run([booking(' Straße '), booking('STRASSE')])

    def test_input_validation(self):
        for function in (run, render, compute, validate):
            for rows in (None, (), {}, 'rows'):
                with self.subTest(function=function.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                        function(rows)
        invalid = [None, [], {}, dict(booking(), extra=1)]
        for key, values in {'id': ['', '  ', None, 1], 'resource': ['', ' ', None, 1],
                            'start': [True, 1.0, '1', -1, 2],
                            'end': [False, 2.0, '2', 0, 1]}.items():
            invalid.extend(dict(booking(), **{key: value}) for value in values)
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                    run([row])

        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        self.assertEqual(run(Rows([Row(booking(start=Integer(1)))])), run([booking()]))

    def test_fresh_results_and_atomic_batches(self):
        rows = [booking(' B1 ', ' ROOM ')]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['bookings'][0]['id'] = 'changed'
        results[0]['resources'].append('changed')
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, original)
        bad = [booking('a'), booking('b')]
        bad_original = copy.deepcopy(bad)
        for function in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^reservations: conflict$'):
                function([rows, bad])
            self.assertEqual(rows, original)
            self.assertEqual(bad, bad_original)
            for batches in (None, (), {}):
                with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                    function(batches)

    def test_render_order_and_empty_results(self):
        rows = [booking(' Z ', '二', 3, 4), booking(' B ', 'é'), booking('A', 'é')]
        rows[2]['start'], rows[2]['end'] = 0, 1
        result = run(rows)
        self.assertEqual([row['id'] for row in result['bookings']], ['a', 'b', 'z'])
        self.assertEqual(list(result), ['bookings', 'resources'])
        self.assertEqual(result['resources'], ['é', '二'])
        self.assertEqual(render(rows), json.dumps(result, ensure_ascii=False, sort_keys=True,
                                                separators=(',', ':')) + '\n')
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
