import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


def row(event: str, target: str, value: int) -> dict:
    return {'id': event, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        # Replacing an ID must retain its original position, before closing.
        rows = [row('start', 'Flow', 0), row('UPDATE', 'old', 0),
                row('finish', 'flow', 2), row(' update ', ' FLOW ', 1)]
        self.assertEqual(project.run(rows), {'states': {'flow': 2}})
        self.assertEqual(project.run_many([rows, []]),
                         [{'states': {'flow': 2}}, {'states': {}}])
        self.assertEqual(project.render_many([rows, []]),
                         '{"states":{"flow":2}}\n{"states":{}}\n')

    def test_priority_and_encountered_ambiguity(self) -> None:
        rows = [row('a', 'flow', 0), row('b', 'flow', 1),
                row('b', 'ignored', 0), row('b', 'flow', 1),
                row('c', 'flow', 2), row('d', 'flow', 2)]
        self.assertEqual(project.run(rows), {'states': {'flow': 2}})
        ambiguous = [row('x', 'a', 0), row('X', 'b', 0), row('x', 'a', 1)]
        with self.assertRaisesRegex(ValueError, '^workflow-state: ambiguous id$'):
            project.run(ambiguous)

    def test_structural_validation_precedes_domain(self) -> None:
        for prefix in ([row('a', 'a', 1)],
                       [row('a', 'a', 99)],
                       [row('a', 'a', 0), row('a', 'b', 0)]):
            with self.subTest(prefix=prefix):
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid row$'):
                    project.run(prefix + [row('late', ' ', 0)])
        rows = [row(' X ', ' A ', 10 ** 100), row('x', ' B ', 0)]
        self.assertEqual(validation.validate(rows),
                         [row('x', 'a', 10 ** 100), row('x', 'b', 0)])

    def test_invalid_row_shapes_and_types(self) -> None:
        class IntSubclass(int):
            pass

        malformed = [None, [], {}, row('', 'a', 0), row('a', '\t', 0),
                     row(1, 'a', 0), row('a', None, 0), row('a', 'a', True),
                     row('a', 'a', IntSubclass(0)), row('a', 'a', 0.0),
                     dict(row('a', 'a', 0), extra=1)]
        for bad in malformed:
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid row$'):
                    validation.validate([bad])
        for bad in (None, (), {}, 'rows'):
            for api in (project.run, project.render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^workflow-state: rows must be a list$'):
                    api(bad)

    def test_normalization_and_subclasses(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=Text(' STRAẞE/ A '), target=Text(' É/ A  B '), value=0)])
        expected = {'states': {'é/ a  b': 0}}
        self.assertEqual(policy.normalize(Text(' STRAẞE/ A ')), 'strasse/ a')
        self.assertEqual(validation.validate(rows), [row('strasse/ a', 'é/ a  b', 0)])
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many(Rows([rows])), [expected])
        self.assertEqual(project.render(rows), '{"states":{"é/ a  b":0}}\n')
        self.assertEqual(project.render_many([rows]), project.render(rows))

    def test_states_and_transitions(self) -> None:
        for codes in ([1], [2], [0, 2], [0, 1, 0], [0, 1, 2, 1], [0, 1, 2, 0]):
            with self.subTest(codes=codes):
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid transition$'):
                    project.run([row(str(i), 'a', code) for i, code in enumerate(codes)])
        for code in (-1, 3, 10 ** 100, -(10 ** 100)):
            with self.assertRaisesRegex(ValueError, '^workflow-state: invalid state$'):
                project.run([row('first', 'a', 1), row('bad', 'b', code)])
        codes = [0, 0, 1, 1, 2, 2]
        self.assertEqual(project.run([row(str(i), 'a', code) for i, code in enumerate(codes)]),
                         {'states': {'a': 2}})

    def test_empty_results_and_sorted_workflows(self) -> None:
        self.assertEqual(project.run([]), {'states': {}})
        self.assertEqual(project.render([]), '{"states":{}}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        result = project.run([row('z', 'z', 0), row('a', 'a', 0)])
        self.assertEqual(list(result), ['states'])
        self.assertEqual(list(result['states']), ['a', 'z'])

    def test_render_matches_run(self) -> None:
        rows = [row('z', 'Ω', 0), row('a', 'é', 0)]
        expected = json.dumps(project.run(rows), ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(project.render(rows), expected)
        self.assertEqual(project.render_many([rows, []]), expected + project.render([]))

    def test_results_are_fresh_and_inputs_unchanged(self) -> None:
        rows = [row(' A ', ' Flow ', 0)]
        batches = [rows, rows]
        before = copy.deepcopy(batches)
        result = project.run_many(batches)
        result[0]['states']['flow'] = 2
        self.assertEqual(result[1], {'states': {'flow': 0}})
        self.assertEqual(project.run(rows), {'states': {'flow': 0}})
        canonical = validation.validate(rows)
        canonical[0]['target'] = 'changed'
        self.assertEqual(batches, before)
        first_empty, second_empty = project.run_many([[], []])
        first_empty['states']['added'] = 0
        self.assertEqual(second_empty, {'states': {}})

    def test_batch_validation_and_atomic_failure(self) -> None:
        for api in (project.run_many, project.render_many):
            for bad in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^workflow-state: batches must be a list$'):
                    api(bad)
            batches = [[row('a', 'a', 0)], [row('b', 'b', 1)], [None]]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid transition$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], batches[0])
                self.assertIs(compute.call_args_list[1].args[0], batches[1])
            self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^workflow-state: rows must be a list$'):
                api([[] , None])

    def test_shared_compute_resolved_at_call_time(self) -> None:
        rows = [row('a', 'a', 0)]
        for api, argument, count in ((project.run, rows, 1), (project.render, rows, 1),
                                     (project.run_many, [rows, rows], 2),
                                     (project.render_many, [rows, rows], 2)):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', return_value={'instrumented': True}) as compute:
                    output = api(argument)
                    self.assertEqual(compute.call_count, count)
                    if api is project.run:
                        self.assertEqual(output, {'instrumented': True})
                    elif api is project.render:
                        self.assertEqual(output, '{"instrumented":true}\n')
                    elif api is project.run_many:
                        self.assertEqual(output, [{'instrumented': True}] * 2)
                    else:
                        self.assertEqual(output, '{"instrumented":true}\n' * 2)

    def test_public_exception_parity_and_failure_immutability(self) -> None:
        cases = [([None], 'invalid row'),
                 ([row('x', 'a', 0), row('x', 'b', 0)], 'ambiguous id'),
                 ([row('x', 'a', 99)], 'invalid state'),
                 ([row('x', 'a', 1)], 'invalid transition')]
        for rows, message in cases:
            before = copy.deepcopy(rows)
            for api, arg in ((project.run, rows), (project.render, rows),
                             (project.run_many, [[], rows]),
                             (project.render_many, [[], rows])):
                with self.subTest(api=api.__name__, message=message):
                    with self.assertRaisesRegex(ValueError, '^workflow-state: ' + message + '$'):
                        api(arg)
                    self.assertEqual(rows, before)


if __name__ == '__main__':
    unittest.main()
