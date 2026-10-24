import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def booking(id='a', resource='room', start=0, end=2):
    return dict(id=id, resource=resource, start=start, end=end)


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        self.assertEqual(run([
            booking('B', ' ROOM ', 2, 4), booking('A', 'room', 0, 2),
        ]), {
            'bookings': [booking('a', 'room', 0, 2), booking('b', 'room', 2, 4)],
            'resources': ['room'],
        })

    def test_canonicalization_and_order(self):
        rows = [booking(' Z ', ' Zebra '), booking(' Straße ', ' ROOM ')]
        expected = {
            'bookings': [booking('strasse', 'room'), booking('z', 'zebra')],
            'resources': ['room', 'zebra'],
        }
        self.assertEqual(normalize(' Straße '), 'strasse')
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(list(run(rows)), ['bookings', 'resources'])
        self.assertEqual(list(run(rows)['bookings'][0]), ['id', 'resource', 'start', 'end'])

    def test_shape_and_fields(self):
        for rows in (None, (), {}, 'rows', iter([])):
            with self.subTest(rows=rows):
                with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                    run(rows)
        invalid = [None, [], {}, dict(booking(), extra=0)]
        for key, values in {
            'id': [None, 1, '', '  '], 'resource': [None, 1, '', '\t'],
            'start': [True, False, 0.0, '0', -1, 2],
            'end': [True, False, 2.0, '2', 0, -1],
        }.items():
            invalid.extend(dict(booking(), **{key: value}) for value in values)
        for key in booking():
            row = booking()
            del row[key]
            invalid.append(row)
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                    run([row])

    def test_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Number(int):
            pass

        self.assertEqual(run(Rows([Row(booking(start=Number(0)))])), run([booking()]))

    def test_domain_errors_and_precedence(self):
        cases = [
            ([booking(), booking(' A ', ' ROOM ')], 'duplicate id'),
            ([booking(), booking('b', ' ROOM ', 1, 3)], 'conflict'),
            ([booking(), booking('b'), {}], 'invalid row'),
            ([booking(), booking(' A '), {}], 'invalid row'),
            ([booking(), booking('b'), booking(' A ')], 'conflict'),
        ]
        for rows, error in cases:
            for operation in (run, compute, render):
                with self.subTest(rows=rows, operation=operation):
                    with self.assertRaisesRegex(ValueError, '^reservations: ' + error + '$'):
                        operation(rows)
        self.assertEqual(len(run([booking(), booking('b', 'other')])['bookings']), 2)

    def test_immutability_and_fresh_results(self):
        rows = [booking(' A ', ' ROOM ')]
        original = copy.deepcopy(rows)
        first = run(rows)
        self.assertEqual(rows, original)
        first['bookings'][0]['id'] = 'changed'
        first['bookings'].append({})
        first['resources'].append('changed')
        self.assertEqual(rows, original)
        self.assertEqual(run(rows), {'bookings': [booking()], 'resources': ['room']})
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        for bad_rows in (rows + [booking('a')], rows + [booking('b')], rows + [{}]):
            before = copy.deepcopy(bad_rows)
            with self.assertRaises(ValueError):
                run(bad_rows)
            self.assertEqual(bad_rows, before)

    def test_render_and_empty(self):
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(render([]), '{"bookings":[],"resources":[]}\n')
        self.assertEqual(render([booking(' É"\\\n ', ' 방 ')]),
                         '{"bookings":[{"end":2,"id":"é\\"\\\\","resource":"방","start":0}],"resources":["방"]}\n')
        first = run([])
        first['bookings'].append({})
        first['resources'].append('changed')
        self.assertEqual(run([]), {'bookings': [], 'resources': []})

    def test_batch_outer_types_and_empty(self):
        for operation in (run_many, render_many):
            for batches in (None, (), {}, 'batches', iter([])):
                with self.subTest(operation=operation, batches=batches):
                    with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                        operation(batches)
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_batch_order_and_render(self):
        batches = [
            [booking(' Z ', ' Zebra ')],
            [],
            [booking('B', ' ROOM ', 2, 4), booking('A', 'room', 0, 2)],
            [booking(' É"\\\n ', ' 방 ')],
        ]
        original = copy.deepcopy(batches)
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(render_many(batches).count('\n'), len(batches))
        self.assertEqual(batches, original)

    def test_batch_member_errors_and_precedence(self):
        cases = [
            (None, TypeError, 'rows must be a list'),
            ((), TypeError, 'rows must be a list'),
            ([{}], ValueError, 'invalid row'),
            ([booking(start=True)], ValueError, 'invalid row'),
            ([booking(), booking(' A ')], ValueError, 'duplicate id'),
            ([booking(), booking('b')], ValueError, 'conflict'),
            ([booking(), booking(' A '), {}], ValueError, 'invalid row'),
            ([booking(), booking('b'), {}], ValueError, 'invalid row'),
            ([booking(), booking('b'), booking(' A ')], ValueError, 'conflict'),
        ]
        for rows, error_type, message in cases:
            for operation in (run_many, render_many):
                for batches in ([rows, [booking()]], [[booking()], rows]):
                    with self.subTest(operation=operation, batches=batches):
                        original = copy.deepcopy(batches)
                        with self.assertRaisesRegex(error_type, '^reservations: ' + message + '$'):
                            operation(batches)
                        self.assertEqual(batches, original)
        # Complete each member before moving on to the next member's validation.
        for operation in (run_many, render_many):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(ValueError, '^reservations: conflict$'):
                    operation([[booking(), booking('b')], [{}]])

    def test_batch_independent_results(self):
        rows = [booking(' A ', ' ROOM ')]
        batches = [rows, rows, [], []]
        original = copy.deepcopy(batches)
        expected = [run(member) for member in batches]
        result = run_many(batches)
        result[0]['bookings'][0]['id'] = 'changed'
        result[0]['bookings'].append({})
        result[0]['resources'].append('changed')
        result[2]['bookings'].append({})
        result[2]['resources'].append('changed')
        self.assertEqual(result[1], expected[1])
        self.assertEqual(result[3], expected[3])
        self.assertEqual(batches, original)
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(render_many(batches), ''.join(render(member) for member in batches))
        empty = run_many([])
        empty.append({})
        self.assertEqual(run_many([]), [])

    def test_batch_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        batches = Rows([Rows([Row(booking(' A ', ' ROOM '))])])
        self.assertEqual(run_many(batches), [run([booking()])])
        self.assertEqual(render_many(batches), render([booking()]))


if __name__ == '__main__':
    unittest.main()
