import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def booking(identifier='a', resource='room', start=0, end=2):
    return dict(id=identifier, resource=resource, start=start, end=end)


class TestCase(unittest.TestCase):
    def test_domain_edge(self):
        rows = [booking(' B ', ' ROOM ', 2, 4), booking('A')]
        self.assertEqual(run(rows), {
            'bookings': [booking('a'), booking('b', start=2, end=4)],
            'resources': ['room'],
        })

    def test_domain_errors(self):
        for rows, message in [
            ([booking(), booking(' A ')], 'duplicate id'),
            ([booking(), booking('b', ' ROOM ')], 'conflict'),
        ]:
            for entry in (run, compute, render):
                with self.subTest(entry=entry, message=message):
                    with self.assertRaisesRegex(ValueError, '^reservations: ' + message + '$'):
                        entry(rows)
        self.assertEqual(run([booking(), booking('b', 'other')])['resources'], ['other', 'room'])

    def test_validation_precedes_domain(self):
        for second in (booking(' A '), booking('b')):
            rows = [booking(), second, booking('c', end=False)]
            for entry in (run, compute, render):
                with self.subTest(entry=entry, second=second):
                    with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                        entry(rows)

    def test_invalid_inputs(self):
        for entry in (run, compute, validate, render):
            for rows in (None, (), {}, 'rows', iter([])):
                with self.subTest(entry=entry, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                        entry(rows)
            invalid = [None, [], {}, dict(booking(), extra=1)]
            for field, values in {
                'id': ['', '  ', 1, None],
                'resource': ['', '\t', False, None],
                'start': [True, 0.0, '0', -1, 2],
                'end': [False, 2.0, '2', 0, -1],
            }.items():
                for value in values:
                    invalid.append(dict(booking(), **{field: value}))
            for row in invalid:
                with self.subTest(entry=entry, row=row):
                    with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                        entry([row])

    def test_subclasses_and_normalization(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        self.assertEqual(normalize(' Straße '), 'strasse')
        self.assertEqual(validate(Rows([Row(booking(' A ', ' ROOM ', Integer(0)))])), [booking()])

    def test_immutability_and_fresh_results(self):
        rows = [booking(' A ', ' ROOM ')]
        original = copy.deepcopy(rows)
        for entry in (run, compute, validate):
            result = entry(rows)
            bookings = result if isinstance(result, list) else result['bookings']
            self.assertIsNot(bookings[0], rows[0])
            bookings[0]['id'] = 'changed'
            bookings.clear()
            if isinstance(result, dict):
                result['resources'].append('changed')
            self.assertEqual(rows, original)
            self.assertEqual(run(rows)['bookings'], [booking()])
        for bad_row in (booking('a'), booking('b'), {}):
            failing = rows + [bad_row]
            before = copy.deepcopy(failing)
            with self.assertRaises(ValueError):
                run(failing)
            self.assertEqual(failing, before)

    def test_render_and_empty(self):
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(list(run([])), ['bookings', 'resources'])
        self.assertEqual(render([]), '{"bookings":[],"resources":[]}\n')
        self.assertEqual(render([booking(' É"\nA ', ' 방 ')]),
                         '{"bookings":[{"end":2,"id":"é\\\"\\na","resource":"방","start":0}],"resources":["방"]}\n')

    def test_batch_empty(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_batch_outer_types(self):
        for entry in (run_many, render_many):
            for batches in (None, (), {}, 'batches', iter([]), 1):
                with self.subTest(entry=entry, batches=batches):
                    with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                        entry(batches)

    def test_batch_order_and_render(self):
        batches = [[booking(' Z ', ' OTHER ', 4, 6), booking('a')],
                   [], [booking(' É"\nA ', ' 방 ')], [booking('a')]]
        before = copy.deepcopy(batches)
        results = run_many(batches)
        self.assertEqual(results, [run(rows) for rows in batches])
        for result in results:
            self.assertEqual(list(result), ['bookings', 'resources'])
        rendered = render_many(batches)
        self.assertEqual(rendered, ''.join(render(rows) for rows in batches))
        self.assertTrue(rendered.endswith('\n'))
        self.assertEqual(batches, before)

    def test_batch_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        batches = Rows([Rows([Row(booking(' A ', ' ROOM '))])])
        self.assertEqual(run_many(batches), [run([booking()])])
        self.assertEqual(render_many(batches), render([booking()]))

    def test_batch_member_errors_and_immutability(self):
        cases = [
            (None, TypeError, 'rows must be a list'),
            ((), TypeError, 'rows must be a list'),
            ([{}], ValueError, 'invalid row'),
            ([booking(end=True)], ValueError, 'invalid row'),
            ([booking(), booking(' A ')], ValueError, 'duplicate id'),
            ([booking(), booking('b', ' ROOM ')], ValueError, 'conflict'),
            ([booking(), booking(' A '), {}], ValueError, 'invalid row'),
            ([booking(), booking('b'), booking(' A ')], ValueError, 'conflict'),
        ]
        for entry in (run_many, render_many):
            for bad, error, message in cases:
                for position in range(3):
                    batches = [[booking(' Good ', ' OTHER ')] for _ in range(2)]
                    batches.insert(position, bad)
                    before = copy.deepcopy(batches)
                    with self.subTest(entry=entry, message=message, position=position):
                        with self.assertRaisesRegex(error, '^reservations: ' + message + '$'):
                            entry(batches)
                        self.assertEqual(batches, before)

    def test_batch_errors_follow_member_order(self):
        batches = [[booking(), booking(' A ')], [{}]]
        for entry in (run_many, render_many):
            with self.subTest(entry=entry):
                with self.assertRaisesRegex(ValueError, '^reservations: duplicate id$'):
                    entry(batches)

    def test_batch_results_are_independent(self):
        rows = [booking(' A ', ' ROOM ')]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        result = run_many(batches)
        later = run_many(batches)
        result[0]['bookings'][0]['id'] = 'changed'
        result[0]['bookings'].clear()
        result[0]['resources'].append('changed')
        result[2]['bookings'].append(booking())
        result[2]['resources'].append('changed')
        self.assertEqual(result[1], run(rows))
        self.assertEqual(result[3], run([]))
        self.assertEqual(later, [run(member) for member in batches])
        self.assertEqual(run_many(batches), later)
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
