import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def booking(identifier='B1', resource=' Room ', start=1, end=2):
    return dict(id=identifier, resource=resource, start=start, end=end)


class RegressionTests(unittest.TestCase):
    def assert_error(self, function, value, error, message):
        with self.assertRaises(error) as caught:
            function(value)
        self.assertEqual(str(caught.exception), message)

    def test_domain_edge(self):
        rows = [booking(' B2 ', start=2, end=3), booking(' B1 ')]
        self.assertEqual(run(rows), {
            'bookings': [booking('b1', 'room'), booking('b2', 'room', 2, 3)],
            'resources': ['room'],
        })
        self.assertEqual(normalize(' STRAẞE '), 'strasse')
        self.assertEqual(validate([booking(' STRAẞE ')] )[0]['id'], 'strasse')

    def test_domain_errors_and_precedence(self):
        duplicate = [booking(' Straße '), booking('STRASSE')]
        conflict = [booking('a'), booking('b')]
        for function in (run, compute, render):
            self.assert_error(function, duplicate, ValueError, 'reservations: duplicate id')
            self.assert_error(function, conflict, ValueError, 'reservations: conflict')
            for rows in (duplicate, conflict):
                self.assert_error(function, rows + [{}], ValueError, 'reservations: invalid row')
        self.assertEqual(len(run([booking('a', 'one'), booking('b', 'two')])['bookings']), 2)
        # Domain checks follow input order; an earlier conflict precedes a later duplicate.
        self.assert_error(run, conflict + [booking('a')], ValueError, 'reservations: conflict')

    def test_validation(self):
        invalid = [None, [], {}, dict(booking(), extra=1),
                   {key: value for key, value in booking().items() if key != 'id'}]
        for field, values in {
            'id': ['', ' \t', None, 1], 'resource': ['', ' \n', [], False],
            'start': [True, 1.0, '1', -1, 2], 'end': [False, 2.0, None, 0, 1],
        }.items():
            invalid.extend(dict(booking(), **{field: value}) for value in values)
        for function in (run, compute, validate, render):
            for value in (None, (), {}, 'rows', iter([])):
                self.assert_error(function, value, TypeError, 'reservations: rows must be a list')
            for row in invalid:
                with self.subTest(function=function.__name__, row=row):
                    self.assert_error(function, [row], ValueError, 'reservations: invalid row')

        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(booking(start=Integer(0), end=Integer(1)))])
        self.assertEqual(run(rows)['bookings'][0]['start'], 0)

    def test_render_and_ordering(self):
        rows = [booking('Z', 'Z', 4, 5), booking('É"\n', ' Ä ', 2, 3),
                booking('a', 'z', 0, 1)]
        expected = run(rows)
        self.assertEqual([row['id'] for row in expected['bookings']], ['a', 'z', 'é"'])
        self.assertEqual(list(expected), ['bookings', 'resources'])
        rendered = render(rows)
        self.assertEqual(rendered, json.dumps(expected, ensure_ascii=False,
                                             sort_keys=True, separators=(',', ':')) + '\n')
        self.assertTrue(rendered.endswith('\n'))
        self.assertFalse(rendered.endswith('\n\n'))
        self.assertIn('ä', rendered)
        self.assertEqual(json.loads(rendered), expected)
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(render([]), '{"bookings":[],"resources":[]}\n')

    def test_fresh_results_and_inputs(self):
        rows = [booking()]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['bookings'][0]['id'] = 'changed'
        results[0]['bookings'].append({})
        results[0]['resources'].append('changed')
        self.assertEqual(rows, original)
        self.assertEqual(results[1], run(rows))
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        empty = run_many([[], []])
        empty[0]['resources'].append('changed')
        self.assertEqual(empty[1], {'bookings': [], 'resources': []})
        for failing in ([booking('a'), booking('b')], [booking(), {}],
                        [booking(), booking()]):
            before = copy.deepcopy(failing)
            for function in (run, render, validate):
                try:
                    function(failing)
                except ValueError:
                    pass
                self.assertEqual(failing, before)

    def test_batch_apis(self):
        batches = [[booking()], [], [booking(' B1 ', 'OTHER')]]
        original = copy.deepcopy(batches)
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(batches, original)
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for function in (run_many, render_many):
            for value in (None, (), {}, 'batches'):
                self.assert_error(function, value, TypeError, 'reservations: batches must be a list')
            for member, error, message in (
                (None, TypeError, 'reservations: rows must be a list'),
                ([{}], ValueError, 'reservations: invalid row'),
                ([booking(), booking()], ValueError, 'reservations: duplicate id'),
                ([booking('a'), booking('b')], ValueError, 'reservations: conflict'),
            ):
                failing = [batches[0], member, batches[2]]
                before = copy.deepcopy(failing)
                self.assert_error(function, failing, error, message)
                self.assertEqual(failing, before)
            self.assertEqual(run_many(batches), [run(rows) for rows in batches])


if __name__ == '__main__':
    unittest.main()
