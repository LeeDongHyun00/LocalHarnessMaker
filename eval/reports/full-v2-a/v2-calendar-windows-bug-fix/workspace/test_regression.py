import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def assert_error(self, exception, message, rows):
        for api in (run, render, engine.compute, run_many, render_many):
            with self.subTest(api=api.__name__):
                argument = [rows] if api in (run_many, render_many) else rows
                before = copy.deepcopy(argument)
                with self.assertRaises(exception) as caught:
                    api(argument)
                self.assertEqual(str(caught.exception), 'calendar-windows: ' + message)
                self.assertEqual(argument, before)

    def test_domain_edge(self):
        rows = [
            {'id': ' Late ', 'target': ' STRAẞE/ A ', 'value': 23},
            {'id': 'late', 'target': 'strasse/ a', 'value': 23},
            {'id': 'Early', 'target': 'strasse/ a', 'value': 22},
            {'id': 'Other', 'target': ' A ', 'value': 22},
        ]
        expected = {'rooms': {'a': [[22, 23, 'other']],
                              'strasse/ a': [[22, 23, 'early'], [23, 24, 'late']]}}
        before = copy.deepcopy(rows)
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['rooms']), ['a', 'strasse/ a'])
        self.assertEqual(run_many([rows, [], rows]), [expected, {'rooms': {}}, expected])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows, [], rows]), serialized + '{"rooms":{}}\n' + serialized)
        self.assertEqual(rows, before)
        self.assert_error(ValueError, 'overlap', rows + [
            {'id': 'clash', 'target': 'strasse/ a', 'value': 22}])
        self.assert_error(ValueError, 'duplicate id', rows + [
            {'id': 'LATE', 'target': 'elsewhere', 'value': 23}])

    def test_structure_and_precedence(self):
        class IntSubclass(int):
            pass

        for rows in (None, (), {}, 'rows'):
            self.assert_error(TypeError, 'rows must be a list', rows)
        for bad in (None, [], {}, {'id': '', 'target': 'a', 'value': 1},
                    {'id': 'a', 'target': '  ', 'value': 1},
                    {'id': 1, 'target': 'a', 'value': 1},
                    {'id': 'a', 'target': None, 'value': 1},
                    {'id': 'a', 'target': 'a', 'value': True},
                    {'id': 'a', 'target': 'a', 'value': IntSubclass(1)},
                    {'id': 'a', 'target': 'a', 'value': 1, 'extra': []}):
            self.assert_error(ValueError, 'invalid row', [bad])
            self.assert_error(ValueError, 'invalid row', [
                {'id': 'a', 'target': 'a', 'value': 24},
                {'id': 'a', 'target': 'a', 'value': 0}, bad])
        for hour in (-1, 24, 10 ** 100, -(10 ** 100)):
            rows = [{'id': 'a', 'target': 'a', 'value': 0},
                    {'id': 'b', 'target': 'a', 'value': 0},
                    {'id': 'c', 'target': 'a', 'value': hour}]
            self.assert_error(ValueError, 'invalid hour', rows)
        rows = [{'id': ' A ', 'target': ' B ', 'value': 10 ** 100},
                {'id': 'a', 'target': 'b', 'value': -1}]
        self.assertEqual(validation.validate(rows), [
            {'id': 'a', 'target': 'b', 'value': 10 ** 100},
            {'id': 'a', 'target': 'b', 'value': -1}])
        self.assert_error(ValueError, 'duplicate id', rows)

    def test_subclasses_unicode_and_independence(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' É/  A '), target=Text(' Ω/  B '), value=0)])
        self.assertEqual(policy.normalize(Text(' É/  A ')), 'é/  a')
        expected = {'rooms': {'ω/  b': [[0, 1, 'é/  a']]}}
        self.assertEqual(engine.compute(rows), expected)
        self.assertIn('ω/  b', render(rows))
        outputs = run_many(Rows([rows, rows]))
        outputs[0]['rooms']['ω/  b'][0][2] = 'changed'
        self.assertEqual(outputs[1], expected)
        self.assertEqual(run(rows), expected)
        canonical = validation.validate(rows)
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows[0]['target'], ' Ω/  B ')
        empty = run_many([[], []])
        empty[0]['rooms']['new'] = []
        self.assertEqual(empty[1], {'rooms': {}})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_engine_delegation_and_batch_atomicity(self):
        rows = [{'id': 'a', 'target': 'b', 'value': 1}]
        for api in (run, render, run_many, render_many):
            batches = api in (run_many, render_many)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api([rows, rows] if batches else rows)
                self.assertEqual(compute.call_count, 2 if batches else 1)
        for api in (run_many, render_many):
            for invalid in (None, (), {}, 'batches'):
                with self.assertRaises(TypeError) as caught:
                    api(invalid)
                self.assertEqual(str(caught.exception), 'calendar-windows: batches must be a list')
            batches = [rows, [{'id': 'bad', 'target': 'b', 'value': 24}], [None]]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaises(ValueError) as caught:
                    api(batches)
                self.assertEqual(str(caught.exception), 'calendar-windows: invalid hour')
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
