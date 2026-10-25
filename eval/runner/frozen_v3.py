"""Version 3 frozen identity, including the complete trusted private snapshot."""

import json
from pathlib import Path

from eval.runner.audit import PrivateGraders, digest


_CACHE_NAMES = {'__pycache__', '.pytest_cache'}


def private_inventory(root: Path) -> list[list[str]]:
    """Hash relative names and bytes; never publish private names or contents.

    The whole supplied v3 root is pinned so responder notes/matchers cannot be
    omitted because of a storage convention. Keep new run/validation outputs
    outside this frozen snapshot. Only interpreter/test caches are excluded.
    """
    entries = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if _CACHE_NAMES.intersection(relative.parts):
            continue
        if path.is_symlink():
            raise ValueError('Frozen private inputs must not contain symlinks')
        if path.is_file():
            entries.append([relative.as_posix(), digest(path.read_bytes())])
        elif not path.is_dir():
            raise ValueError('Frozen private inputs must be regular files')
    if not entries:
        raise ValueError('Frozen private snapshot must not be empty')
    return entries


def taskset_digest_v3(private_by_task: dict[str, PrivateGraders]) -> str:
    """Use the same full private snapshot for freeze and runner identities."""
    from eval.runner import core

    roots = {private.root for private in private_by_task.values()}
    if len(roots) != 1:
        raise ValueError('Version 3 requires one separate trusted private snapshot')
    root = next(iter(roots))
    public = {}
    for task in sorted(private_by_task):
        private = private_by_task[task]
        if not (root / task / 'coverage.json').is_file():
            raise ValueError('Version 3 requires private coverage')
        if not (root / '.references' / task / 'application.json').is_file():
            raise ValueError('Version 3 requires private reference manifests')
        if not private.files:
            raise ValueError('Version 3 requires private graders')
        base = core.REPOSITORY / 'eval/tasks-v3' / task
        public[task] = [[path.relative_to(base).as_posix(), digest(path.read_bytes())]
                        for path in core.public_files(task, 'eval/tasks-v3')]
    payload = {'task_root': 'eval/tasks-v3', 'public': public,
               'private': private_inventory(root)}
    return digest(json.dumps(payload, sort_keys=True).encode())
