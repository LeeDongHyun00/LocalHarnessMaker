import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def booking(identifier='a', resource='room', start=0, end=1):
    return {'id': identifier, 'resource': resource, 'start': start, 'end': end}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [booking('last', ' ROOM ', 2, 3),
                booking(' FIRST ', 'Room', 0, 1),
                booking('middle', 'room', 1, 2),
                booking('other', 'elsewhere', 0, 3)]
        self.assertEqual(run(rows), {
            'bookings': [booking('other', 'elsewhere', 0, 3),
                         booking('first', 'room', 0, 3)],
            'resources': ['elsewhere', 'room']})

    def test_error_precedence_across_entry_points(self):
        cases = [
            ([booking(), booking('b', start=0, end=2), {}], 'invalid row'),
            ([booking(' A '), booking('a')], 'duplicate id'),
            ([booking(), booking('b', start=0, end=2)], 'conflict'),
            # A discarded id still participates in duplicate checks.
            ([booking(), booking('b', start=1, end=2),
              booking(' B ', 'elsewhere')], 'duplicate id'),
            # Domain checks follow input order after all fields validate.
            ([booking(), booking('b', end=2), booking('a', 'elsewhere')],
             'conflict'),
        ]
        for rows, message in cases:
            original = copy.deepcopy(rows)
            for call in (run, compute, render,
                         lambda value: run_many([[], value]),
                         lambda value: render_many([[], value])):
                with self.subTest(rows=rows, call=call):
                    with self.assertRaisesRegex(ValueError, '^reservations: ' + message + '$'):
                        call(rows)
                    self.assertEqual(rows, original)

    def test_validation(self):
        invalid = [None, [], {}, dict(booking(), extra=1)]
        for key, values in {
            'id': ['', '  ', None, 1],
            'resource': ['', '\t', None, 1],
            'start': [True, 0.0, '0', -1, 1],
            'end': [False, 1.0, '1', 0, -1],
        }.items():
            for value in values:
                row = booking()
                row[key] = value
                invalid.append(row)
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                    validate([row])
        for call in (validate, compute, run, render):
            for value in (None, (), {}, 'rows'):
                with self.subTest(call=call, value=value):
                    with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                        call(value)

    def test_subclasses_and_canonicalization(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(booking(' STRASSE ', ' Straße ', Integer(0), Integer(1)))])
        expected = [booking('strasse', 'strasse')]
        self.assertEqual(validate(rows), expected)
        self.assertEqual(run(rows)['bookings'], expected)
        self.assertEqual(normalize(' Straße '), 'strasse')

    def test_rendering(self):
        rows = [booking(' É"\nX ', ' 房間\\ ')]
        expected = '{"bookings":[{"end":1,"id":"é\\"\\nx","resource":"房間\\\\","start":0}],"resources":["房間\\\\"]}\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(json.loads(render(rows)), run(rows))

    def test_batches_and_empty_results(self):
        batches = [[booking(' A ')], [], [booking(' A ', 'other')]]
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for call in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                call(())
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                call([[booking()], None])

    def test_fresh_results_and_unchanged_inputs(self):
        rows = [booking(' A '), booking('b', start=1, end=2)]
        original = copy.deepcopy(rows)
        expected = run(rows)
        results = run_many([rows, rows])
        results[0]['bookings'][0]['end'] = 99
        results[0]['bookings'].append({})
        results[0]['resources'].append('extra')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        empty = run_many([[], []])
        self.assertIsNot(empty[0], empty[1])
        self.assertIsNot(empty[0]['bookings'], empty[1]['bookings'])
        self.assertIsNot(empty[0]['resources'], empty[1]['resources'])


if __name__ == '__main__':
    unittest.main()
