import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def booking(id='b1', resource='room', start=1, end=2):
    return {'id': id, 'resource': resource, 'start': start, 'end': end}


class RegressionTests(unittest.TestCase):
    def assert_error(self, kind, message, function, value):
        with self.assertRaises(kind) as caught:
            function(value)
        self.assertEqual(str(caught.exception), message)

    def test_domain_edge(self):
        rows = [booking('last', ' ROOM ', 3, 4),
                booking(' FIRST ', 'room', 1, 2),
                booking('middle', 'Room', 2, 3),
                booking('other', 'desk', 1, 4)]
        self.assertEqual(run(rows), {
            'bookings': [booking('other', 'desk', 1, 4),
                         booking('first', 'room', 1, 4)],
            'resources': ['desk', 'room']})

    def test_canonicalization_across_entry_points(self):
        rows = [booking(' Straße ', ' ÉTAGE ')]
        expected = {'bookings': [booking('strasse', 'étage')],
                    'resources': ['étage']}
        self.assertEqual(normalize(' Straße '), 'strasse')
        self.assertEqual(validate(rows), expected['bookings'])
        self.assertEqual(compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(json.loads(render(rows)), expected)
        self.assertEqual(render_many([rows]), render(rows))

    def test_shape_and_fields(self):
        invalid_rows = [None, [], {}, dict(booking(), extra=1),
                        {k: v for k, v in booking().items() if k != 'id'}]
        for key, values in [('id', ['', ' \t', None, 1]),
                            ('resource', ['', ' ', None, 1]),
                            ('start', [True, None, 1.0, '1', -1, 2]),
                            ('end', [False, None, 2.0, '2', 0, 1])]:
            for value in values:
                row = booking()
                row[key] = value
                invalid_rows.append(row)
        for function in (validate, compute, run, render):
            for value in (None, (), {}, 'rows'):
                self.assert_error(TypeError, 'reservations: rows must be a list',
                                  function, value)
            for row in invalid_rows:
                with self.subTest(function=function.__name__, row=row):
                    self.assert_error(ValueError, 'reservations: invalid row',
                                      function, [row])

    def test_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(booking(start=Integer(1)))])
        self.assertEqual(run(rows)['bookings'], [booking()])
        self.assertEqual(run_many(Rows([rows])), [run(rows)])

    def test_error_precedence(self):
        conflict = [booking('a', start=0, end=3),
                    booking('b', start=1, end=2)]
        duplicate = [booking('a'), booking(' A ', start=2, end=3)]
        for function in (run, compute, render,
                         lambda rows: run_many([[], rows]),
                         lambda rows: render_many([[], rows])):
            for rows in (conflict, duplicate):
                self.assert_error(ValueError, 'reservations: invalid row',
                                  function, rows + [{}])
            self.assert_error(ValueError, 'reservations: conflict',
                              function, conflict)
            self.assert_error(ValueError, 'reservations: duplicate id',
                              function, [booking(' A '), booking('a')])
            self.assert_error(ValueError, 'reservations: duplicate id',
                              function, duplicate + [booking('a', 'desk')])
            # Domain errors follow original row order, before any sorting.
            self.assert_error(ValueError, 'reservations: conflict',
                              function, conflict + [booking('a', 'desk')])

    def test_render_format(self):
        rows = [booking('É"\n', ' ROOM\\ ')]
        self.assertEqual(render(rows),
                         '{"bookings":[{"end":2,"id":"é\\"","resource":"room\\\\",'
                         '"start":1}],"resources":["room\\\\"]}\n')
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_empty_and_batch_shapes(self):
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(list(run([])), ['bookings', 'resources'])
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for function in (run_many, render_many):
            for value in (None, (), {}, 'batches'):
                self.assert_error(TypeError, 'reservations: batches must be a list',
                                  function, value)
            self.assert_error(TypeError, 'reservations: rows must be a list',
                              function, [[], ()])

    def test_no_mutation_or_shared_results(self):
        rows = [booking(' B1 ', ' ROOM ')]
        before = copy.deepcopy(rows)
        batches = [rows, rows]
        results = run_many(batches)
        results[0]['bookings'][0]['id'] = 'changed'
        results[0]['bookings'].append(booking('added'))
        results[0]['resources'].append('changed')
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, before)
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        for bad in ([booking('x'), booking(' X ')],
                    [booking('x'), booking('y'), {}]):
            snapshot = copy.deepcopy(bad)
            for function in (run, render, lambda value: run_many([rows, value]),
                             lambda value: render_many([rows, value])):
                with self.assertRaises(ValueError):
                    function(bad)
                self.assertEqual(bad, snapshot)
                self.assertEqual(rows, before)


if __name__ == '__main__':
    unittest.main()
