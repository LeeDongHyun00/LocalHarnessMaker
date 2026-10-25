"""Read-only host inventory and runner-compatible v3 digest; no model calls."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from eval.runner import core
from eval.runner.audit import PrivateGraders


SHAPES = {'bug_fix', 'feature_plus_test', 'constrained_refactoring',
          'multiple_requirements', 'two_session', 'ambiguous_requirement'}
PLACEHOLDER = 'FILL_FROM_HOST_FREEZE_V3_OUTPUT'


def freeze_summary(private_root: Path) -> dict[str, Any]:
    """Check both inventories without loading the deliberately draft H3 config."""
    configs = []
    for arm in ('a', 'h3'):
        document = json.loads((core.REPOSITORY / f'eval/configs/full-v3-{arm}.yaml').read_text())
        if arm == 'h3' and document.get('template_status') != 'draft_not_approved':
            raise ValueError('H3 must remain a draft until plugin mode exists')
        configs.append(document.get('run_config', document))
    root = core.REPOSITORY / 'eval/tasks-v3'
    tasks = sorted(path.parent.name for path in root.glob('*/meta.json'))
    metadata = {task: json.loads((root / task / 'meta.json').read_text()) for task in tasks}
    counts = Counter(meta.get('type') for meta in metadata.values())
    if (len(tasks) != 54 or counts != Counter({shape: 9 for shape in SHAPES}) or
            any(meta.get('id') != task or meta.get('version') != 3 or
                meta.get('frozen') is not True or type(meta.get('two_session')) is not bool
                for task, meta in metadata.items())):
        raise ValueError('Requires 54 frozen version 3 tasks, nine per shape')
    two_session = sum(meta['two_session'] for meta in metadata.values())
    if two_session != 9 or any(
            (root / task / 'day2.md').is_file() != meta['two_session'] or
            meta['two_session'] != (meta['type'] == 'two_session')
            for task, meta in metadata.items()):
        raise ValueError('Requires nine two-session tasks with day2.md')
    for arm, config in zip(('a', 'h3'), configs):
        if (config.get('name') != f'full-v3-{arm}' or config.get('tasks') != tasks or
                config.get('task_population', tasks) != tasks or
                config.get('task_root') != 'eval/tasks-v3' or
                config.get('calibration') is not False or
                config.get('model') != 'gpt-6.1-sol' or
                config.get('reasoning_effort') != 'medium' or
                config.get('service_tier') != 'priority' or
                (arm == 'a' and config.get('harness') is not False)):
            raise ValueError('Full configurations differ from the frozen population/settings')
    graders = {task: PrivateGraders.load(private_root, task, core.REPOSITORY,
                                       task_root='eval/tasks-v3') for task in tasks}
    population_hash = core.configured_digest(graders, configs[0])
    for config in configs:
        if config.get('task_set_sha256') not in {PLACEHOLDER, population_hash}:
            raise ValueError('Configuration digest differs from the frozen inputs')
    return {'task_count': len(tasks), 'two_session_count': two_session,
            'counts_by_type': dict(sorted(counts.items())), 'task_set_sha256': population_hash}


def main() -> int:
    """Print only counts and the digest; keep private paths out of diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = freeze_summary(args.private_root)
    except Exception:
        print('Freeze digest unavailable: check frozen inputs, configs and host private snapshot.',
              file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
