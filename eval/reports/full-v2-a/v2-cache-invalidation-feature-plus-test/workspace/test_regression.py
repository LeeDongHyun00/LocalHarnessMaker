import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def row(key, target, value):
    return {'id': key, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [row(' ROOT ', 'root', 0), row('Child', ' ROOT ', 4),
                row('child', 'absent', 2), row('leaf', 'CHILD', 9),
                row('clean', 'clean', 10**100)]
        expected = {'dirty': ['child', 'leaf', 'root'], 'clean': ['clean']}
        self.assertEqual(run(rows), expected)
        # A higher priority replacement can also make the entire chain clean.
        self.assertEqual(run(rows + [row('root', 'root', 1)]),
                         {'dirty': [], 'clean': ['child', 'clean', 'leaf', 'root']})

    def test_batches_and_serialization(self) -> None:
        rows = [row(' Straße / A ', 'STRASSE / A', 0)]
        batches = [rows, [], rows]
        expected = {'dirty': ['strasse / a'], 'clean': []}
        self.assertEqual(run_many(batches), [expected, {'dirty': [], 'clean': []}, expected])
        self.assertEqual(render_many(batches), ''.join(render(r) for r in batches))
        unicode_rows = [row(' É / 中 ', 'é / 中', 1)]
        self.assertEqual(render(unicode_rows), '{"clean":["é / 中"],"dirty":[]}\n')
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False,
                                                 sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(list(run([])), ['dirty', 'clean'])

    def test_validation_is_complete_and_canonical(self) -> None:
        rows = [row(' A ', ' A ', -1), row('a', 'other', -1), {}]
        for api in (run, render, engine.compute, validation.validate):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^cache-invalidation: invalid row$'):
                    api(rows)
        rows = [row(' A ', ' B / ß ', -1), row('a', 'a', -1)]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [row('a', 'b / ss', -1), row('a', 'a', -1)])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' A / ß 中 '), 'a / ss 中')

    def test_structural_types(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        self.assertEqual(run(ListSubclass([DictSubclass(row(StringSubclass('A'), 'a', 1))])),
                         {'dirty': [], 'clean': ['a']})
        for bad in (None, (), {}, 'rows'):
            with self.assertRaisesRegex(TypeError, '^cache-invalidation: rows must be a list$'):
                run(bad)
        for bad in (None, {}, row('', 'a', 1), row('a', '  ', 1),
                    row(1, 'a', 1), row('a', None, 1), row('a', 'a', True),
                    row('a', 'a', IntSubclass(1)), row('a', 'a', 1.0),
                    dict(row('a', 'a', 1), extra=1)):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, '^cache-invalidation: invalid row$'):
                    run([bad])

    def test_priority_and_domain_error_order(self) -> None:
        cases = [
            ([row('a', 'a', 1), row('a', 'b', 1), row('a', 'a', 2)], 'ambiguous id'),
            ([row('a', 'missing', -1), row('b', 'c', 1), row('c', 'b', 1)], 'negative generation'),
            ([row('a', 'missing', 1), row('b', 'c', 1), row('c', 'b', 1)], 'missing dependency'),
            ([row('a', 'b', 0), row('b', 'a', 1)], 'cycle'),
        ]
        for rows, message in cases:
            for api in (run, render):
                with self.subTest(message=message, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^cache-invalidation: ' + message + '$'):
                        api(rows)
        self.assertEqual(run([row('a', 'a', 3), row('a', 'absent', -1), row('a', 'a', 3)]),
                         {'dirty': [], 'clean': ['a']})

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [row(' A ', 'a', 0)]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['dirty'].append('changed')
        results[0]['clean'].append('changed')
        self.assertEqual(results[1], {'dirty': ['a'], 'clean': []})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(rows, before)
        bad = [row(' A ', 'a', 0), {'id': ['nested']}]
        batches = [rows, bad]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^cache-invalidation: invalid row$'):
                api(batches)
            self.assertEqual(batches, before)

    def test_batch_errors_and_runtime_engine_lookup(self) -> None:
        for api in (run_many, render_many):
            for bad in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^cache-invalidation: batches must be a list$'):
                    api(bad)
            batches = [[row('a', 'a', -1)], None]
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^cache-invalidation: negative generation$'):
                    api(batches)
                self.assertEqual(compute.call_count, 1)
                self.assertIs(compute.call_args.args[0], batches[0])
            with self.assertRaisesRegex(TypeError, '^cache-invalidation: rows must be a list$'):
                api([[], None])
        rows = [row('a', 'a', 1)]
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)


if __name__ == '__main__':
    unittest.main()
