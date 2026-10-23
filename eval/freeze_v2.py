"""Read-only host inventory and runner-compatible v2 freeze digest; no model calls."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from eval.runner import core
from eval.runner.audit import PrivateGraders


def freeze_summary(private_root: Path) -> dict[str, Any]:
    """Hash the frozen population and verify all full configurations select it."""
    configs = [core.load_config(core.REPOSITORY / f'eval/configs/full-v2-{name}.yaml')
               for name in ('a', 'b', 'harness')]
    root = core.task_directory(configs[0])
    tasks = sorted(p.parent.name for p in root.glob('*/meta.json'))
    metadata = {task: json.loads((root / task / 'meta.json').read_text()) for task in tasks}
    if len(tasks) != 100 or any(m.get('frozen') is not True or m.get('version') != 2
                                or m.get('id') != task for task, m in metadata.items()):
        raise ValueError('Requires exactly 100 frozen version 2 tasks')
    two_session = {task for task, m in metadata.items() if m['two_session']}
    if (len(two_session) != 20 or
            any((root / task / 'day2.md').is_file() != m['two_session']
                for task, m in metadata.items())):
        raise ValueError('Requires 20 two-session tasks with day2.md')
    for config in configs:
        selected = sorted(set(tasks) - two_session) if config['name'] == 'full-v2-b' else tasks
        if (config.get('task_root') != 'eval/tasks-v2' or config['tasks'] != selected or
                config.get('task_population', config['tasks']) != tasks or
                config.get('calibration') is not False or config.get('service_tier') != 'priority' or
                config['codex_version'] != 'codex-cli 0.163.0-alpha.11.1'):
            raise ValueError('Full configuration differs from the frozen population/settings')
    graders = {task: PrivateGraders.load(private_root, task, core.REPOSITORY,
                                       task_root='eval/tasks-v2') for task in tasks}
    population_hash = core.configured_digest(graders, configs[0])
    selections = {}
    for config in configs:
        selected = {task: graders[task] for task in config['tasks']}
        population = {task: graders[task] for task in config.get('task_population', config['tasks'])}
        if core.configured_digest(population, config) != population_hash:
            raise ValueError('Full configurations do not select the same population digest')
        selections[config['name']] = {'task_count': len(selected),
                                     'selected_task_set_sha256': core.configured_digest(selected, config)}
    return {'task_count': len(tasks), 'two_session_count': len(two_session),
            'counts_by_type': dict(sorted(Counter(m['type'] for m in metadata.values()).items())),
            'counts_by_family': dict(sorted(Counter(m['family'] for m in metadata.values()).items())),
            'task_set_sha256': population_hash, 'configurations': selections}


def main() -> int:
    """Print counts and hashes only; do not expose private paths on errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = freeze_summary(args.private_root)
    except Exception:
        print('Freeze digest unavailable: check frozen inputs, configs and host private graders.',
              file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
