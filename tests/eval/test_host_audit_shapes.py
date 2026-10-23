"""Regressions for retained v2 multi-file patches and process-name patterns."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner.audit import PrivateGraders, command_operands, custom_commands, patch_paths
from tests.eval.test_access_audit import audit_command, audit_native, native_session, private


def test_exact_code_mode_multi_add_literal(tmp_path: Path, private: PrivateGraders,
                                          native_session: list[dict[str, Any]]) -> None:
    workspace = Path('/private/var/folders/XX/T/lhm-eval-ZZZZ/workspace')
    targets = [str(workspace / name) for name in ('project.py', 'engine.py', 'validation.py')]
    patch = '*** Begin Patch\n' + ''.join(f'*** Add File: {path}\n+...\n' for path in targets) + '*** End Patch'
    source = 'text(await tools.apply_patch(' + json.dumps(patch) + '));'
    commands, patches, unknown = custom_commands({'name': 'exec', 'input': source})
    assert not commands and not unknown
    assert [path for value in patches for path in patch_paths(value)] == targets
    native_session[22]['payload']['input'] = source
    result = audit_native(tmp_path, private, native_session)
    assert result['status'] == 'clean', result
    assert not result['errors'] and not result['matches']


@pytest.mark.parametrize('private_index', range(6))
def test_multi_file_patch_audits_every_header(tmp_path: Path, private: PrivateGraders,
                                             native_session: list[dict[str, Any]], private_index: int) -> None:
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    (workspace / 'alias').symlink_to(private.root, target_is_directory=True)
    headers = ['Add File', 'Add File', 'Add File', 'Update File', 'Delete File', 'Move to']
    targets = [str(workspace / f'file_{i}.py') for i in range(len(headers))]
    targets[private_index] = str(workspace / 'alias' / f'file_{private_index}.py')
    patch = '*** Begin Patch\n' + ''.join(
        f'*** {header}: {path}\n' for header, path in zip(headers, targets)) + '*** End Patch\n'
    native_session[22]['payload']['input'] = 'text(await tools.apply_patch(' + json.dumps(patch) + '));'
    result = audit_native(tmp_path, private, native_session)
    assert result['status'] == 'access_detected', result
    assert not result['errors']
    assert any(m['line'] == 23 and m['marker'] == 'protected_path' for m in result['matches'])


def test_multi_file_patch_built_from_variable_is_inconclusive(tmp_path: Path, private: PrivateGraders,
                                                            native_session: list[dict[str, Any]]) -> None:
    patch = '*** Begin Patch\n*** Add File: project.py\n+...\n*** Add File: engine.py\n+...\n'
    source = ('const ending = "*** End Patch";\ntext(await tools.apply_patch(' +
              json.dumps(patch) + ' + ending));')
    native_session[22]['payload']['input'] = source
    result = audit_native(tmp_path, private, native_session)
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:native.jsonl:23' in result['errors']
    assert not result['matches']


@pytest.mark.parametrize('executable', ['pkill', 'pgrep', 'killall', '/usr/bin/pkill'])
def test_process_patterns_are_not_file_operands(tmp_path: Path, private: PrivateGraders,
                                               executable: str) -> None:
    command = '/bin/zsh -lc "' + executable + ' -f \'^python (-m unittest verify|verify.py)$\'"'
    assert command_operands(command, tmp_path, workspace=tmp_path) == ([], False)
    result = audit_command(tmp_path, private, command, tmp_path)
    assert result['status'] == 'clean', result
    assert not result['errors'] and not result['matches']


@pytest.mark.parametrize('command', [
    "cat '^python (-m unittest verify|verify.py)$'",
    "pkill -f \"$(cat unknown)\"",
    'pkill -f python > "$output"',
])
def test_process_pattern_exemption_stays_narrow(tmp_path: Path, private: PrivateGraders, command: str) -> None:
    assert audit_command(tmp_path, private, command, tmp_path)['status'] == 'inconclusive'


@pytest.mark.parametrize('suffix', ['; cat ', ' > ', ' < '])
def test_process_patterns_do_not_hide_file_access(tmp_path: Path, private: PrivateGraders, suffix: str) -> None:
    command = "pkill -f '^python (-m unittest verify|verify.py)$'" + suffix + str(private.files[0])
    assert audit_command(tmp_path, private, command, tmp_path)['status'] == 'access_detected'
