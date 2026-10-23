"""Regression coverage for the public interleave API."""

from unittest import TestCase, main

from solution import interleave, interleave_many


class InterleaveTests(TestCase):
    def test_equal_lengths_alternate_left_first(self) -> None:
        self.assertEqual(interleave([1, 2, 3], [4, 5, 6]), [1, 4, 2, 5, 3, 6])

    def test_longer_left_keeps_remainder_in_order(self) -> None:
        self.assertEqual(interleave([1, 2, 3, 4], [5]), [1, 5, 2, 3, 4])

    def test_longer_right_keeps_remainder_in_order(self) -> None:
        self.assertEqual(interleave([1], [2, 3, 4, 5]), [1, 2, 3, 4, 5])

    def test_empty_inputs(self) -> None:
        self.assertEqual(interleave([], []), [])
        self.assertEqual(interleave([], [1, 2]), [1, 2])
        self.assertEqual(interleave([1, 2], []), [1, 2])

    def test_inputs_are_unchanged_and_result_is_new(self) -> None:
        left = [1, 2]
        right = [3, 4]
        result = interleave(left, right)
        self.assertEqual(left, [1, 2])
        self.assertEqual(right, [3, 4])
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)
        result.append(5)
        self.assertEqual(left, [1, 2])
        self.assertEqual(right, [3, 4])

    def test_iterables_and_mixed_values(self) -> None:
        self.assertEqual(
            interleave((value for value in (None, 0)), ("a", "b", "c")),
            [None, "a", 0, "b", "c"],
        )

    def test_many_results_follow_case_order(self) -> None:
        self.assertEqual(
            interleave_many([([1, 2], [3]), ((), ("a", "b")), ([], [])]),
            [[1, 3, 2], ["a", "b"], []],
        )

    def test_many_empty_cases(self) -> None:
        self.assertEqual(interleave_many([]), [])

    def test_many_preserves_cases_and_arguments(self) -> None:
        left = [1, 2]
        right = [3, 4]
        case = (left, right)
        cases = [case, case]
        results = interleave_many(cases)
        self.assertEqual(cases, [([1, 2], [3, 4]), ([1, 2], [3, 4])])
        self.assertIs(cases[0], case)
        self.assertIs(cases[1], case)
        self.assertIs(case[0], left)
        self.assertIs(case[1], right)
        results[0].append(5)
        self.assertEqual(results[1], [1, 3, 2, 4])
        self.assertEqual(left, [1, 2])
        self.assertEqual(right, [3, 4])

    def test_many_propagates_first_exception_unchanged_and_stops(self) -> None:
        first_error = ValueError("first failure")
        later_error = RuntimeError("later failure")
        visited = []

        def failing_items(label, error):
            visited.append(label)
            raise error
            yield  # Make this an iterator; failure occurs when consumed.

        cases = [
            ([1], [2]),
            (failing_items("first", first_error), []),
            (failing_items("later", later_error), []),
        ]
        with self.assertRaises(ValueError) as caught:
            interleave_many(cases)
        self.assertIs(caught.exception, first_error)
        self.assertEqual(visited, ["first"])

    def test_many_forwards_positional_argument_errors(self) -> None:
        with self.assertRaises(TypeError):
            interleave_many([([1],)])


if __name__ == "__main__":
    main()
