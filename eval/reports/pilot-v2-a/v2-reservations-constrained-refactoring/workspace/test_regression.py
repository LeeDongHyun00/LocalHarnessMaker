import copy
import json
import unittest
from unittest.mock import patch

from project import run, render, run_many, render_many
from project.engine import compute
from project.validation import validate
from project import policy


def booking(id='a', resource='room', start=0, end=2):
    return dict(id=id, resource=resource, start=start, end=end)


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [booking('b', start=2, end=4), booking('a')]
        self.assertEqual([row['id'] for row in run(rows)['bookings']], ['a', 'b'])
        self.assertEqual(len(run([booking(), booking('b', 'other')])['bookings']), 2)
        with self.assertRaisesRegex(ValueError, '^reservations: conflict$'):
            run([booking(), booking('b', start=1, end=3)])
        with self.assertRaisesRegex(ValueError, '^reservations: duplicate id$'):
            run([booking(' A '), booking('a')])

    def test_runtime_normalization(self):
        rows = [booking(' A ', ' ROOM ')]
        expected = {'bookings': [booking('patched:a', 'patched:room')],
                    'resources': ['patched:room']}
        original = policy.normalize
        for entry in (run, render, run_many, render_many, compute, validate):
            with self.subTest(entry=entry.__name__):
                with patch.object(policy, 'normalize', side_effect=lambda s: 'patched:' + original(s)) as mock:
                    result = entry([rows] if entry in (run_many, render_many) else rows)
                    if entry in (render, render_many):
                        result = json.loads(result)
                    elif entry is run_many:
                        result = result[0]
                    elif entry is validate:
                        result = {'bookings': result, 'resources': ['patched:room']}
                    self.assertEqual(result, expected)
                    self.assertEqual(mock.call_args_list, [unittest.mock.call(' A '), unittest.mock.call(' ROOM ')])
        self.assertEqual(policy.normalize(' STRAẞE '), 'strasse')

    def test_invalid_rows_precede_domain_errors(self):
        for domain_rows in ([booking(), booking()],
                            [booking(), booking('b')]):
            for entry in (run, render, run_many, render_many):
                rows = domain_rows + [booking('bad', end=True)]
                with self.subTest(entry=entry.__name__, rows=rows):
                    with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                        entry([rows] if entry in (run_many, render_many) else rows)

    def test_input_validation(self):
        for rows in (None, (), {}, 'rows'):
            for entry in (run, render, compute, validate):
                with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                    entry(rows)
        invalid = [None, [], {}, dict(booking(), extra=1),
                   {k: v for k, v in booking().items() if k != 'end'},
                   booking(id=' '), booking(resource='\t'), booking(id=1),
                   booking(resource=None), booking(start=True), booking(end=False),
                   booking(start=0.0), booking(end='2'), booking(start=-1),
                   booking(start=2), booking(end=0)]
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^reservations: invalid row$'):
                    run([row])
        class Rows(list):
            pass
        class Row(dict):
            pass
        class Number(int):
            pass
        self.assertEqual(run(Rows([Row(booking(start=Number(0)))])), run([booking()]))

    def test_render_and_ordering(self):
        rows = [booking('Z', ' Ä ', 2, 4), booking('B', 'a'), booking('A', 'Ä')]
        expected = {'bookings': [booking('b', 'a'), booking('a', 'ä'), booking('z', 'ä', 2, 4)],
                    'resources': ['a', 'ä']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)), ['bookings', 'resources'])
        self.assertEqual(render(rows), json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
        escaped = [booking('Quote"\n\\', '방')]
        self.assertEqual(json.loads(render(escaped)), run(escaped))

    def test_batches_and_fresh_results(self):
        rows = [booking(' A ', ' ROOM ')]
        batches = [rows, rows]
        snapshot = copy.deepcopy(batches)
        results = run_many(batches)
        self.assertEqual(results, [run(rows), run(rows)])
        self.assertEqual(render_many(batches), render(rows) * 2)
        results[0]['bookings'][0]['id'] = 'changed'
        results[0]['resources'].append('changed')
        results[0]['bookings'].append({})
        self.assertEqual(results[1], run(rows))
        self.assertEqual(batches, snapshot)
        for bad in ([booking(), booking('b')], [booking(end=False)]):
            failing = [rows, bad]
            before = copy.deepcopy(failing)
            for entry in (run_many, render_many):
                with self.assertRaises(ValueError):
                    entry(failing)
                self.assertEqual(failing, before)
        for entry in (run_many, render_many):
            for outer in (None, (), {}):
                with self.assertRaisesRegex(TypeError, '^reservations: batches must be a list$'):
                    entry(outer)
            with self.assertRaisesRegex(TypeError, '^reservations: rows must be a list$'):
                entry([rows, None])
        self.assertEqual(run([]), {'bookings': [], 'resources': []})
        self.assertEqual(render([]), '{"bookings":[],"resources":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
