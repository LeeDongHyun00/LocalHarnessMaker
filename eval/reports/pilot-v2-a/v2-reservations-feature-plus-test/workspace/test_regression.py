import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.validation import validate


def booking(id='b1', resource='room', start=1, end=2):
    return dict(id=id, resource=resource, start=start, end=end)


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

    def test_domain_errors_and_field_precedence(self):
        cases = [
            ([booking(), booking(' B1 ')], 'duplicate id'),
            ([booking(), booking('b2')], 'conflict'),
            ([booking(), booking('b2'), booking(end=True)], 'invalid row'),
            ([booking(), booking('b2'), {}], 'invalid row'),
            ([booking(), booking('b2'), booking(' B1 ')], 'conflict'),
        ]
        for rows, error in cases:
            before = copy.deepcopy(rows)
            for single in (run, compute, render):
                with self.subTest(api=single.__name__, error=error):
                    with self.assertRaisesRegex(ValueError, '^reservations: ' + error + '$'):
                        single(rows)
            for batch in (run_many, render_many):
                with self.subTest(api=batch.__name__, error=error):
                    with self.assertRaisesRegex(ValueError, '^reservations: ' + error + '$'):
                        batch([[booking('ok')], rows])
            self.assertEqual(rows, before)

    def test_input_shapes_and_invalid_fields(self):
        for api in (run_many, render_many):
            for outer in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                    api(outer)
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                api([[] , ()])
        invalid = [None, {}, dict(booking(), extra=1), booking(id='  '),
                   booking(resource=5), booking(start=True), booking(end=2.5),
                   booking(start=-1), booking(start=2), booking(end=0)]
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                    validate([row])
        for api in (run, render, compute, validate):
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                api(())

    def test_fresh_results_and_no_mutation(self):
        rows = [booking(' B1 ', ' ROOM ')]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['bookings'][0]['id'] = 'changed'
        results[0]['bookings'].append({})
        results[0]['resources'].append('changed')
        expected = {'bookings': [booking()], 'resources': ['room']}
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['resources'].append('changed')
        self.assertEqual(empty[1], {'bookings': [], 'resources': []})

    def test_unicode_rendering_and_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(booking(' Straße\n" ', ' CAFÉ ', Integer(0), Integer(1)))])
        expected = {'bookings': [booking('strasse\n"', 'café', 0, 1)],
                    'resources': ['café']}
        self.assertEqual(run(rows), expected)
        rendered = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), rendered)
        self.assertEqual(render_many(Rows([rows, rows])), rendered * 2)
        self.assertEqual(run_many(Rows([rows])), [expected])


if __name__ == '__main__':
    unittest.main()
