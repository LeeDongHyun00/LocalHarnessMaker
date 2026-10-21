"""Prepare unfrozen public task candidates without creating any private graders."""

import ast
import json
from pathlib import Path
from typing import Any

# name, signature, public behavior, starter defect, behavior-preserving seed
CATALOG: list[tuple[str, str, str, str, str]] = [
    ("stable-unique", "unique(items: list[str]) -> list[str]", "Return each string once, in first-occurrence order. Empty input returns []. Equality is case-sensitive.", "return sorted(set(items))", "return list(dict.fromkeys(items))"),
    ("rotate-left", "rotate(items: list[int], steps: int) -> list[int]", "Rotate left by steps modulo length. Negative steps rotate right. Empty input returns []. Example: [1,2,3], 4 gives [2,3,1].", "return items[steps:] + items[:steps]", "if not items: return []\nsteps %= len(items)\nreturn items[steps:] + items[:steps]"),
    ("adjacent-runs", "runs(items: list[str]) -> list[tuple[str, int]]", "Run-length encode adjacent equal strings as (value,count) pairs. Nonadjacent equal values form separate runs. Empty input returns [].", "return [(value, items.count(value)) for value in dict.fromkeys(items)]", "result: list[tuple[str, int]] = []\nfor item in items:\n    if result and result[-1][0] == item:\n        result[-1] = (item, result[-1][1] + 1)\n    else:\n        result.append((item, 1))\nreturn result"),
    ("clamp-values", "clamp(value: int, low: int, high: int) -> int", "Clamp value into the inclusive [low,high] range. Raise ValueError if low > high. Equal bounds are valid.", "return min(value, high)", "if low > high: raise ValueError('reversed bounds')\nreturn max(low, min(value, high))"),
    ("merge-counts", "merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]", "Return the union of keys, adding counts for shared keys. Preserve zero and negative totals. Neither input may be changed.", "return left | right", "result = dict(left)\nfor key, value in right.items(): result[key] = result.get(key, 0) + value\nreturn result"),
    ("pairwise-edges", "pairs(items: list[int]) -> list[tuple[int, int]]", "Return overlapping adjacent pairs in input order. Inputs with fewer than two items return []. Example [1,2,3] gives [(1,2),(2,3)].", "return list(zip(items[::2], items[1::2]))", "return list(zip(items, items[1:]))"),
    ("prefix-sums", "prefix(items: list[int]) -> list[int]", "Return inclusive prefix sums, preserving input length. Empty input returns []. Negative numbers are supported.", "return [sum(items[:i]) for i in range(len(items))]", "result: list[int] = []\nvalue = 0\nfor item in items:\n    value += item\n    result.append(value)\nreturn result"),
    ("flatten-once", "flatten(items: list[list[int]]) -> list[int]", "Flatten exactly one list level and preserve order. Ignore empty inner lists. Return a new list without modifying inner lists.", "return [group[0] for group in items if group]", "return [item for group in items for item in group]"),
    ("inclusive-range", "inclusive(start: int, stop: int) -> list[int]", "Return all integers from start through stop, inclusive, stepping +1 or -1 as appropriate. Equal endpoints give a singleton.", "return list(range(start, stop))", "step = 1 if stop >= start else -1\nreturn list(range(start, stop + step, step))"),
    ("word-counts", "words(text: str) -> dict[str, int]", "Split on arbitrary whitespace, casefold each token, and count it. Punctuation remains part of the token. Empty or whitespace-only text returns {}.", "return {word: text.split().count(word) for word in text.split()}", "result: dict[str, int] = {}\nfor word in text.split():\n    word = word.casefold()\n    result[word] = result.get(word, 0) + 1\nreturn result"),
    ("line-endings", "normalize(text: str) -> str", "Replace CRLF and lone CR with LF. Preserve existing LF, all other characters, and the number of line breaks. Do not strip trailing newlines.", "return text.replace('\\r', '')", "return text.replace('\\r\\n', '\\n').replace('\\r', '\\n')"),
    ("common-prefix", "common(items: list[str]) -> str", "Return the longest common character prefix. Matching is case-sensitive. Empty input returns an empty string; one item returns that item.", "return items[0] if items else ''", "if not items: return ''\nprefix = items[0]\nfor item in items[1:]:\n    while not item.startswith(prefix): prefix = prefix[:-1]\nreturn prefix"),
    ("partition-sign", "partition(items: list[int]) -> tuple[list[int], list[int], list[int]]", "Return negatives, zeros, positives as three lists in that order. Preserve relative order and duplicates in each partition.", "return (sorted(x for x in items if x < 0), [], sorted(x for x in items if x > 0))", "return ([x for x in items if x < 0], [x for x in items if x == 0], [x for x in items if x > 0])"),
    ("invert-groups", "invert(items: dict[str, str]) -> dict[str, list[str]]", "Group input keys by their values. Each list of keys follows dictionary insertion order. Empty input returns {}.", "return {value: [key] for key, value in items.items()}", "result: dict[str, list[str]] = {}\nfor key, value in items.items(): result.setdefault(value, []).append(key)\nreturn result"),
    ("window-slices", "windows(items: list[int], size: int) -> list[list[int]]", "Return all contiguous windows of exactly size, advancing by one. Raise ValueError for size <= 0. A size exceeding length returns [].", "return [items[i:i+size] for i in range(0, len(items), size)]", "if size <= 0: raise ValueError('positive size required')\nreturn [items[i:i+size] for i in range(len(items) - size + 1)]"),
    ("interleave", "interleave(left: list[int], right: list[int]) -> list[int]", "Alternate left then right items. Append any remainder from the longer input in order. Empty inputs are valid.", "return [item for pair in zip(left, right) for item in pair]", "result: list[int] = []\nfor i in range(max(len(left), len(right))):\n    if i < len(left): result.append(left[i])\n    if i < len(right): result.append(right[i])\nreturn result"),
    ("last-index", "last_index(items: list[str], target: str) -> int | None", "Return the last zero-based index equal to target, or None when absent. Empty input returns None. Matching is case-sensitive.", "return items.index(target) if target in items else None", "for i in range(len(items) - 1, -1, -1):\n    if items[i] == target: return i\nreturn None"),
    ("strip-prefix", "strip_prefix(text: str, prefix: str) -> str", "Remove exactly one matching prefix. A nonmatching or empty prefix leaves text unchanged. Do not strip individual characters or repeated prefixes.", "return text.lstrip(prefix)", "return text[len(prefix):] if prefix and text.startswith(prefix) else text"),
    ("balanced-brackets", "balanced(text: str) -> bool", "Check nesting of (), [] and {}. Ignore all other characters. An unmatched closing or opening bracket is false; empty text is true.", "return text.count('(') == text.count(')')", "stack: list[str] = []\npairs = {')': '(', ']': '[', '}': '{'}\nfor char in text:\n    if char in '([{': stack.append(char)\n    elif char in pairs:\n        if not stack or stack.pop() != pairs[char]: return False\nreturn not stack"),
    ("interval-union", "union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]", "Merge overlapping or touching closed intervals, sorted by start. Raise ValueError for any start > end. Empty input returns []. Do not mutate input.", "return sorted(intervals)", "result: list[tuple[int, int]] = []\nfor start, end in sorted(intervals):\n    if start > end: raise ValueError('reversed interval')\n    if result and start <= result[-1][1]: result[-1] = (result[-1][0], max(result[-1][1], end))\n    else: result.append((start, end))\nreturn result"),
    ("unique-permutations", "permutations(text: str) -> list[str]", "Return all distinct permutations of characters in sorted lexicographic order. The empty string has one permutation: the empty string. Inputs are at most seven characters.", "return [text]", "from itertools import permutations as permute\nreturn sorted({''.join(p) for p in permute(text)})"),
    ("round-robin", "round_robin(groups: list[list[int]]) -> list[int]", "Take one item from each nonempty group in order each round until exhausted. Preserve order inside each group. Never modify groups.", "return [x for group in groups for x in group]", "return [group[i] for i in range(max(map(len, groups), default=0)) for group in groups if i < len(group)]"),
    ("parse-pairs", "parse_pairs(text: str) -> dict[str, str]", "Parse nonempty newline-separated key=value records, splitting on the first equals sign and stripping both sides. Ignore blank lines; last repeated key wins. Raise ValueError on missing equals or empty key. Empty values are allowed.", "return dict(line.split('=') for line in text.splitlines())", "result: dict[str, str] = {}\nfor line in text.splitlines():\n    if not line.strip(): continue\n    key, sep, value = line.partition('=')\n    key = key.strip()\n    if not sep or not key: raise ValueError('invalid record')\n    result[key] = value.strip()\nreturn result"),
    ("select-columns", "select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]", "Return new dictionaries containing requested columns in column order for every row. Missing keys are omitted. Keep row order, preserve values, and never modify rows. Repeated column names appear once.", "return [{key: row[key] for key in columns} for row in rows]", "return [{key: row[key] for key in columns if key in row} for row in rows]"),
    ("ordinal-labels", "ordinal(value: int) -> str", "Format a nonnegative integer with its English ordinal suffix: 1st, 2nd, 3rd, 4th; 11,12,13 use th, including 111,112,113. Raise ValueError for negatives. Zero is 0th.", "return str(value) + {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')", "if value < 0: raise ValueError('nonnegative value required')\nsuffix = 'th' if 10 <= value % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')\nreturn str(value) + suffix"),
]


def source(signature: str, body: str) -> str:
    """Produce runnable public scaffolding, never private grading code."""
    return '"""Public task implementation."""\n\n\ndef ' + signature + ':\n' + ''.join('    ' + line + '\n' for line in body.splitlines())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')


def prepare(root: Path) -> list[str]:
    """Write only absent candidate paths; existing/frozen tasks are never replaced."""
    pending: list[str] = []
    for category in ('bug_fix', 'feature_plus_test', 'multiple_requirements', 'constrained_refactoring', 'two_session'):
        entries = CATALOG[:24] if category == 'bug_fix' else CATALOG[:20] if category == 'two_session' else CATALOG
        for name, signature, spec, defect, correct in entries:
            task_id = category.replace('_', '-') + '-' + name
            task = root / task_id
            pending.append(task_id)
            if task.exists():
                continue
            workspace = task / 'workspace'
            workspace.mkdir(parents=True)
            function = signature.split('(')[0]
            body = 'raise NotImplementedError("Implement the public specification")' if category in {'feature_plus_test', 'two_session'} else defect
            text = source(signature, body)
            if category == 'constrained_refactoring':
                legacy = signature.replace(function + '(', function + '_legacy(', 1)
                text = source(signature, correct) + '\n\n' + source(legacy, correct).split('\n\n\n', 1)[1]
                instruction = f'Refactor {function} and {function}_legacy to delegate their shared algorithm to one private helper. Preserve both signatures, return types, error behavior and input immutability. Keep imports and public names compatible.'
            elif category == 'feature_plus_test':
                instruction = f'Implement {function} and add standard-library unittest tests in test_solution.py covering ordinary, boundary and empty inputs (or invalid numeric inputs when no collection is accepted).'
            elif category == 'multiple_requirements':
                instruction = f'Repair {function}. Also add its public specification as a docstring, add regression tests in test_solution.py, and preserve input values and collection order as specified.'
            elif category == 'two_session':
                instruction = f'Day 1: implement {function}, add unittest regression coverage, and record design decisions plus a verification command in HANDOFF.md for the next session.'
            else:
                instruction = f'Fix the incorrect behavior of {function} without changing its signature. Add a small regression test in test_solution.py.'
            prompt = f'{instruction}\n\nWork only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.\n\nPublic behavior:\n{spec}\n\nMaintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.\n'
            (task / 'prompt.md').write_text(prompt)
            (workspace / 'solution.py').write_text(text)
            ast.parse(text)
            two = category == 'two_session'
            meta: dict[str, Any] = {'id': task_id, 'type': 'feature_plus_test' if two else category,
                'difficulty': 'easy' if category == 'bug_fix' else 'medium', 'two_session': two,
                'source': 'hand_written', 'version': 1, 'frozen': False, 'grader_status': 'pending',
                'family': name, 'review_status': 'draft'}
            if two:
                day2 = f'Day 2: extend the existing public API with {function}_many(cases: list[tuple]) -> list. Each tuple supplies positional arguments for one call of {function}. Return results in case order, [] for no cases, and propagate the first exception unchanged. Keep the day-1 API compatible, do not mutate cases or arguments, add unittest coverage, and update HANDOFF.md with verification evidence. Use the workspace and handoff provided by the runner.\n'
                (task / 'day2.md').write_text(day2)
                meta['day2_prompt'] = 'day2.md'
            write_json(task / 'meta.json', meta)
            write_json(task / 'expected.json', {'command': ['python', '-I', '-m', 'unittest', 'discover', '-v'],
                'expected_exit_code': 0, 'expected_test_count': 3, 'grader_status': 'pending',
                'pass_condition': 'Pending external graders: ordinary behavior, boundaries/errors, and compatibility/input preservation.',
                'planned_grader_groups': ['ordinary behavior', 'boundaries and errors', 'compatibility and input preservation']})
    return pending


if __name__ == '__main__':
    tasks = Path(__file__).resolve().parents[1] / 'tasks'
    missing = prepare(tasks)
    manifest = tasks.parent / 'GRADERS-PENDING.md'
    manifest.write_text('# Public task candidates awaiting external graders\n\n'
        'These 119 candidates are unfrozen drafts in 25 related families. No hidden graders were written. '
        'Each needs specification review, external graders, negative/reference validation, and diversity review before freeze. '
        'The existing bug-chunk-tail has historical external grader evidence; host revalidation is pending. '
        'Related family variants must not be treated as independent evidence of broad task diversity.\n\n'
        '| Task ID | Grader status |\n| --- | --- |\n' + ''.join(f'| {task} | pending |\n' for task in missing))
    print(f'Prepared {len(missing)} public candidates; no graders generated.')
