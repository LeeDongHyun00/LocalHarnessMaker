"""The sole cross-package spelling/message adapter for the v3 hook path."""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable

from plugin.artifacts import ROOT
from plugin.hooks._process import run_group


class Adapter:
    def __init__(self, runner: Callable[..., Any] = run_group, *, budget: float = 650) -> None:
        self.runner = runner
        self.deadline = time.monotonic() + budget
        self.seconds = 0.0

    def call(self, module: str, operation: str, *, session_id: str, directory: Path,
             workspace: Path | None = None, prompt: Path | None = None,
             requirements: Path | None = None, final: Path | None = None,
             round_number: int | None = None, audit: Path | None = None,
             ledger: Path | None = None) -> Any:
        args = ['--session-id', session_id, '--artifacts', str(directory)]
        for flag, value in (('--workspace', workspace), ('--prompt', prompt),
                            ('--requirements', requirements), ('--final-message', final),
                            ('--round', round_number), ('--claim-audit', audit), ('--ledger', ledger)):
            if value is not None:
                args += [flag, str(value)]
        command = [os.environ.get('HARNESS_PYTHON', sys.executable), '-m', module, operation, *args]
        timeout = min(12 if module == 'controller' else 480 if operation == 'check' else 2,
                      self.deadline - time.monotonic())
        if timeout <= 0:
            raise TimeoutError('hook cumulative deadline exhausted')
        started = time.monotonic()
        try:
            result = self.runner(command, cwd=ROOT, env={**os.environ, 'HARNESS_NESTED': '1'},
                                 shell=False, text=True, capture_output=True, check=False, timeout=timeout)
        finally:
            self.seconds += time.monotonic() - started
        if result.returncode and not (operation == 'ledger-validate' and result.returncode == 1):
            raise RuntimeError(f'{module} {operation} exited {result.returncode}: {result.stderr[-1000:]}')
        return result

    def repair_text(self, requirements: dict[str, Any], report: dict[str, Any],
                    failed_rows: list[str]) -> str:
        # Retained verifier formatter is usable without inheriting its retry policy.
        from verifier.reinstruct import reinstruct
        criteria = [{'id': r['id'], 'description': r['text'], 'check': r['check']}
                    for r in requirements['requirements'] if r['id'] in failed_rows]
        items = [{'id': r['requirement_id'], 'status': 'fail', 'reason': r['reason'],
                  'evidence': '\n'.join(e['excerpt'] for e in r['evidence'])}
                 for r in report['items'] if r['requirement_id'] in failed_rows and r['status'] == 'fail']
        message = reinstruct(criteria, items, 1, 2)
        if not message:
            raise ValueError('verifier supplied no executed-failure repair message')
        return message

    def ledger_text(self, directory: Path, session_id: str) -> str:
        """Resolve Role 4's pending in-package formatter in this one adapter seam.

        No locally authored ledger fallback: missing formatter is visible and
        fail-open. Adjust here when the concurrently implemented package lands.
        """
        module = importlib.import_module('verifier.ledger')
        message = module.ledger_request(ledger=directory / 'ledger.json',
                                        requirements=directory / 'requirements.json', session_id=session_id)
        if not isinstance(message, str) or not message.strip():
            raise ValueError('verifier ledger request is empty')
        return message
