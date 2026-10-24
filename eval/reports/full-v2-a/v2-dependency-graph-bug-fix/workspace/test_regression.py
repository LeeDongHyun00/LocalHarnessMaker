import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def row(identifier: str, target: str, value: int = 1) -> dict:
    return {'id': identifier, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [row(' A ', ' Z ', -100), row('z', 'z'),
                row(' B ', 'B'), row('a', 'z', -100), row('0', 'a')]
        expected = {'order': ['b', 'z', 'a', '0']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'order': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_validation(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(row(Text(' Straße / A  B '), Text(' STRASSE / A  B '), 10**1000))])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [row('strasse / a  b', 'strasse / a  b', 10**1000)])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' É / A  B '), 'é / a  b')
        self.assertEqual(engine.compute(rows), {'order': ['strasse / a  b']})

    def test_validation_does_not_select_or_resolve(self) -> None:
        rows = [row(' A ', 'missing'), row('a', 'a', 2)]
        self.assertEqual(validation.validate(rows), [row('a', 'missing'), row('a', 'a', 2)])

    def test_errors_and_precedence(self) -> None:
        class Integer(int):
            pass

        malformed = [None, [], {}, row('', 'a'), row('a', ' '),
                     row(1, 'a'), row('a', None), row('a', 'a', True),
                     row('a', 'a', Integer(1)), row('a', 'a', 1.0),
                     dict(row('a', 'a'), extra=1)]
        prefixes = [[row('a', 'a'), row('a', 'a', 2)],
                    [row('a', 'missing')], [row('a', 'b'), row('b', 'a')]]
        for invalid in malformed:
            for prefix in prefixes:
                rows = prefix + [invalid]
                original = copy.deepcopy(rows)
                for api in (run, render, engine.compute, validation.validate):
                    with self.subTest(api=api.__name__, invalid=invalid, prefix=prefix):
                        with self.assertRaisesRegex(ValueError, '^dependency-graph: invalid row$'):
                            api(rows)
                        self.assertEqual(rows, original)
        for invalid in (None, (), {}, 'a'):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^dependency-graph: rows must be a list$'):
                    api(invalid)

    def test_domain_failures(self) -> None:
        for rows, message in (
            ([row('a', 'a'), row(' A ', 'a', 2)], 'duplicate id'),
            ([row('a', 'missing')], 'missing dependency'),
            ([row('a', 'b'), row('b', 'a')], 'cycle'),
            ([row('root', 'root'), row('a', 'b'), row('b', 'a')], 'cycle'),
        ):
            original = copy.deepcopy(rows)
            for api in (run, render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^dependency-graph: ' + message + '$'):
                    api(rows)
                self.assertEqual(rows, original)

    def test_serialization_and_empty_inputs(self) -> None:
        rows = [row(' É ', 'é')]
        self.assertEqual(render(rows), '{"order":["é"]}\n')
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False,
                                                sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'order': []})
        self.assertEqual(render([]), '{"order":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_outputs(self) -> None:
        rows = [row('a', 'a')]
        original = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        outputs[0]['order'].append('changed')
        self.assertEqual(outputs[1], {'order': ['a']})
        self.assertEqual(run(rows), {'order': ['a']})
        self.assertEqual(rows, original)
        first = validation.validate(rows)
        first[0]['target'] = 'changed'
        self.assertEqual(validation.validate(rows), original)

    def test_runtime_compute_dispatch(self) -> None:
        rows = [row('a', 'a')]
        for api, argument, calls in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, calls)

    def test_batch_atomicity_and_encounter_order(self) -> None:
        for api in (run_many, render_many):
            for invalid in (None, (), {}, ''):
                with self.assertRaisesRegex(TypeError, '^dependency-graph: batches must be a list$'):
                    api(invalid)
            batches = [[row('a', 'a')], [row('b', 'missing')], [None]]
            original = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^dependency-graph: missing dependency$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], batches[0])
                self.assertIs(compute.call_args_list[1].args[0], batches[1])
            self.assertEqual(batches, original)


if __name__ == '__main__':
    unittest.main()
