import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


def row(name: str, target: str, value: int) -> dict:
    return {'id': name, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [row(' Child ', ' ROOT ', 2), row('Root', 'root', 1),
                row('CHILD', 'root', 3), row('child', 'absent', 2)]
        self.assertEqual(project.run(rows), {'migrations': ['root', 'child']})
        with self.assertRaisesRegex(ValueError, '^schema-migration: version order$'):
            project.run([row('root', 'root', 2), row('child', 'root', 2)])

    def test_ambiguity_is_immediate_after_validation(self) -> None:
        rows = [row('a', 'a', 1), row(' A ', 'other', 1), row('a', 'a', 3)]
        with self.assertRaisesRegex(ValueError, '^schema-migration: ambiguous id$'):
            project.run(rows)
        self.assertEqual(project.run([row('a', 'a', 1)] * 2),
                         {'migrations': ['a']})
        for prefix in (rows, [row('a', 'missing', 0)]):
            with self.assertRaisesRegex(ValueError, '^schema-migration: invalid row$'):
                project.run(prefix + [row('bad', 'bad', True)])

    def test_domain_error_priority(self) -> None:
        cases = [
            ([row('a', 'missing', 0), row('b', 'b', 1)], 'invalid version'),
            ([row('a', 'missing', 1), row('b', 'c', 3), row('c', 'c', 4)],
             'missing predecessor'),
            ([row('a', 'b', 1), row('b', 'b', 2)], 'version order'),
        ]
        for rows, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, '^schema-migration: ' + message + '$'):
                    project.run(rows)

    def test_validation_is_fresh_and_does_not_select(self) -> None:
        rows = [row(' B ', ' Missing ', 0), row('b', 'b', -1)]
        expected = [row('b', 'missing', 0), row('b', 'b', -1)]
        result = validation.validate(rows)
        self.assertEqual(result, expected)
        self.assertEqual(list(result[0]), ['id', 'target', 'value'])
        result[0]['target'] = 'changed'
        self.assertEqual(rows[0]['target'], ' Missing ')
        self.assertEqual(validation.validate(rows), expected)

    def test_structural_types(self) -> None:
        class IntSubclass(int):
            pass

        class StringSubclass(str):
            pass

        class DictSubclass(dict):
            pass

        class ListSubclass(list):
            pass

        good = ListSubclass([DictSubclass(row(StringSubclass(' A '), 'a', 10 ** 100))])
        self.assertEqual(project.run(good), {'migrations': ['a']})
        invalid = [None, [], {}, row('', 'a', 1), row('a', '  ', 1),
                   row(1, 'a', 1), row('a', None, 1), row('a', 'a', True),
                   row('a', 'a', IntSubclass(1)), row('a', 'a', 1.0),
                   dict(row('a', 'a', 1), extra=1)]
        for item in invalid:
            with self.subTest(item=item):
                with self.assertRaisesRegex(ValueError, '^schema-migration: invalid row$'):
                    validation.validate([item])
        for value in (None, (), {}, 'rows'):
            with self.assertRaisesRegex(TypeError, '^schema-migration: rows must be a list$'):
                project.run(value)

    def test_normalization_and_order_through_public_paths(self) -> None:
        rows = [row(' Z / Straße ', 'Z / STRASSE', 2),
                row(' Ω  / A ', 'Ω  / A', 1), row(' A ', 'a', 1)]
        expected = {'migrations': ['a', 'ω  / a', 'z / strasse']}
        self.assertEqual(policy.normalize(' Z / Straße '), 'z / strasse')
        self.assertEqual(validation.validate(rows)[0]['id'], 'z / strasse')
        for call in (project.run, engine.compute):
            self.assertEqual(call(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, {'migrations': []}])
        rendered = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(project.render(rows), rendered)
        self.assertEqual(project.render_many([rows, []]), rendered + '{"migrations":[]}\n')

    def test_empty_and_outer_types(self) -> None:
        self.assertEqual(project.run([]), {'migrations': []})
        self.assertEqual(project.render([]), '{"migrations":[]}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        for call in (project.run_many, project.render_many):
            for value in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^schema-migration: batches must be a list$'):
                    call(value)

    def test_outputs_and_inputs_are_independent(self) -> None:
        rows = [row('a', 'a', 1)]
        batches = [rows, rows]
        before = copy.deepcopy(batches)
        result = project.run_many(batches)
        self.assertIsNot(result[0], result[1])
        result[0]['migrations'].append('changed')
        self.assertEqual(result[1], {'migrations': ['a']})
        self.assertEqual(project.run(rows), {'migrations': ['a']})
        self.assertEqual(batches, before)

    def test_batch_failure_is_sequential_and_leaves_inputs_unchanged(self) -> None:
        good = [row('a', 'a', 1)]
        failures = [([row('a', 'missing', 0)], ValueError,
                     'schema-migration: invalid version'),
                    ([dict(row('a', 'a', 1), nested={'items': [1]})], ValueError,
                     'schema-migration: invalid row'),
                    ((), TypeError, 'schema-migration: rows must be a list')]
        for call in (project.run_many, project.render_many):
            for bad, error, message in failures:
                batches = [good, bad, [None]]
                before = copy.deepcopy(batches)
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex(error, '^' + message + '$'):
                        call(batches)
                    self.assertEqual(compute.call_count, 2)
                    self.assertIs(compute.call_args_list[0].args[0], good)
                    self.assertIs(compute.call_args_list[1].args[0], bad)
                self.assertEqual(batches, before)

    def test_all_facades_resolve_compute_at_call_time(self) -> None:
        rows = [row('a', 'a', 1)]
        for call, argument, count in (
                (project.run, rows, 1), (project.render, rows, 1),
                (project.run_many, [rows, rows], 2),
                (project.render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                call(argument)
                self.assertEqual(compute.call_count, count)
        payload = {'z': [{'β': 1, 'a': 2}], 'a': {}}
        expected = '{"a":{},"z":[{"a":2,"β":1}]}\n'
        with patch.object(engine, 'compute', return_value=payload):
            self.assertEqual(project.run(rows), payload)
            self.assertEqual(project.render(rows), expected)
            self.assertEqual(project.render_many([rows, rows]), expected * 2)

    def test_facades_propagate_exact_compute_exception(self) -> None:
        error = ValueError('schema-migration: ambiguous id')
        for call in (project.run, project.render, project.run_many, project.render_many):
            with patch.object(engine, 'compute', side_effect=error):
                with self.assertRaises(ValueError) as raised:
                    call([[]])
                self.assertIs(raised.exception, error)


if __name__ == '__main__':
    unittest.main()
