"""Validate private graders against untouched and solved copies, without executors.

References use .references/TASK/application.json with a ``files`` object mapping
reference-relative filenames to workspace-relative destinations. Reference sources
must never be named test_*.py. Only counts and content hashes are published.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
from pathlib import Path
import shutil
import tempfile
from typing import Any

from eval.runner import core
from eval.runner.audit import PrivateGraders, digest
from eval.runner.process import run_process
from eval.runner.mutations import mutations


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


def public_task(task_id: str) -> Path:
    """Locate globally unique versioned IDs without adding CLI flags."""
    root = "eval/tasks-v2" if task_id.startswith("v2-") else "eval/tasks"
    public = core.task_directory({"task_root": root}) / task_id
    if Path(task_id).name != task_id or not public.is_dir() or public.is_symlink():
        raise ValueError("Unknown task")
    return public


def safe_task_id(task_id: str) -> str:
    """Keep failure output limited to known public task identifiers."""
    try:
        public_task(task_id)
    except (OSError, TypeError, ValueError):
        return 'unknown'
    return task_id


def validate_task(private_root: Path, task_id: str) -> dict[str, Any]:
    """Exercise the exact trusted runner grader on two independent public copies."""
    private = PrivateGraders.load(private_root, task_id, core.REPOSITORY)
    public = public_task(task_id)
    expected = json.loads((public / 'expected.json').read_text())
    with tempfile.TemporaryDirectory(prefix='lhm-grader-validation-', dir=private.root) as temporary:
        runtime = Path(temporary)
        results = []
        for label in ('public', 'reference'):
            workspace = runtime / label
            shutil.copytree(public / 'workspace', workspace,
                            ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
            if label == 'reference':
                apply_reference(private.root / '.references' / task_id, workspace)
            result = core.grade(workspace, private, runtime, runtime / f'{label}.log',
                                expected, 30, run_process, retention_root=runtime / "grading-copies")
            if label == 'reference' and task_id.startswith('v2-'):
                coverage = json.loads((private.root / task_id / 'coverage.json').read_text())
                requirements = set(re.findall(r"(?m)^([RD][0-9]+)\.", (public / 'prompt.md').read_text() +
                    ((public / 'day2.md').read_text() if (public / 'day2.md').exists() else '')))
                observed = (runtime / 'reference.log').read_text()
                covered = {key for key, tests in coverage.items() if isinstance(tests, list) and tests and
                           all(isinstance(test, str) and test + ')' in observed for test in tests)}
                result['coverage'] = {'requirement_count': len(requirements),
                                      'covered_requirement_count': len(requirements & covered),
                                      'uncovered_requirement_count': len(requirements - covered)}
            results.append(result)
    baseline, reference = results
    valid = (baseline['result'] == 'fail' and baseline['failed_tests'] >= 1
             and baseline.get('total_tests') == expected['expected_test_count']
             and reference['result'] == 'pass' and reference['failed_tests'] == 0
             and reference.get('coverage', {}).get('uncovered_requirement_count', 0) == 0)
    return {'task_id': task_id, 'public_passed': baseline['passed_tests'],
            'public_failed': baseline['failed_tests'], 'reference_passed': reference['passed_tests'],
            'reference_failed': reference['failed_tests'], 'valid_count': int(valid),
            'grader_sha256': [digest(p.read_bytes()) for p in private.files], **reference.get('coverage', {})}


def mutate_task(private_root: Path, task_id: str, limit: int) -> dict[str, Any]:
    """Grade reference-overlay mutants; keep review/equivalence data private.

    Application and submitted regression overlays are both mutated. Equivalences
    must be reviewed manually and contain a nonempty rationale, bound to source
    and public specification hashes. A survivor is never automatically equivalent.
    """
    private = PrivateGraders.load(private_root, task_id, core.REPOSITORY)
    public = public_task(task_id)
    reference = private.root / '.references' / task_id
    files = json.loads((reference / 'application.json').read_text())['files']
    expected = json.loads((public / 'expected.json').read_text())
    specification_bytes = (public / 'prompt.md').read_bytes() + (public / 'expected.json').read_bytes()
    if task_id.startswith('v2-') and (public / 'day2.md').is_file():
        specification_bytes += (public / 'day2.md').read_bytes()
    specification = digest(specification_bytes)
    records = private.root / '.mutation-records'
    records.mkdir(mode=0o700, exist_ok=True)
    equivalence_path = records / (task_id + '.equivalences.json')
    equivalences = json.loads(equivalence_path.read_text()) if equivalence_path.exists() else {}
    counts = {'task_id': task_id, 'killed': 0, 'survived': 0, 'recorded_equivalent': 0}
    reviews = []
    with tempfile.TemporaryDirectory(prefix='lhm-mutations-', dir=private.root) as temporary:
        runtime = Path(temporary)
        baseline = runtime / 'reference'
        shutil.copytree(public / 'workspace', baseline,
                        ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
        apply_reference(reference, baseline)
        control = core.grade(baseline, private, runtime, runtime / 'reference.log',
                             expected, 2, run_process, retention_root=runtime / 'grading-copies')
        if control['result'] != 'pass':
            raise ValueError('Mutation reference control must pass within the same deadline')
        overlay_hash = digest(json.dumps([(source, target, digest((reference / source).read_bytes()))
                                         for source, target in files.items()]).encode())
        candidates = []
        for source, target in files.items():
            if Path(target).suffix == '.py':
                original = (reference / source).read_text()
                candidates.extend((target, digest(original.encode()), mutation)
                                  for mutation in mutations(original))
        for number, (target, original_hash, mutation) in enumerate(candidates[:limit]):
            workspace = runtime / str(number)
            shutil.copytree(public / 'workspace', workspace,
                            ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
            apply_reference(reference, workspace)
            (workspace / target).write_text(mutation.source)
            result = core.grade(workspace, private, runtime, runtime / f'{number}.log',
                                expected, 2, run_process, retention_root=runtime / 'grading-copies')
            identity = digest((target + overlay_hash + mutation.sha256 + specification).encode())
            record = equivalences.get(identity, {})
            equivalent = isinstance(record, dict) and isinstance(record.get('reason'), str) and bool(record['reason'].strip())
            # Nontermination violates the same behavior as a failed assertion.
            killed = bool(result.get('timed_out')) or (result['result'] == 'fail' and result['failed_tests'] > 0)
            outcome = 'killed' if killed else 'recorded_equivalent' if equivalent and result['result'] == 'pass' else 'survived'
            counts[outcome] += 1
            reviews.append({'id': identity, 'target': target, 'reference_sha256': original_hash,
                            'mutant_sha256': mutation.sha256, 'specification_sha256': specification,
                            'kind': mutation.kind, 'line': mutation.line, 'before': mutation.before,
                            'after': mutation.after, 'source': mutation.source, 'outcome': outcome})
    (records / (task_id + '.review.json')).write_text(json.dumps(reviews, indent=2) + '\n')
    return counts


def validation_digest(private_by_task: dict[str, PrivateGraders], config: dict[str, Any]) -> str:
    """Hash unfrozen v2 candidates offline; execution still requires tracked inputs."""
    if config.get('task_root') != 'eval/tasks-v2':
        return core.configured_digest(private_by_task, config)
    hashes = {}
    for task, private in private_by_task.items():
        public = public_task(task)
        paths = sorted(p for p in public.rglob('*')
                       if not {'__pycache__', '.pytest_cache'} & set(p.parts) and p.is_file())
        if not paths or any(p.is_symlink() for p in public.rglob('*')):
            raise ValueError('Candidate requires regular files')
        hashes[task] = {'public': [[str(p.relative_to(public)), digest(p.read_bytes())] for p in paths],
                        'graders': sorted(digest(p.read_bytes()) for p in private.files)}
    return digest(json.dumps({'task_root': config['task_root'], 'tasks': hashes}, sort_keys=True).encode())


def main() -> int:
    """Print task identifiers, counts and hashes only, even on setup failures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--tasks', nargs='+', required=True)
    parser.add_argument('--mutants', type=int, help='Maximum reference-overlay mutants per task; offline only')
    args = parser.parse_args()
    tasks = (sorted(p.name for p in (core.REPOSITORY / 'eval/tasks').iterdir() if p.is_dir())
             if args.tasks == ['all'] else args.tasks)
    if args.mutants is not None:
        if args.mutants < 1:
            parser.error('--mutants must be positive')
        def measure(task: str) -> dict[str, Any]:
            try:
                return mutate_task(args.private_root, task, args.mutants)
            except Exception:
                return {'task_id': safe_task_id(task),
                        'killed': 0, 'survived': 0, 'recorded_equivalent': 0, 'error_count': 1}
        accepted = True
        with ThreadPoolExecutor(max_workers=4) as pool:
            for row in pool.map(measure, tasks):
                denominator = row['killed'] + row['survived']
                accepted &= not row.get('error_count') and denominator > 0 and row['killed'] / denominator >= 0.90
                print(json.dumps(row, sort_keys=True), flush=True)
        return 0 if accepted else 1
    valid = 0
    for task in tasks:
        try:
            row = validate_task(args.private_root, task)
        except Exception:
            row = {'task_id': safe_task_id(task),
                   'valid_count': 0}
        print(json.dumps(row, sort_keys=True), flush=True)
        valid += row['valid_count']
    summary: dict[str, Any] = {'task_count': len(tasks), 'valid_count': valid,
                               'invalid_count': len(tasks) - valid}
    if valid == len(tasks):
        try:
            roots = {public_task(task).parent.relative_to(core.REPOSITORY).as_posix() for task in tasks}
            if len(roots) != 1:
                raise ValueError("Validation hash requires one task set")
            summary['task_set_sha256'] = validation_digest({
                task: PrivateGraders.load(args.private_root, task, core.REPOSITORY) for task in tasks
            }, {"task_root": roots.pop()})
        except Exception:
            summary['hash_error_count'] = 1
    print(json.dumps(summary, sort_keys=True))
    return 0 if valid == len(tasks) and 'task_set_sha256' in summary else 1


if __name__ == '__main__':
    raise SystemExit(main())
