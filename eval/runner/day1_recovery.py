"""Identify the narrow post-exit day-1 verifier gap without inventing history."""

import re
from typing import Any


def pending_verification(entry: dict[str, Any], config: dict[str, Any]) -> bool:
    """Allow an audit-blocked harness attempt after its last retained verdict."""
    segments = entry.get('segments', [])
    verdicts = entry.get('verdicts_day1', [])
    result = entry.get('result', {})
    audit = result.get('grader_access_audit', {})
    return bool(config.get('harness') and entry.get('phase') == 'finished' and not entry.get('pid') and
                result.get('two_session') and result.get('outcome') == 'invalid' and
                set(result.get('invalid_reasons', [])) == {
                    'incomplete_access_audit', 'missing_two_session_handoff_observation'} and
                audit.get('status') == 'inconclusive' and not audit.get('matches') and
                not result.get('grading') and not entry.get('day2_observation') and
                not entry.get('retained_audit_context') and 1 not in entry.get('completed_days', []) and
                not entry.get('control_error') and not entry.get('control_invalid_reason') and
                segments and result.get('segments') == segments and
                len(segments) == len(verdicts) + 1 and
                len(verdicts) <= config.get('reinstruction_limit', -1) and
                all(s.get('day', 1) == 1 and s.get('attempt') == i and
                    type(s.get('exit_code')) is int and s['exit_code'] == 0 and
                    not s.get('timed_out') and s.get('exited_at') for i, s in enumerate(segments, 1)) and
                all(v.get('attempt') == i and v.get('overall') == 'fail' and v.get('reinstruct_message')
                    for i, v in enumerate(verdicts, 1)) and
                all(re.fullmatch(r'[0-9a-f]{64}', s.get('workspace_exit_sha256', ''))
                    for s in segments[:-1]) and
                'day-1/contract.json' in entry.get('control_files', {}) and
                f'day-1/verdict-{len(segments)}.json' not in entry.get('control_files', {}) and
                'handoff.json' not in entry.get('control_files', {}))
