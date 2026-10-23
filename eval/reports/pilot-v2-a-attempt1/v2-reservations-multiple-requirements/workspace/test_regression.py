import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def booking(id='a', resource='room', start=1, end=2):
    return dict(id=id, resource=resource, start=start, end=end)


class RegressionTests(unittest.TestCase):
    def assert_single_error(self, rows, error, message):
        for call in (run, compute, render):
            with self.subTest(call=call.__name__):
                with self.assertRaisesRegex(error, '^' + message + '$'):
                    call(rows)
        for call in (run_many, render_many):
            with self.subTest(call=call.__name__):
                with self.assertRaisesRegex(error, '^' + message + '$'):
                    call([[], rows])

    def test_domain_edge(self):
        rows = [booking('last', ' ROOM ', 4, 6),
                booking('FIRST', 'room', 0, 2),
                booking('middle', 'Room', 2, 4),
                booking('other', 'desk', 1, 5)]
        self.assertEqual(run(rows), {
            'bookings': [booking('other', 'desk', 1, 5),
                         booking('first', 'room', 0, 6)],
            'resources': ['desk', 'room']})

    def test_duplicate_before_coalescing_and_conflict(self):
        self.assert_single_error(
            [booking('a', start=0, end=1), booking('B', start=1, end=2),
             booking(' b ', start=0, end=3)],
            ValueError, 'reservations: duplicate id')

    def test_overlap_and_input_order_precedence(self):
        self.assert_single_error(
            [booking('a', ' ROOM ', 0, 3), booking('b', 'room', 2, 4)],
            ValueError, 'reservations: conflict')
        self.assert_single_error(
            [booking('a', start=0, end=3), booking('b', start=2, end=4),
             booking('a', resource='desk')],
            ValueError, 'reservations: conflict')

    def test_all_fields_checked_before_domain(self):
        for prefix in ([booking(), booking()],
                       [booking('a', start=0, end=3), booking('b', start=2, end=4)]):
            self.assert_single_error(prefix + [booking(end=True)],
                                     ValueError, 'reservations: invalid row')

    def test_invalid_rows(self):
        invalid = [None, [], {}, {**booking(), 'extra': 0},
                   {key: value for key, value in booking().items() if key != 'id'}]
        for key, values in {'id': [None, 3, '', '  '],
                            'resource': [None, 3, '', '\t'],
                            'start': [True, False, 1.0, '1', -1],
                            'end': [True, False, 2.0, '2', 0, 1]}.items():
            for value in values:
                invalid.append({**booking(), key: value})
        for row in invalid:
            with self.subTest(row=row):
                self.assert_single_error([row], ValueError, 'reservations: invalid row')
                with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                    validate([row])

    def test_input_types_and_subclasses(self):
        for rows in (None, {}, (), 'rows', iter([])):
            self.assert_single_error(rows, TypeError, 'reservations: rows must be a list')
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                validate(rows)
        for batches in (None, {}, (), 'batches', iter([])):
            for call in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                    call(batches)

        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(booking(start=Integer(1)))])
        self.assertEqual(run(rows)['bookings'], [booking()])
        self.assertEqual(run_many(Rows([rows])), [run(rows)])

    def test_unicode_canonicalization_and_rendering(self):
        rows = [booking(' STRAẞE ', ' Ä\"\n室 ', 0, 2)]
        expected = {'bookings': [booking('strasse', 'ä\"\n室', 0, 2)],
                    'resources': ['ä\"\n室']}
        self.assertEqual(normalize(' STRAẞE '), 'strasse')
        self.assertEqual(validate(rows), expected['bookings'])
        self.assertEqual(compute(rows), expected)
        self.assertEqual(run(rows), expected)
        serialized = '{"bookings":[{"end":2,"id":"strasse","resource":"ä\\\"\\n室","start":0}],"resources":["ä\\\"\\n室"]}\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(json.loads(serialized), expected)
        self.assertEqual(list(run(rows)), ['bookings', 'resources'])

    def test_batch_order_and_empty_results(self):
        batches = [[booking('z', 'z')], [], [booking('a', 'a')]]
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(render([]), '{"bookings":[],"resources":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_input_and_result_isolation(self):
        rows = [booking(' A ', ' ROOM ', 0, 1), booking('b', start=1, end=2)]
        original = copy.deepcopy(rows)
        expected = run(rows)
        for call in (run, compute, validate, render):
            call(rows)
            self.assertEqual(rows, original)
        results = run_many([rows, rows])
        results[0]['bookings'][0]['end'] = 99
        results[0]['bookings'].append(booking())
        results[0]['resources'].append('other')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        invalid = rows + [booking('a')]
        before = copy.deepcopy(invalid)
        self.assert_single_error(invalid, ValueError, 'reservations: duplicate id')
        for call in (run_many, render_many):
            with self.assertRaises(ValueError):
                call([rows, invalid])
            self.assertEqual(rows, original)
            self.assertEqual(invalid, before)
        self.assertEqual(run_many([rows]), [expected])


if __name__ == '__main__':
    unittest.main()
