"""Verify legacy retained sources without reconstructing historical cache bytes."""

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import stat
from typing import Any

from eval.runner import core
from eval.runner.audit import digest
from eval.runner.publication import safe_source


def workspace_artifacts(task: dict[str, Any]) -> list[tuple[str, dict[str, str]]]:
    """Read pinned TASK/workspace/relative references, including older run paths."""
    selected = []
    task_id = task.get('task_id')
    for ref in task.get('artifacts', []):
        path = Path(ref['path'])
        parts = path.parts
        boundaries = [i + 2 for i in range(len(parts) - 1)
                      if parts[i:i + 2] == (task_id, 'workspace')]
        if not boundaries:
            continue
        if '..' in parts or len(boundaries) != 1 or boundaries[0] == len(parts):
            raise ValueError('Unsafe published workspace artifact')
        relative = Path(*parts[boundaries[0]:])
        if any(core.WORKSPACE_COPY_IGNORE('', [part]) for part in relative.parts):
            continue
        selected.append((relative.as_posix(), ref))
    return selected


def exit_time_ns(recorded: dict[str, Any], task: dict[str, Any]) -> int:
    """Require checkpoint/report agreement on timezone-aware executor exits."""
    exits = [s['exited_at'] for s in recorded['segments']]
    if not exits or exits != [s['exited_at'] for s in task['executor_segments']]:
        raise ValueError('Missing or conflicting retained exit times')
    times = [datetime.fromisoformat(value) for value in exits]
    if any(value.tzinfo is None or value.utcoffset() is None for value in times):
        raise ValueError('Unbounded retained exit time')
    elapsed = max(times) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return ((elapsed.days * 86400 + elapsed.seconds) * 1_000_000 + elapsed.microseconds) * 1000


def verify(workspace: Path, recorded: dict[str, Any],
           task: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Try recorded digests first, then legacy published hashes plus exit mtimes.

    Explicit v2/unknown versions never use legacy recovery. Both v1 and v2 must
    fail before published artifacts can establish the unchanged source set.
    Return provenance only; never repin historical workspace or artifact hashes.
    """
    version = core.matching_workspace_digest_version(workspace, recorded)
    if version is not None:
        return {'workspace_verification': 'workspace_digest', 'workspace_digest_version': version}
    legacy_version = recorded.get('workspace_digest_version', 1)
    expected = recorded.get('workspace_exit_sha256')
    if (type(legacy_version) is not int or legacy_version != 1 or task is None or
            not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected) or
            any(core.workspace_digest(workspace, v) == expected for v in (1, 2))):
        return None
    try:
        refs = workspace_artifacts(task)
        pinned = {name: ref['sha256'] for name, ref in refs}
        if (not pinned or len(pinned) != len(refs) or
                any(not re.fullmatch(r'[0-9a-f]{64}', value) for value in pinned.values()) or
                not safe_source(workspace, workspace.parent)):
            return None
        cutoff = exit_time_ns(recorded, task)
        observed = {}

        def unreadable(error: OSError) -> None:
            raise error

        for directory, directories, files in os.walk(workspace, followlinks=False, onerror=unreadable):
            ignored = core.WORKSPACE_COPY_IGNORE(directory, directories + files)
            directories[:] = [name for name in directories if name not in ignored]
            for name in directories + files:
                if name in ignored:
                    continue
                path = Path(directory) / name
                info = path.lstat()
                if stat.S_ISDIR(info.st_mode):
                    continue
                if not stat.S_ISREG(info.st_mode) or info.st_mtime_ns > cutoff:
                    return None
                observed[path.relative_to(workspace).as_posix()] = digest(path.read_bytes())
        if observed != pinned:
            return None
        return {'workspace_verification': 'published_artifact_hashes',
                'published_file_count': len(pinned), 'workspace_file_count': len(observed),
                'hashes_compared': len(observed), 'mtimes_checked': len(observed),
                'last_exit_time_ns': cutoff}
    except (KeyError, TypeError, ValueError, OSError, OverflowError):
        return None
