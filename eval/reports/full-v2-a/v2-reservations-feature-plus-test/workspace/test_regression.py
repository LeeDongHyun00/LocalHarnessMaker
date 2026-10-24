import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def booking(identifier='b1', resource='room', start=1, end=2):
    return dict(id=identifier, resource=resource, start=start, end=end)


class RegressionTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [booking(' B ', ' ROOM ', 2, 3), booking(' A ', 'Room', 1, 2)]
        expected = {'bookings': [booking('a'), booking('b', start=2, end=3)],
                    'resources': ['room']}
        self.assertEqual(run_many([[], rows]), [run([]), expected])
        self.assertEqual(render_many([[], rows]), render([]) + render(rows))
        self.assertEqual(run([booking('a'), booking('b', 'other')])['resources'],
                         ['other', 'room'])

    def test_validation_and_domain_error_precedence(self):
        conflict = [booking('a'), booking('b')]
        duplicate = [booking(' A '), booking('a')]
        for rows, message in ((conflict, 'conflict'), (duplicate, 'duplicate id'),
                              (conflict + [{}], 'invalid row'),
                              (duplicate + [{}], 'invalid row')):
            for operation, value in ((run, rows), (render, rows),
                                     (run_many, [[], rows]),
                                     (render_many, [[], rows])):
                with self.subTest(operation=operation.__name__, message=message):
                    before = copy.deepcopy(value)
                    with self.assertRaisesRegex(ValueError, '^reservations: ' + message + '$'):
                        operation(value)
                    self.assertEqual(value, before)

    def test_invalid_shapes_and_fields(self):
        for operation in (run_many, render_many):
            for value in (None, {}, (), 'rows'):
                with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                    operation(value)
        for operation in (run, compute, validate, render):
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                operation(())
        for operation in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                operation([[], ()])
        invalid = [None, {}, dict(booking(), extra=0)]
        for field, values in {'id': ['', ' ', 1, None],
                              'resource': ['', '\t', 1, None],
                              'start': [True, 1.0, -1, 2],
                              'end': [False, 2.0, 0, 1]}.items():
            for value in values:
                row = booking()
                row[field] = value
                invalid.append(row)
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                    run_many([[row]])

    def test_canonicalization_order_and_rendering(self):
        rows = [booking(' Z ', ' Straße ', 4, 5),
                booking(' Ä" ', ' A ', 1, 2),
                booking('b', 'STRASSE', 0, 4)]
        expected = {'bookings': [booking('ä"', 'a'),
                                 booking('b', 'strasse', 0, 4),
                                 booking('z', 'strasse', 4, 5)],
                    'resources': ['a', 'strasse']}
        self.assertEqual(normalize(' Straße '), 'strasse')
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(list(run(rows)), ['bookings', 'resources'])
        self.assertEqual(list(run(rows)['bookings'][0]), ['id', 'resource', 'start', 'end'])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows, rows]), encoded * 2)

    def test_fresh_results_and_independent_batches(self):
        rows = [booking(' B1 ', ' ROOM ')]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['bookings'][0]['id'] = 'changed'
        results[0]['resources'].append('changed')
        results[0]['bookings'].append({})
        self.assertEqual(rows, before)
        self.assertEqual(results[1], run(rows))
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['resources'].append('changed')
        empty[0]['bookings'].append({})
        self.assertEqual(empty[1], {'bookings': [], 'resources': []})

    def test_allowed_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(booking(start=Integer(1), end=Integer(2)))])
        self.assertEqual(run_many(Rows([rows])), [run([booking()])])


if __name__ == '__main__':
    unittest.main()
