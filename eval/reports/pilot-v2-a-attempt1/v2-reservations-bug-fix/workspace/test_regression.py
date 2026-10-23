import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def booking(id='b1', resource='room', start=1, end=2):
    return dict(id=id, resource=resource, start=start, end=end)


class RegressionTests(unittest.TestCase):
    def assert_single_error(self, rows, error, message):
        for entry in (run, compute, validate, render):
            # validate handles field validation; domain checks belong to compute.
            if entry is validate and message != 'reservations: invalid row' and error is not TypeError:
                continue
            with self.subTest(entry=entry.__name__):
                with self.assertRaises(error) as caught:
                    entry(rows)
                self.assertEqual(str(caught.exception), message)

    def test_domain_edge(self):
        rows = [booking(' B ', ' ROOM ', 2, 3), booking('A', 'room', 1, 2)]
        expected = dict(bookings=[booking('a'), booking('b', start=2, end=3)], resources=['room'])
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(render_many([rows]), render(rows))

    def test_unicode_canonicalization(self):
        self.assertEqual(normalize(' Straße '), 'strasse')
        self.assert_single_error([booking(' Straße '), booking('STRASSE', 'other')],
                                 ValueError, 'reservations: duplicate id')
        self.assert_single_error([booking('a', ' Straße '), booking('b', 'STRASSE')],
                                 ValueError, 'reservations: conflict')
        self.assertEqual(len(run([booking('a', 'one'), booking('b', 'two')])['bookings']), 2)

    def test_domain_error_order(self):
        self.assert_single_error([booking('a'), booking(' A ')],
                                 ValueError, 'reservations: duplicate id')
        # Domain checks follow input order: an earlier conflict wins over a later duplicate.
        self.assert_single_error([booking('a'), booking('b'), booking('a')],
                                 ValueError, 'reservations: conflict')

    def test_all_fields_validated_before_domain_checks(self):
        for prefix in ([booking('a'), booking('b')], [booking('a'), booking('a')]):
            rows = prefix + [booking('bad', start=True)]
            self.assert_single_error(rows, ValueError, 'reservations: invalid row')

    def test_invalid_rows(self):
        for rows in (None, (), {}, '', iter([])):
            self.assert_single_error(rows, TypeError, 'reservations: rows must be a list')
        invalid = [None, [], {}, {**booking(), 'extra': 1}]
        for key in booking():
            row = booking()
            del row[key]
            invalid.append(row)
        for key in ('id', 'resource'):
            for value in (None, 1, True, '', ' \t\n'):
                invalid.append({**booking(), key: value})
        for key in ('start', 'end'):
            for value in (None, True, False, 1.5, '1'):
                invalid.append({**booking(), key: value})
        invalid.extend([booking(start=-1), booking(start=2), booking(end=0)])
        for row in invalid:
            with self.subTest(row=row):
                self.assert_single_error([row], ValueError, 'reservations: invalid row')

    def test_subclasses_and_zero_boundary(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(booking(start=Integer(0), end=Integer(1)))])
        self.assertEqual(run(rows)['bookings'], [booking(start=0, end=1)])
        self.assertEqual(run_many(Rows([rows])), [run(rows)])

    def test_render_and_order(self):
        rows = [booking(' Z ', ' É ', 4, 6), booking('B', 'a', 2, 3),
                booking(' A\n"\\ ', 'A', 0, 2)]
        result = run(rows)
        self.assertEqual(result['resources'], ['a', 'é'])
        self.assertEqual([r['id'] for r in result['bookings']], ['a\n"\\', 'b', 'z'])
        self.assertEqual(list(result), ['bookings', 'resources'])
        self.assertTrue(all(list(row) == ['id', 'resource', 'start', 'end'] for row in result['bookings']))
        expected = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertIn('é', render(rows))
        self.assertEqual(render(rows).count('\n'), 1)

    def test_empty_inputs(self):
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(validate([]), [])
        self.assertEqual(render([]), '{"bookings":[],"resources":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_results_and_input_preservation(self):
        rows = [booking(' B ', ' ROOM ')]
        original = copy.deepcopy(rows)
        expected = run(rows)
        results = run_many([rows, rows])
        results[0]['bookings'][0]['id'] = 'changed'
        results[0]['bookings'].append(booking())
        results[0]['resources'].append('changed')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        self.assertIsNot(run([])['bookings'], run([])['bookings'])
        self.assertIsNot(run([])['resources'], run([])['resources'])

    def test_batch_errors_and_atomicity(self):
        for entry in (run_many, render_many):
            for batches in (None, (), {}, ''):
                with self.assertRaises(TypeError) as caught:
                    entry(batches)
                self.assertEqual(str(caught.exception), 'reservations: batches must be a list')
            for bad, error, message in (
                ((), TypeError, 'reservations: rows must be a list'),
                ([{}], ValueError, 'reservations: invalid row'),
                ([booking('a'), booking(' A ')], ValueError, 'reservations: duplicate id'),
                ([booking('a'), booking('b')], ValueError, 'reservations: conflict'),
                ([booking('a'), booking('b'), {}], ValueError, 'reservations: invalid row'),
            ):
                batches = [[booking(' Good ', ' ROOM ')], bad]
                original = copy.deepcopy(batches)
                with self.assertRaises(error) as caught:
                    entry(batches)
                self.assertEqual(str(caught.exception), message)
                self.assertEqual(batches, original)
        batches = [[booking('a')], [], [booking(' A ')]]
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))


if __name__ == '__main__':
    unittest.main()
