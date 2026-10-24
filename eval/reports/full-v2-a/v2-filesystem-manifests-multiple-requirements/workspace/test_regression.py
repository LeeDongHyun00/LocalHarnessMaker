import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Dir/Straße ', 'target': ' OLD ', 'value': -5},
            {'id': 'z', 'target': 'z', 'value': 10},
            {'id': 'dir/STRASSE', 'target': ' New ', 'value': 2},
            {'id': 'Z', 'target': 'Last', 'value': 1},
        ]
        expected = {'files': {
            'dir/strasse': {'digest': 'new', 'size': 2},
            'z': {'digest': 'last', 'size': 1},
        }, 'bytes': 3}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'files': {}, 'bytes': 0}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        with self.assertRaisesRegex(ValueError, '^filesystem-manifests: invalid path$'):
            run([{'id': 'a/../b', 'target': 'hash', 'value': 1}])

    def test_structural_validation_and_canonical_rows(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(id=Text(' Ä /File '), target=Text(' HASH '), value=10**100)])
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'ä /file', 'target': 'hash', 'value': 10**100}])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(run(rows)['bytes'], 10**100)
        self.assertEqual(rows, before)
        self.assertEqual(policy.normalize(' Straße / A B '), 'strasse / a b')
        invalid_rows = [None, {}, {'id': 'x', 'target': 'h', 'value': 1, 'extra': 2}]
        for field, values in (
            ('id', ['', '  ', 1]), ('target', ['', '\t', None]),
            ('value', [True, Integer(1), 1.0, '1']),
        ):
            for value in values:
                row = {'id': 'x', 'target': 'h', 'value': 1}
                row[field] = value
                invalid_rows.append(row)
        for row in invalid_rows:
            with self.subTest(row=row):
                data = [{'id': '/bad', 'target': 'h', 'value': -1}, row]
                snapshot = copy.deepcopy(data)
                with self.assertRaisesRegex(ValueError, '^filesystem-manifests: invalid row$'):
                    run(data)
                self.assertEqual(data, snapshot)
        self.assertEqual(validation.validate([
            {'id': '/BAD', 'target': 'H', 'value': -1},
            {'id': '/bad', 'target': 'J', 'value': 2},
        ]), [
            {'id': '/bad', 'target': 'h', 'value': -1},
            {'id': '/bad', 'target': 'j', 'value': 2},
        ])
        for api in (run, render, engine.compute, validation.validate):
            with self.assertRaisesRegex(TypeError, '^filesystem-manifests: rows must be a list$'):
                api(())

    def test_paths_and_domain_error_order(self) -> None:
        for path in ('/a', 'a/', 'a//b', '.', '..', 'a/./b', 'a/../b'):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, '^filesystem-manifests: invalid path$'):
                    run([{'id': path, 'target': 'h', 'value': -1}])
        with self.assertRaisesRegex(ValueError, '^filesystem-manifests: invalid path$'):
            run([{'id': 'a', 'target': 'h', 'value': -1},
                 {'id': '/b', 'target': 'h', 'value': 1}])
        with self.assertRaisesRegex(ValueError, '^filesystem-manifests: negative size$'):
            run([{'id': 'ok', 'target': 'h', 'value': -1}])
        self.assertIn('a\\..\\b', run([
            {'id': 'a\\..\\b', 'target': 'h', 'value': 0},
        ])['files'])

    def test_serialization_order_and_independence(self) -> None:
        rows = [{'id': ' Z ', 'target': ' É ', 'value': 4},
                {'id': 'a', 'target': 'h', 'value': 1}]
        snapshot = copy.deepcopy(rows)
        result = run(rows)
        self.assertEqual(list(result), ['files', 'bytes'])
        self.assertEqual(list(result['files']), ['a', 'z'])
        self.assertEqual(list(result['files']['a']), ['digest', 'size'])
        serialized = render(rows)
        self.assertEqual(serialized, json.dumps(result, ensure_ascii=False, sort_keys=True,
                                               separators=(',', ':')) + '\n')
        outputs = run_many([rows, rows])
        outputs[0]['files']['z']['digest'] = 'changed'
        outputs[0]['files']['extra'] = {}
        self.assertEqual(outputs[1], result)
        self.assertEqual(run(rows), result)
        self.assertEqual(rows, snapshot)
        self.assertEqual(run([]), {'files': {}, 'bytes': 0})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_batch_atomicity_and_dynamic_engine(self) -> None:
        valid = [{'id': 'x', 'target': 'h', 'value': 1}]
        bad = [{'id': 'x', 'target': 'h', 'value': -1}]
        later = [{'id': None, 'target': 'h', 'value': 1}]
        for api in (run, render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(valid)
                self.assertEqual(compute.call_count, 1)
                self.assertIs(compute.call_args.args[0], valid)
        for api in (run_many, render_many):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api([valid, valid])
                    self.assertEqual(compute.call_count, 2)
                batches = [valid, bad, later]
                snapshot = copy.deepcopy(batches)
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex(ValueError, '^filesystem-manifests: negative size$'):
                        api(batches)
                    self.assertEqual(compute.call_count, 2)
                self.assertEqual(batches, snapshot)
                with self.assertRaisesRegex(TypeError, '^filesystem-manifests: batches must be a list$'):
                    api(())


if __name__ == '__main__':
    unittest.main()
