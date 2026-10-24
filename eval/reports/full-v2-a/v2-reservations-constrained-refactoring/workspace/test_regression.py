import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project.engine import compute
from project.validation import validate


def booking(identifier='b1', resource='room', start=1, end=2):
    return dict(id=identifier, resource=resource, start=start, end=end)


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [booking('B2', ' ROOM ', 2, 3), booking(' B1 ', 'Room')]
        self.assertEqual(run(rows), {
            'bookings': [booking(), booking('b2', start=2, end=3)],
            'resources': ['room'],
        })
        with self.assertRaisesRegex(ValueError, '^reservations: conflict$'):
            run([booking(end=3), booking('b2', start=2, end=4)])
        self.assertEqual(len(run([booking(), booking('b2', 'other')])['bookings']), 2)

    def test_runtime_normalization(self):
        rows = [booking(' B1 ', ' ROOM ')]
        expected = {'bookings': [booking('patched:b1', 'patched:room')],
                    'resources': ['patched:room']}
        for api in (run, render, run_many, render_many, compute, validate):
            with self.subTest(api=api.__name__), patch(
                'project.policy.normalize', side_effect=lambda value: 'patched:' + value.strip().casefold()
            ) as normalize:
                actual = api([rows] if api in (run_many, render_many) else rows)
                if api in (render, render_many):
                    actual = json.loads(actual)
                elif api is run_many:
                    actual = actual[0]
                elif api is validate:
                    actual = {'bookings': actual, 'resources': ['patched:room']}
                self.assertEqual(actual, expected)
                self.assertEqual(normalize.call_count, 2)

    def test_validation_precedes_domain_errors(self):
        for domain_rows in ([booking(), booking(' B1 ')],
                            [booking(end=4), booking('b2', start=2, end=3)]):
            with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                run(domain_rows + [booking(start=True)])
        with self.assertRaisesRegex(ValueError, '^reservations: duplicate id$'):
            run([booking(end=4), booking(' B1 ', start=2, end=3)])

    def test_input_validation(self):
        for api in (run, render, compute, validate):
            with self.subTest(api=api.__name__), self.assertRaisesRegex(
                TypeError, '^reservations: rows must be a list$'
            ):
                api(())
        invalid = [None, {}, dict(booking(), extra=1), booking(identifier=' '),
                   booking(resource=3), booking(start=False), booking(end=2.0),
                   booking(start=-1), booking(start=2), booking(end=0)]
        for row in invalid:
            with self.subTest(row=row), self.assertRaisesRegex(
                ValueError, '^reservations: invalid row$'
            ):
                run([row])
        class Rows(list):
            pass
        class Row(dict):
            pass
        class Integer(int):
            pass
        self.assertEqual(run(Rows([Row(booking(start=Integer(1)))])), run([booking()]))

    def test_fresh_results_and_atomic_batches(self):
        rows = [booking(' B1 ', ' ROOM ')]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['bookings'][0]['id'] = 'changed'
        results[0]['resources'].append('changed')
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, original)
        for api in (run_many, render_many):
            batches = [rows, [booking(), booking()]]
            before = copy.deepcopy(batches)
            with self.assertRaisesRegex(ValueError, '^reservations: duplicate id$'):
                api(batches)
            self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                api(())
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                api([rows, ()])

    def test_rendering_and_empty_batches(self):
        rows = [booking(' Ä"\\\n ', ' Ü ')]
        expected = json.dumps(run(rows), ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render_many([rows, []]), expected + render([]))
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
