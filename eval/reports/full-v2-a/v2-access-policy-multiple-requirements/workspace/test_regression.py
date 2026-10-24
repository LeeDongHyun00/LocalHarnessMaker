import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' First ', 'target': 'obsolete', 'value': 100},
            {'id': 'allow', 'target': 'resource', 'value': 4},
            {'id': 'FIRST', 'target': ' Resource ', 'value': -4},
            {'id': 'z', 'target': 'resource', 'value': -4},
            {'id': 'zero', 'target': 'other', 'value': 0},
        ]
        expected = {'decisions': {
            'other': {'rule': 'zero', 'allow': False},
            'resource': {'rule': 'first', 'allow': False},
        }}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'decisions': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_validation_keeps_all_revisions_and_order(self) -> None:
        rows = [
            {'id': ' Z ', 'target': ' Straße / A  B ', 'value': 9},
            {'id': 'a', 'target': 'x', 'value': -1},
            {'id': 'z', 'target': 'y', 'value': 1},
        ]
        canonical = validation.validate(rows)
        self.assertEqual([r['id'] for r in canonical], ['z', 'a', 'z'])
        self.assertEqual(canonical[0]['target'], 'strasse / a  b')
        self.assertEqual(policy.normalize(' Straße / A  B '), 'strasse / a  b')
        with patch.object(engine, 'resolve', return_value={}) as resolve:
            engine.compute(rows)
        self.assertEqual(resolve.call_args.args[0], [canonical[2], canonical[1]])
        canonical[0]['value'] = 0
        self.assertEqual(rows[0]['value'], 9)

    def test_all_entry_points_normalize_and_render_exactly(self) -> None:
        rows = [{'id': ' RÜLE ', 'target': ' É / A  B ', 'value': 1}]
        expected = {'decisions': {'é / a  b': {'rule': 'rüle', 'allow': True}}}
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        serialized = '{"decisions":{"é / a  b":{"allow":true,"rule":"rüle"}}}\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows]), serialized)
        self.assertEqual(json.loads(serialized), expected)

    def test_invalid_structure_and_error_precedence(self) -> None:
        class IntSubclass(int):
            pass

        malformed = [None, [], {},
                     {'id': 'a', 'target': 't', 'value': 1, 'extra': 2},
                     {'id': ' ', 'target': 't', 'value': 1},
                     {'id': 'a', 'target': '\t', 'value': 1},
                     {'id': 1, 'target': 't', 'value': 1},
                     {'id': 'a', 'target': None, 'value': 1}]
        malformed.extend({'id': 'a', 'target': 't', 'value': v}
                         for v in [True, 1.0, '1', IntSubclass(1)])
        revisions = [{'id': 'a', 'target': 't', 'value': 1},
                     {'id': 'a', 'target': 'u', 'value': 2}]
        for bad in malformed:
            rows = revisions + [bad]
            before = copy.deepcopy(rows)
            for api in [validation.validate, engine.compute, run, render,
                        lambda r: run_many([r]), lambda r: render_many([r])]:
                with self.subTest(bad=bad, api=api):
                    with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
        for api in [validation.validate, engine.compute, run, render]:
            with self.assertRaisesRegex(TypeError, '^access-policy: rows must be a list$'):
                api(())
        for api in [run_many, render_many]:
            with self.assertRaisesRegex(TypeError, '^access-policy: batches must be a list$'):
                api(())

    def test_subclasses_and_unbounded_integers(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' A '), target=Text(' T '), value=10**1000)])
        expected = {'decisions': {'t': {'rule': 'a', 'allow': True}}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])

    def test_empty_and_dictionary_order(self) -> None:
        self.assertEqual(run([]), {'decisions': {}})
        self.assertEqual(render([]), '{"decisions":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        result = run([{'id': t, 'target': t, 'value': 1} for t in ['z', 'a']])
        self.assertEqual(list(result), ['decisions'])
        self.assertEqual(list(result['decisions']), ['a', 'z'])
        self.assertEqual(list(result['decisions']['a']), ['rule', 'allow'])

    def test_outputs_are_independent(self) -> None:
        rows = [{'id': 'a', 'target': 't', 'value': 1}]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        separate = run(rows)
        outputs[0]['decisions']['t']['allow'] = False
        self.assertTrue(outputs[1]['decisions']['t']['allow'])
        self.assertTrue(separate['decisions']['t']['allow'])
        self.assertEqual(run(rows), separate)
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['decisions']['new'] = {}
        self.assertEqual(empty[1], {'decisions': {}})

    def test_compute_is_resolved_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 't', 'value': 1}]
        for api, arg, calls in [(run, rows, 1), (render, rows, 1),
                                (run_many, [rows, []], 2),
                                (render_many, [rows, []], 2)]:
            with self.subTest(api=api):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(arg)
                    self.assertEqual(compute.call_count, calls)
                    self.assertEqual([c.args[0] for c in compute.call_args_list],
                                     [rows] if calls == 1 else [rows, []])

    def test_batches_stop_at_first_failure_and_preserve_inputs(self) -> None:
        valid = [{'id': 'a', 'target': 't', 'value': 1}]
        batches = [valid, [{'id': 'bad'}], None]
        before = copy.deepcopy(batches)
        for api in [run_many, render_many]:
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)
            error = RuntimeError('instrumented failure')
            with patch.object(engine, 'compute', side_effect=error):
                with self.assertRaises(RuntimeError) as caught:
                    api([valid, None])
                self.assertIs(caught.exception, error)


if __name__ == '__main__':
    unittest.main()
