"""Copy future demo captures to portable evidence; never rewrite the raw capture."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

from plugin import demo
from plugin.evidence_paths import recorded_path_aliases


def export(source: Path, destination: Path) -> None:
    """Replace host paths consistently in text and embedded JSON contexts."""
    source = source.resolve()
    destination = destination.resolve()
    if destination.exists() or source == destination or source in destination.parents:
        raise ValueError('use a fresh destination outside the raw capture')
    replacements = {str(demo.ROOT): '${REPO}', str(Path.home()): '${HOME}', str(source): '${EVIDENCE}'}
    for path in source.rglob('experiment.json'):
        meta = json.loads(path.read_text())
        replacements[meta['workspace']] = '${WORKSPACE}'
        replacements[meta['codex_home']] = '${CODEX_HOME}'
        replacements[str(PurePosixPath(meta['codex_home']).parent)] = '${DEMO}'
        original = PurePosixPath(meta['out'])
        replacements[str(original.parent if path.parent.name in {'day1', 'day2'} else original)] = '${EVIDENCE}'
    # Expand recorded macOS aliases without consulting the checking filesystem.
    for prefix, replacement in list(replacements.items()):
        for alias in recorded_path_aliases(prefix):
            replacements[alias] = replacement
    files = list(source.rglob('*'))
    if any(p.is_symlink() for p in files):
        raise ValueError('evidence must not contain symlinks')
    destination.mkdir(parents=True)
    for path in files:
        target = destination / path.relative_to(source)
        if path.is_dir():
            target.mkdir(exist_ok=True)
        else:
            value = path.read_text(encoding='utf-8')
            for prefix, replacement in sorted(replacements.items(), key=lambda item: -len(item[0])):
                value = value.replace(prefix, replacement)
            target.write_text(value, encoding='utf-8')
    # This hash refers to the now-portable handoff, rather than raw host bytes.
    validation = destination / 'handoff-validation.json'
    if validation.exists():
        data = json.loads(validation.read_text())
        data['sha256'] = hashlib.sha256((destination / 'day1/approval-state/handoff.json').read_bytes()).hexdigest()
        demo.write_json(validation, data)
    demo.write_json(destination / 'portable-export.json', {
        'transformation': 'Host path prefixes replaced by placeholders; handoff validation hash recomputed for exported bytes.',
        'raw_capture': 'Retained separately on host; not modified.',
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    export(args.source, args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
