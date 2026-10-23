import inspect
import typing
import unittest

import solution

from solution import inclusive, inclusive_legacy


class InclusiveTests(unittest.TestCase):
    def test_public_api_compatibility(self):
        for name in ("inclusive", "inclusive_legacy"):
            function = getattr(solution, name)
            with self.subTest(function=name):
                self.assertEqual(function.__name__, name)
                self.assertEqual(
                    str(inspect.signature(function)),
                    "(start: int, stop: int) -> list[int]",
                )
                self.assertEqual(
                    typing.get_type_hints(function),
                    {"start": int, "stop": int, "return": list[int]},
                )
        namespace = {}
        exec("from solution import *", namespace)
        self.assertEqual(
            {name for name in namespace if not name.startswith("_")},
            {"inclusive", "inclusive_legacy"},
        )
        self.assertIs(namespace["inclusive"], inclusive)
        self.assertIs(namespace["inclusive_legacy"], inclusive_legacy)

    def test_inclusive_ranges(self):
        for function in (inclusive, inclusive_legacy):
            for start, stop, expected in (
                (1, 4, [1, 2, 3, 4]),
                (3, -1, [3, 2, 1, 0, -1]),
                (-2, 1, [-2, -1, 0, 1]),
                (5, 5, [5]),
            ):
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    result = function(start=start, stop=stop)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, expected)

    def test_invalid_endpoints_raise_type_error(self):
        for function in (inclusive, inclusive_legacy):
            for start, stop in ((None, 1), (1, None), (1.5, 3), (1, 3.5)):
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    with self.assertRaises(TypeError):
                        function(start, stop)

    def test_error_behavior_matches_original_algorithm(self):
        def original(start: int, stop: int) -> list[int]:
            step = 1 if stop >= start else -1
            return list(range(start, stop + step, step))

        for start, stop in (
            (None, 1), (1, None), (1.5, 3), (1, 3.5),
            ("1", "3"), ([1], [3]), ({1}, {3}), (1j, 3j),
        ):
            with self.assertRaises(TypeError) as expected:
                original(start, stop)
            for function in (inclusive, inclusive_legacy):
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    with self.assertRaises(type(expected.exception)) as actual:
                        function(start, stop)
                    self.assertEqual(str(actual.exception), str(expected.exception))

    def test_invalid_collections_are_not_mutated(self):
        for function in (inclusive, inclusive_legacy):
            with self.subTest(function=function.__name__):
                start, stop = [1], [3]
                with self.assertRaises(TypeError):
                    function(start, stop)
                self.assertEqual(start, [1])
                self.assertEqual(stop, [3])


if __name__ == "__main__":
    unittest.main()
