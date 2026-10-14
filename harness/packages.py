import hashlib
import json
import os
import secrets
import shutil
from pathlib import Path

from .container import source_files
from .results import SubmissionError

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / 'experiments/pilot-v1/projects'


def inventory(source):
    return {str(relative): {'sha256': hashlib.sha256(os.readlink(path).encode() if path.is_symlink() else path.read_bytes()).hexdigest() if not path.is_dir() or path.is_symlink() else None,
                            'kind': 'symlink' if path.is_symlink() else 'directory' if path.is_dir() else 'file',
                            'mode': path.stat().st_mode & 0o777}
            for path, relative in source_files(source)}


def artifact_digest(source):
    return hashlib.sha256(json.dumps(inventory(source), sort_keys=True).encode()).hexdigest()


def private_directory(path, public):
    path, public = Path(path).resolve(), Path(public).resolve()
    if path.is_relative_to(ROOT) or path.is_relative_to(public) or public.is_relative_to(path):
        raise ValueError('Private mapping must be outside repository and public package tree')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.stat().st_mode & 0o077:
        raise ValueError('Private mapping directory must have mode 0700')
    return path


def write_private(path, value):
    # Exclusive creation prevents accidentally overwriting a first submission or mapping.
    with path.open('x', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def prepare(project_id, arm, output):
    if project_id not in ('frontend-001', 'backend-001') or arm not in 'ABCDE' or len(arm) != 1:
        raise ValueError('Unknown pilot project or arm')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    project = PILOT / project_id
    (output / 'COMMON_CONTEXT.md').write_bytes((project / 'common-context.md').read_bytes())
    (output / 'TASK.md').write_bytes((project / 'prompts' / f'{arm}.md').read_bytes())
    return {'files': sorted(inventory(output)), 'digest': artifact_digest(output)}


def blind_package(source, project_id, output_root, mapping_root, metadata):
    if project_id not in ('frontend-001', 'backend-001'):
        raise ValueError('Unknown project')
    source, output_root = Path(source).resolve(), Path(output_root).resolve()
    if source == output_root or output_root.is_relative_to(source):
        raise ValueError('Package output must be outside artifact source')
    private = private_directory(mapping_root, output_root)
    artifact_id = 'artifact-' + secrets.token_hex(12)
    destination = output_root / artifact_id
    destination.mkdir(parents=True, exist_ok=False)
    try:
        code = destination / 'artifact'
        code.mkdir()
        before = inventory(source)
        if not before:
            raise SubmissionError('Empty artifact')
        for path, relative in source_files(source):
            target = code / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.is_dir() and not path.is_symlink():
                target.mkdir(exist_ok=True)
            else:
                shutil.copy2(path, target, follow_symlinks=False)
            os.utime(target, (0, 0), follow_symlinks=False)
        for path, relative in reversed(list(source_files(source))):
            if path.is_dir() and not path.is_symlink():
                shutil.copystat(path, code / relative, follow_symlinks=False)
        after = inventory(code)
        if before != after:
            raise SubmissionError('Artifact changed during packaging')
        digest = artifact_digest(code)
        public = {'artifact_id': artifact_id, 'files': after, 'artifact_digest': digest,
                  'identity_review': 'required_before_judge_access',
                  'technology_visibility': 'source is preserved; technology can be inferred'}
        (destination / 'manifest.json').write_text(json.dumps(public, ensure_ascii=False, indent=2) + '\n')
        shutil.copyfile(PILOT / project_id / 'evaluation-checklist.md', destination / 'evaluation-checklist.md')
        for path in destination.rglob('*'):
            os.utime(path, (0, 0), follow_symlinks=False)
        os.utime(destination, (0, 0))
        write_private(private / f'{artifact_id}.json',
                      {'artifact_id': artifact_id, 'artifact_digest': digest,
                       'project_id': project_id, 'metadata': metadata})
        return {'artifact_id': artifact_id, 'artifact_digest': digest}
    except BaseException:
        shutil.rmtree(destination)
        raise


def judge_order(output_root):
    identities = []
    for path in sorted(Path(output_root).iterdir()):
        if not path.is_dir() or not (path / 'manifest.json').is_file():
            continue
        manifest = json.loads((path / 'manifest.json').read_text())
        if manifest['identity_review'] != 'verified':
            raise ValueError('Complete operator identity review before judge access')
        if manifest['artifact_digest'] != artifact_digest(path / 'artifact'):
            raise SubmissionError('Packaged artifact was modified after snapshot')
        identities.append(path.name)
    secrets.SystemRandom().shuffle(identities)
    return identities


def review_package(package, mapping_root, reviewer):
    """Explicit operator attestation, not an automatic assertion of successful blinding."""
    package = Path(package).resolve()
    private = private_directory(mapping_root, package.parent)
    manifest_path = package / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    artifact_id = manifest['artifact_id']
    if package.name != artifact_id or manifest['artifact_digest'] != artifact_digest(package / 'artifact'):
        raise SubmissionError('Package identity or content differs from its snapshot')
    if not (private / f'{artifact_id}.json').is_file() or not reviewer.strip():
        raise ValueError('Private mapping and named operator review are required')
    original = json.loads((private / f'{artifact_id}.json').read_text())
    if original['artifact_id'] != artifact_id or original['artifact_digest'] != manifest['artifact_digest']:
        raise SubmissionError('Public manifest differs from the private original snapshot')
    write_private(private / f'{artifact_id}.review.json',
                  {'artifact_id': artifact_id, 'reviewer': reviewer,
                   'identity_leaks_checked': True, 'artifact_digest': manifest['artifact_digest']})
    manifest['identity_review'] = 'verified'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    os.utime(manifest_path, (0, 0))
    os.utime(package, (0, 0))
