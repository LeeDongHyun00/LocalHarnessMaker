#!/usr/bin/env python3
"""Publish only evaluator fixture evidence, never private experimental mappings."""
import argparse
import hashlib
import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.packages import artifact_digest

OUTPUT = ROOT / 'experiments/harness-v1/validation.json'


def source_inventory():
    files = [p for folder in ('harness', 'tests') for p in (ROOT / folder).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts]
    files += [ROOT / 'requirements-evaluation.txt', Path(__file__).resolve()]
    files += [ROOT / f'experiments/pilot-v1/projects/{name}-001/intent-card.json'
              for name in ('frontend', 'backend')]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def evidence(raw):
    records = {name: json.loads((raw / (name + '.json')).read_text()) for name in
               ('backend-reference', 'frontend-reference', 'backend-mutants', 'frontend-mutants',
                'isolation', 'browser-isolation', 'backend-cli', 'frontend-extra', 'filesystem-packaging')}
    for prefix in ('backend', 'frontend'):
        report = records[prefix + '-reference']
        assert report['complete'] and report['measurement_errors'] == 0
        assert len(report['cases']) == 15 and all(c['status'] == 'pass' for c in report['cases'])
        card = json.loads((ROOT / f'experiments/pilot-v1/projects/{prefix}-001/intent-card.json').read_text())
        expected = {f"{r['id']}.{i}" for r in card['requirements'] for i in range(1, len(r['acceptance']) + 1)}
        assert {c['case_id'] for c in report['cases']} == expected
        mutants = records[prefix + '-mutants']
        assert len(mutants) == 8 and all(m['detected'] for m in mutants)
    assert records['backend-cli']['complete']
    assert all(records['isolation']['checks'].values())
    assert all(records['browser-isolation'].values())
    assert all(records['filesystem-packaging'].values())
    assert len(records['frontend-extra']) == 2 and all(r['status']=='pass' for r in records['frontend-extra'])
    suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_harness')
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    assert result.wasSuccessful(), stream.getvalue()
    inputs = source_inventory()
    return {
        'version': 'harness-v1-validation-1',
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Hand-authored evaluator reference fixtures and deliberate faults; not teacher development outcomes',
        'teacher_development_runs': 0, 'performance_improvement_verified': False, 'training_eligible': False,
        'unit_tests_passed': result.testsRun,
        'reference_acceptance_cases_passed': 30, 'deliberate_faults_detected': 16,
        'evidence': records,
        'fixture_artifact_digests': {name: artifact_digest(ROOT / 'tests/fixtures' / name)
                                     for name in ('frontend', 'backend')},
        'source_sha256': inputs,
        'limitations': [
            'Frontend F7.2 combines browser checks with fixture review assertions; actual submissions require human accessibility review.',
            'Submitted-service isolation is verified; live teacher development filesystem and provider-network isolation remains unverified.',
            'Private mapping separation and byte preservation are unit tested; independent judge account access separation remains unverified.',
            'The preparation runtime.json is a preserved earlier draft; this evidence does not freeze the development protocol.',
            'The initial combined integration run found isolation probe errors; corrected isolation checks and strengthened frontend checks were rerun.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=ROOT / '.local/harness-validation')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        saved = json.loads(OUTPUT.read_text())
        assert source_inventory() == saved['source_sha256'], 'Evaluation source inventory differs'
        print(f"PASS: {len(saved['source_sha256'])} evaluation-source SHA-256 entries")
    else:
        record = evidence(args.raw)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        print('Recorded fixture checks: 30 acceptance cases, 16 deliberate faults; no teacher development runs')


if __name__ == '__main__':
    main()
