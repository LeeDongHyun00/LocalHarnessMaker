import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.validation import validate


def booking(identifier='b1', resource='room', start=1, end=2):
    return dict(id=identifier, resource=resource, start=start, end=end)


class RegressionTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [booking(' B2 ', ' ROOM ', 2, 3), booking('B1'),
                booking('b3', 'other', 1, 3)]
        expected = {'bookings': [booking('b3', 'other', 1, 3),
                                 booking('b1'), booking('b2', 'room', 2, 3)],
                    'resources': ['other', 'room']}
        self.assertEqual(run_many([[], rows]),
                         [{'bookings': [], 'resources': []}, expected])
        self.assertEqual(render_many([[], rows]), render([]) + render(rows))

    def test_batch_errors_and_precedence(self):
        for api in (run_many, render_many):
            for outer in (None, {}, (), 'rows'):
                with self.subTest(api=api.__name__, outer=outer):
                    with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                        api(outer)
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                api([[], ()])
            conflict = [booking(), booking('b2', start=1, end=3)]
            with self.assertRaisesRegex(ValueError, '^reservations: conflict$'):
                api([[], conflict])
            with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                api([[], conflict + [booking('bad', start=True)]])
            with self.assertRaisesRegex(ValueError, '^reservations: duplicate id$'):
                api([[booking(' Straße '), booking('STRASSE')]])

    def test_fresh_results_and_unchanged_inputs(self):
        rows = [booking(' B1 ', ' ROOM ')]
        batches = [rows, rows]
        original = copy.deepcopy(batches)
        result = run_many(batches)
        result[0]['bookings'][0]['id'] = 'changed'
        result[0]['resources'].append('changed')
        result[0]['bookings'].append({})
        self.assertEqual(result[1], run(rows))
        self.assertEqual(batches, original)
        self.assertEqual(run_many(batches), [run(rows), run(rows)])
        failed = [rows, [booking(), booking('b2')]]
        original_failed = copy.deepcopy(failed)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^reservations: conflict$'):
                api(failed)
            self.assertEqual(failed, original_failed)

    def test_row_validation(self):
        invalid = [None, [], {}, dict(booking(), extra=1),
                   {key: value for key, value in booking().items() if key != 'end'},
                   booking(identifier=' '), booking(resource='\t'),
                   booking(identifier=1), booking(resource=None),
                   booking(start=True), booking(end=False), booking(start=1.0),
                   booking(end='2'), booking(start=-1), booking(start=2),
                   booking(start=3)]
        for api in (run, compute, render, validate):
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                api(())
            for row in invalid:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                        api([row])

    def test_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(booking(start=Integer(1)))])
        self.assertEqual(run_many(Rows([rows])), [run([booking()])])

    def test_unicode_rendering(self):
        rows = [booking(' Straße ', ' 방"\n이름 ', 0, 1)]
        expected = {'bookings': [booking('strasse', '방"\n이름', 0, 1)],
                    'resources': ['방"\n이름']}
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)), ['bookings', 'resources'])
        self.assertEqual(list(run(rows)['bookings'][0]), ['id', 'resource', 'start', 'end'])
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows, rows]), serialized * 2)


if __name__ == '__main__':
    unittest.main()
