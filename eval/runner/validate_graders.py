"""Validate private graders against untouched and solved copies, without executors.

References use .references/TASK/application.json with a ``files`` object mapping
reference-relative filenames to workspace-relative destinations. Reference sources
must never be named test_*.py. Only counts and content hashes are published.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from eval.runner import core
from eval.runner.audit import PrivateGraders, digest
from eval.runner.process import run_process


def apply_reference(reference: Path, workspace: Path) -> None:
    """Apply a private reference overlay without copying its manifest or storage."""
    files = json.loads((reference / "application.json").read_text())["files"]
    if not isinstance(files, dict) or not files:
        raise ValueError("Reference overlay must be nonempty")
    for source, target in files.items():
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError("Reference overlay entries must be strings")
        origin, destination = reference / source, workspace / target
        if (not origin.resolve().is_relative_to(reference.resolve())
                or not destination.resolve().is_relative_to(workspace.resolve())
                or origin.is_symlink() or not origin.is_file()
                or (origin.name.startswith("test_") and origin.suffix == ".py")):
            raise ValueError("Unsafe reference overlay")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, destination)


def validate_task(private_root: Path, task_id: str) -> dict[str, Any]:
    """Exercise the exact trusted runner grader on two independent public copies."""
    if task_id not in {p.name for p in (core.REPOSITORY / 'eval/tasks').iterdir() if p.is_dir()}:
        raise ValueError("Unknown task")
    private = PrivateGraders.load(private_root, task_id, core.REPOSITORY)
    public = core.REPOSITORY / 'eval/tasks' / task_id
    expected = json.loads((public / 'expected.json').read_text())
    with tempfile.TemporaryDirectory(prefix='lhm-grader-validation-') as temporary:
        runtime = Path(temporary)
        results = []
        for label in ('public', 'reference'):
            workspace = runtime / label
            shutil.copytree(public / 'workspace', workspace,
                            ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
            if label == 'reference':
                apply_reference(private.root / '.references' / task_id, workspace)
            result = core.grade(workspace, private, runtime, runtime / f'{label}.log',
                                expected, 30, run_process)
            results.append(result)
    baseline, reference = results
    valid = (baseline['result'] == 'fail' and baseline['failed_tests'] >= 1
             and baseline.get('total_tests') == expected['expected_test_count']
             and reference['result'] == 'pass' and reference['failed_tests'] == 0)
    return {'task_id': task_id, 'public_passed': baseline['passed_tests'],
            'public_failed': baseline['failed_tests'], 'reference_passed': reference['passed_tests'],
            'reference_failed': reference['failed_tests'], 'valid_count': int(valid),
            'grader_sha256': [digest(p.read_bytes()) for p in private.files]}


def main() -> int:
    """Print task identifiers, counts and hashes only, even on setup failures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--tasks', nargs='+', required=True)
    args = parser.parse_args()
    tasks = (sorted(p.name for p in (core.REPOSITORY / 'eval/tasks').iterdir() if p.is_dir())
             if args.tasks == ['all'] else args.tasks)
    valid = 0
    for task in tasks:
        try:
            row = validate_task(args.private_root, task)
        except Exception:
            row = {'task_id': task if task in {p.name for p in (core.REPOSITORY / 'eval/tasks').iterdir()} else 'unknown',
                   'valid_count': 0}
        print(json.dumps(row, sort_keys=True), flush=True)
        valid += row['valid_count']
    summary: dict[str, Any] = {'task_count': len(tasks), 'valid_count': valid,
                               'invalid_count': len(tasks) - valid}
    if valid == len(tasks):
        try:
            summary['task_set_sha256'] = core.taskset_digest({
                task: PrivateGraders.load(args.private_root, task, core.REPOSITORY) for task in tasks
            })
        except Exception:
            summary['hash_error_count'] = 1
    print(json.dumps(summary, sort_keys=True))
    return 0 if valid == len(tasks) and 'task_set_sha256' in summary else 1


if __name__ == '__main__':
    raise SystemExit(main())
